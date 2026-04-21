from django.contrib import admin
from .models import EstadoReserva, CanalVenta, Reserva, DetalleReserva

class DetalleReservaInline(admin.TabularInline): # Permite ver el detalle dentro de la misma página de la Reserva
    model = DetalleReserva
    extra = 0

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('codigo_reserva', 'evento', 'usuario', 'total_reserva', 'estado_reserva')
    list_filter = ('estado_reserva', 'canal_venta', 'fecha_creacion')
    search_fields = ('codigo_reserva', 'usuario__correo')
    inlines = [DetalleReservaInline] # Muestra qué compró justo abajo de la reserva

admin.site.register(EstadoReserva)
admin.site.register(CanalVenta)