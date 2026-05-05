from django.contrib import admin
from .models import EstadoPago, MetodoPago, Pago


@admin.register(EstadoPago)
class EstadoPagoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')


@admin.register(MetodoPago)
class MetodoPagoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'reserva', 'monto',
        'metodo_pago', 'estado_pago', 'fecha_creacion'
    )
    list_filter = ('estado_pago', 'metodo_pago', 'fecha_creacion')
    search_fields = ('id', 'referencia_externa', 'transaccion_interna')
    readonly_fields = (
        'transaccion_interna',
        'fecha_creacion', 'actualizado_en'
    )
    list_select_related = ('reserva', 'metodo_pago', 'estado_pago')
    ordering = ('-fecha_creacion',)