from django.contrib import admin
from .models import EstadoPago, MetodoPago, Pago

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('id', 'reserva', 'monto', 'metodo_pago', 'estado_pago', 'fecha_creacion')
    list_filter = ('estado_pago', 'metodo_pago')
    readonly_fields = ('transaccion_interna',) # El UUID no se debe editar a mano

admin.site.register(EstadoPago)
admin.site.register(MetodoPago)