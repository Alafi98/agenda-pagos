from rest_framework import viewsets
from .models import Service, Booking
from .serializers import ServiceSerializer, BookingSerializer

class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer#Conecta cada vista con el traductor (serializer) que creamos para que los datos salgan formateados correctamente en JSON.

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer