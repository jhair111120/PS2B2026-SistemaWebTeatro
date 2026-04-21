from django.contrib import admin
from .models import EstadoVenta, Venta, EstadoEntrada, Entrada

@admin.register(EstadoVenta)
class EstadoVentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'reserva', 'usuario', 'total', 'fecha_venta', 'estado_venta')
    list_filter = ('estado_venta', 'fecha_venta', 'canal_venta')
    search_fields = ('reserva__codigo_reserva', 'usuario__correo')
    # readonly_fields hace que no se pueda editar el total o la fecha por accidente
    readonly_fields = ('fecha_venta',) 

@admin.register(EstadoEntrada)
class EstadoEntradaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')

@admin.register(Entrada)
class EntradaAdmin(admin.ModelAdmin):
    list_display = ('codigo_ticket', 'venta', 'descripcion_ubicacion', 'usada', 'fecha_emision')
    list_filter = ('usada', 'estado_entrada', 'fecha_emision')
    search_fields = ('codigo_ticket', 'codigo_qr')
    # Para seguridad, el UUID y el QR suelen ser de solo lectura en el admin
    readonly_fields = ('codigo_ticket', 'fecha_emision')