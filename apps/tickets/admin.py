from django.contrib import admin
from .models import EstadoEntrada, Entrada


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