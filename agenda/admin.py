from django.contrib import admin

# Register your models here.
from .models import Service, Booking

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio_base')
    list_filter = ('categoria',)
    search_fields = ('nombre',)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('cliente_nombre', 'servicio', 'fecha', 'hora', 'precio_total', 'saldo_pendiente', 'estado')
    list_filter = ('estado', 'fecha', 'servicio__categoria')
    search_fields = ('cliente_nombre', 'cliente_contacto')
    readonly_fields = ('saldo_pendiente',)