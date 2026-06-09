from django.contrib import admin
from .models import EstadoReserva, Reserva, DetalleReserva


@admin.register(EstadoReserva)
class EstadoReservaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    ordering = ('id',)


class DetalleReservaInline(admin.TabularInline):
    model = DetalleReserva
    extra = 0
    readonly_fields = ('subtotal',)


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = (
        'codigo_reserva', 'evento', 'usuario',
        'total_reserva', 'estado_reserva',
        'canal_venta', 'fecha_creacion', 'fecha_expiracion'
    )
    list_filter = ('estado_reserva', 'canal_venta', 'fecha_creacion')
    search_fields = ('codigo_reserva', 'usuario__correo')
    readonly_fields = ('fecha_creacion', 'actualizado_en')
    list_select_related = ('evento', 'usuario', 'estado_reserva', 'canal_venta')
    inlines = [DetalleReservaInline]
    ordering = ('-fecha_creacion',)


@admin.register(DetalleReserva)                            # ← AGREGAR registro directo
class DetalleReservaAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'reserva', 'evento_zona',
        'evento_asiento', 'cantidad',
        'precio_unitario', 'subtotal'
    )
    list_select_related = ('reserva', 'evento_zona', 'evento_asiento')
    search_fields = ('reserva__codigo_reserva',)