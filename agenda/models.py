from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

class Service(models.Model):
    CATEGORY_CHOICES = [
        ('ESTETICA', 'Estética (Maquillaje / Peinado)'),
        ('ENFERMERIA', 'Enfermería'),
    ]

    nombre = models.CharField(max_length=100)
    categoria = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    precio_base = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.nombre} ({self.get_categoria_display()})"


class Booking(models.Model):
    STATUS_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('COMPLETADA', 'Completada'),
        ('CANCELADA', 'Cancelada'),
    ]

    cliente_nombre = models.CharField(max_length=150)
    cliente_contacto = models.CharField(max_length=50)
    servicio = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='citas')
    fecha = models.DateField()
    hora = models.TimeField()
    precio_total = models.DecimalField(max_digits=10, decimal_places=2)
    monto_anticipo = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    saldo_pendiente = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    notas = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDIENTE')

    def clean(self):
        super().clean()

        # Regla 1: Enfermería no requiere anticipo (fuerza monto_anticipo = 0)
        if self.servicio and self.servicio.categoria == 'ENFERMERIA':
            self.monto_anticipo = 0.00

        # Regla 2: El anticipo no puede superar el total
        if self.monto_anticipo > self.precio_total:
            raise ValidationError({'monto_anticipo': 'El anticipo no puede ser mayor al precio total.'})

        # Regla 3: No permitir citas en fechas pasadas
        if self.fecha and self.fecha < timezone.now().date():
            raise ValidationError({'fecha': 'No puedes agendar una cita en una fecha pasada.'})

        # Regla 4: Validar no solapamiento de horario (misma fecha y hora)
        solapadas = Booking.objects.filter(
            fecha=self.fecha, 
            hora=self.hora
        ).exclude(estado='CANCELADA')

        if self.pk:
            solapadas = solapadas.exclude(pk=self.pk)

        if solapadas.exists():
            raise ValidationError({'hora': 'Ya existe una cita programada para esta misma fecha y hora.'})

    def save(self, *args, **kwargs):
        # Fuerza la ejecución de las validaciones de clean() antes de guardar
        self.full_clean()
        
        # Cálculo automatizado del saldo en el servidor
        self.saldo_pendiente = self.precio_total - self.monto_anticipo
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Cita {self.cliente_nombre} - {self.fecha} {self.hora}"
