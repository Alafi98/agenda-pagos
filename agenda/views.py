from decimal import Decimal
from urllib import request
from django.db.models import Sum, Count, DecimalField
from django.db.models.functions import Coalesce, TruncMonth
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Service, Booking
from .serializers import ServiceSerializer, BookingSerializer

class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer#Conecta cada vista con el traductor (serializer) que creamos para que los datos salgan formateados correctamente en JSON.

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    filterset_fields = ['categoria']  # Permite filtrar por categoría
    search_fields = ['nombre']  # Permite buscar por nombre
    ordering_fields = ['nombre', 'precio_base']  # Permite ordenar por nombre y precio base
    ordering = ['nombre']  # Orden predeterminado por nombre

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['fecha', 'estado', 'servicio']  # Permite filtrar por fecha, estado y servicio
    search_fields = ['cliente_nombre', 'cliente_contacto', 'notas']  # Permite buscar por nombre del cliente, contacto y notas
    ordering_fields = ['fecha', 'hora', 'precio_total','saldo_pendiente']  # Permite ordenar por fecha, hora y precio total
    ordering = ['-fecha', '-hora']  # Orden predeterminado por fecha y hora

    @action(
        detail=False,
        methods=['get'],
        url_path='reporte-financiero',
        permission_classes=[IsAuthenticated]
    )
    def reporte_financiero(self, request):
        # 1. Obtenemos el queryset aplicando automáticamente cualquier filtro de la URL (?fecha=, ?estado=)
        queryset_filtrado = self.filter_queryset(self.get_queryset())

        # 2. Filtros adicionales por Año (?anio=2026) y Mes (?mes=11)
        anio = request.query_params.get('anio')
        mes = request.query_params.get('mes')
        if anio and anio.isdigit():
            queryset_filtrado = queryset_filtrado.filter(fecha__year=int(anio))
        if mes and mes.isdigit():
            queryset_filtrado = queryset_filtrado.filter(fecha__month=int(mes))
        # 3. Excluimos citas canceladas si no se pidió explícitamente filtrar por un estado en la URL
        if 'estado' not in request.query_params:
            queryset_filtrado = queryset_filtrado.exclude(estado='CANCELADA')

        # 4. Calculamos los totales generales directamente en la base de datos (SQL)
        cero = Decimal('0.00')
        resumen_general = queryset_filtrado.aggregate(
            total_citas=Count('id'),
            ingresos_esperados=Coalesce(Sum('precio_total'), cero, output_field=DecimalField()),
            total_recaudado_anticipos=Coalesce(Sum('monto_anticipo'), cero, output_field=DecimalField()),
            total_por_cobrar=Coalesce(Sum('saldo_pendiente'), cero, output_field=DecimalField()),
        )
        # 5. Agrupación mensual: cuánto se hizo en cada mes
        mensual_qs = (
            queryset_filtrado
            .annotate(mes_fecha=TruncMonth('fecha'))
            .values('mes_fecha')
            .annotate(
                cantidad_citas=Count('id'),
                ingresos_totales_mes=Coalesce(Sum('precio_total'), cero, output_field=DecimalField()),
                anticipos_recaudados=Coalesce(Sum('monto_anticipo'), cero, output_field=DecimalField()),
                saldo_pendiente_mes=Coalesce(Sum('saldo_pendiente'), cero, output_field=DecimalField()),
            )
        .order_by('-mes_fecha')
        )

        # Formateamos la fecha a "YYYY-MM" (ej. "2026-11") para que el JSON sea limpio
        ganancias_por_mes = [
            {
                'mes': item['mes_fecha'].strftime('%Y-%m') if item['mes_fecha'] else None,
                'cantidad_citas': item['cantidad_citas'],
                'ingresos_totales_mes': item['ingresos_totales_mes'],
                'anticipos_recaudados': item['anticipos_recaudados'],
                'saldo_pendiente_mes': item['saldo_pendiente_mes'],
            }
            for item in mensual_qs
        ]
        # Formateamos la fecha a "YYYY-MM" (ej. "2026-11") para que el JSON sea limpio
        ganancias_por_mes = [
            {
                'mes': item['mes_fecha'].strftime('%Y-%m') if item['mes_fecha'] else None,
                'cantidad_citas': item['cantidad_citas'],
                'ingresos_totales_mes': item['ingresos_totales_mes'],
                'anticipos_recaudados': item['anticipos_recaudados'],
                'saldo_pendiente_mes': item['saldo_pendiente_mes'],
            }
            for item in mensual_qs
        ]
        # 6. Desglose agrupado por categoría de servicio (ESTETICA vs ENFERMERIA)
        por_categoria = (queryset_filtrado.values('servicio__categoria').annotate(
            cantidad_citas=Count('id'),
            ingresos_esperados=Coalesce(Sum('precio_total'), cero, output_field=DecimalField()),
            anticipos_recaudados=Coalesce(Sum('monto_anticipo'), cero, output_field=DecimalField()),
            saldo_por_cobrar=Coalesce(Sum('saldo_pendiente'), cero, output_field=DecimalField()),
        ).order_by('servicio__categoria'))

        return Response({
            'filtros_aplicados': request.query_params,
            'resumen_general': resumen_general,
            'ganancias_por_mes': ganancias_por_mes,
            'desglose_por_categoria': list(por_categoria)
        })