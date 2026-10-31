from rest_framework import viewsets, filters
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
    ordering_fields = ['fecha', 'hora', 'precio_total']  # Permite ordenar por fecha, hora y precio total
    ordering = ['-fecha', '-hora']  # Orden predeterminado por fecha y hora