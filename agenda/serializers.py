from rest_framework import serializers
from django.core.exceptions import ValidationError
from .models import Service, Booking

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'  # Le dice a DRF que incluya todos los campos del modelo Service

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'  # Incluye todos los campos del modelo Booking
        read_only_fields = ['saldo_pendiente', 'precio_total']  # saldo_pendiente y precio_total son calculados, no se pueden modificar directamente
    def validate(self, data):
        instancia = Booking(**data)
        try:
            instancia.clean()  # Llama al método clean del modelo para validar las reglas de negocio
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict if hasattr(e, 'message_dict') else list(e))
        return data
    def to_representation(self, instance):
        # 1. Ejecutamos la traducción normal a JSON y la guardamos en 'response'
        response = super().to_representation(instance)
        
        # 2. Reemplazamos el simple ID numérico por el JSON completo del servicio
        # (Si tu campo en models.py se llama en español, cambia 'service' por 'servicio')
        response['servicio'] = ServiceSerializer(instance.servicio).data
        
        return response  