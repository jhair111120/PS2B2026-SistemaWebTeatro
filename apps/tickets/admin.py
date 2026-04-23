from django.contrib import admin
from .models import (
    CanalVenta,
    EstadoEntrada, Entrada,
    EstadoVenta, Venta              # ← AGREGAR imports
)


@admin.register(CanalVenta)
class CanalVentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')


@admin.register(EstadoEntrada)
class EstadoEntradaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')


@admin.register(EstadoVenta)                               # ← AGREGAR
class EstadoVentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')


@admin.register(Venta)                                     # ← AGREGAR
class VentaAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'reserva', 'usuario', 'empleado',
        'canal_venta', 'estado_venta',
        'total', 'fecha_venta'
    )
    list_filter = ('estado_venta', 'canal_venta', 'fecha_venta')
    search_fields = ('id', 'reserva__codigo_reserva', 'usuario__correo')
    readonly_fields = ('fecha_venta', 'actualizado_en')
    list_select_related = (
        'reserva', 'usuario', 'empleado',
        'canal_venta', 'estado_venta'
    )
    ordering = ('-fecha_venta',)


@admin.register(Entrada)
class EntradaAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'codigo_ticket', 'venta',
        'descripcion_ubicacion', 'estado_entrada',
        'usada', 'fecha_emision'
    )
    list_filter = ('usada', 'estado_entrada', 'fecha_emision')
    search_fields = ('codigo_ticket', 'codigo_qr', 'venta__id')
    readonly_fields = (
        'codigo_ticket', 'codigo_qr',
        'fecha_emision', 'fecha_validacion'
    )
    list_select_related = ('venta', 'estado_entrada')
    ordering = ('-fecha_emision',)