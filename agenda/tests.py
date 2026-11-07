from django.test import TestCase

from decimal import Decimal
from datetime import time, timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Service, Booking


class AgendaAPITests(APITestCase):

    def setUp(self):
        # 1. Crear usuario de prueba para autenticación
        self.user = User.objects.create_user(
            username='admin_test',
            password='testpassword123'
        )

        # 2. Servicios de prueba base
        self.servicio_estetica = Service.objects.create(
            nombre='Maquillaje Social',
            categoria='ESTETICA',
            precio_base=Decimal('50.00')
        )
        self.servicio_enfermeria = Service.objects.create(
            nombre='Inyectología',
            categoria='ENFERMERIA',
            precio_base=Decimal('10.00')
        )

        # 3. Fechas relativas dinámicas (evita fallos por fechas fijas)
        self.hoy = timezone.now().date()
        self.manana = self.hoy + timedelta(days=1)
        self.ayer = self.hoy - timedelta(days=1)

        # URLs de los endpoints
        self.services_url = reverse('service-list')
        self.bookings_url = reverse('booking-list')
        self.reporte_url = reverse('booking-reporte-financiero')

    # =========================================================================
    # 1. PRUEBAS DE SEGURIDAD Y PERMISOS (JWT / Session)
    # =========================================================================

    def test_lectura_servicios_es_publica(self):
        """GET /api/services/ debe ser accesible sin autenticación (200 OK)."""
        response = self.client.get(self.services_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_creacion_sin_autenticacion_falla(self):
        """POST sin token o sesión debe ser rechazado con 401 Unauthorized."""
        data = {
            'nombre': 'Peinado Express',
            'categoria': 'ESTETICA',
            'precio_base': '20.00'
        }
        response = self.client.post(self.services_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_reporte_financiero_requiere_autenticacion(self):
        """GET al reporte financiero sin login debe responder 401."""
        response = self.client.get(self.reporte_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # =========================================================================
    # 2. PRUEBAS DE REGLAS DE NEGOCIO Y CÁLCULOS (ORM + Serializers)
    # =========================================================================

    def test_calculo_automatico_precio_y_saldo_estetica(self):
        """El precio_total debe heredar el precio_base y calcular el saldo correctamente."""
        self.client.force_authenticate(user=self.user)
        payload = {
            'cliente_nombre': 'Camila Perez',
            'cliente_contacto': '04141234567',
            'servicio': self.servicio_estetica.id,
            'fecha': self.manana.strftime('%Y-%m-%d'),
            'hora': '10:00:00',
            'monto_anticipo': '20.00'
        }
        response = self.client.post(self.bookings_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        booking = Booking.objects.get(id=response.data['id'])
        self.assertEqual(booking.precio_total, Decimal('50.00'))
        self.assertEqual(booking.saldo_pendiente, Decimal('30.00'))

    def test_enfermeria_fuerza_anticipo_a_cero(self):
        """Para enfermería, monto_anticipo debe resetearse a 0.00 automáticamente."""
        self.client.force_authenticate(user=self.user)
        payload = {
            'cliente_nombre': 'Pedro Morales',
            'cliente_contacto': '04129876543',
            'servicio': self.servicio_enfermeria.id,
            'fecha': self.manana.strftime('%Y-%m-%d'),
            'hora': '11:00:00',
            'monto_anticipo': '5.00'  # Intentamos enviar anticipo
        }
        response = self.client.post(self.bookings_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        booking = Booking.objects.get(id=response.data['id'])
        self.assertEqual(booking.monto_anticipo, Decimal('0.00'))
        self.assertEqual(booking.saldo_pendiente, Decimal('10.00'))

    def test_anticipo_mayor_al_precio_es_rechazado(self):
        """Si monto_anticipo > precio_total, debe retornar 400 Bad Request."""
        self.client.force_authenticate(user=self.user)
        payload = {
            'cliente_nombre': 'Andrea Sosa',
            'cliente_contacto': '04245551122',
            'servicio': self.servicio_estetica.id,  # Precio base es 50.00
            'fecha': self.manana.strftime('%Y-%m-%d'),
            'hora': '14:00:00',
            'monto_anticipo': '60.00'  # Anticipo superior al total
        }
        response = self.client.post(self.bookings_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('monto_anticipo', response.data)

    def test_bloqueo_fecha_pasada(self):
        """No se debe permitir crear una cita con fecha anterior a hoy."""
        self.client.force_authenticate(user=self.user)
        payload = {
            'cliente_nombre': 'Carlos Ruiz',
            'cliente_contacto': '04163334455',
            'servicio': self.servicio_estetica.id,
            'fecha': self.ayer.strftime('%Y-%m-%d'),
            'hora': '09:00:00',
            'monto_anticipo': '10.00'
        }
        response = self.client.post(self.bookings_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('fecha', response.data)

    def test_bloqueo_solapamiento_horario(self):
        """Dos citas activas en la misma fecha y hora no deben permitirse."""
        self.client.force_authenticate(user=self.user)

        # Cita inicial creada directamente
        Booking.objects.create(
            cliente_nombre='Cita 1 Existente',
            cliente_contacto='123',
            servicio=self.servicio_estetica,
            fecha=self.manana,
            hora=time(15, 0),
            monto_anticipo=Decimal('10.00')
        )

        # Intentamos agendar otra cita a la misma hora exacta
        payload = {
            'cliente_nombre': 'Cita 2 Conflicto',
            'cliente_contacto': '456',
            'servicio': self.servicio_enfermeria.id,
            'fecha': self.manana.strftime('%Y-%m-%d'),
            'hora': '15:00:00',
            'monto_anticipo': '0.00'
        }
        response = self.client.post(self.bookings_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('hora', response.data)

    # =========================================================================
    # 3. PRUEBA DEL REPORTE FINANCIERO MENSUAL
    # =========================================================================

    def test_reporte_financiero_totales(self):
        """El reporte financiero debe sumar correctamente los totales y ganancias mensuales."""
        self.client.force_authenticate(user=self.user)

        # Creamos dos citas de prueba
        Booking.objects.create(
            cliente_nombre='Cliente A',
            cliente_contacto='111',
            servicio=self.servicio_estetica,
            fecha=self.manana,
            hora=time(9, 0),
            monto_anticipo=Decimal('20.00')
        )
        Booking.objects.create(
            cliente_nombre='Cliente B',
            cliente_contacto='222',
            servicio=self.servicio_enfermeria,
            fecha=self.manana,
            hora=time(11, 0),
            monto_anticipo=Decimal('0.00')
        )

        response = self.client.get(self.reporte_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        resumen = response.data['resumen_general']
        self.assertEqual(resumen['total_citas'], 2)
        # 50.00 (estética) + 10.00 (enfermería) = 60.00
        self.assertEqual(Decimal(str(resumen['ingresos_esperados'])), Decimal('60.00'))
        self.assertEqual(Decimal(str(resumen['total_recaudado_anticipos'])), Decimal('20.00'))
        self.assertEqual(Decimal(str(resumen['total_por_cobrar'])), Decimal('40.00'))
        self.assertTrue(len(response.data['ganancias_por_mes']) >= 1)
