from django.contrib import admin
from .models import (
    EstadoEvento, Evento,
    Zona, Asiento,
    EventoZona, EventoAsiento,
    FasePrecio, FasePrecioZona       # ← AGREGAR imports
)


@admin.register(EstadoEvento)
class EstadoEventoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')


class EventoZonaInline(admin.TabularInline):
    model = EventoZona
    extra = 0
    fields = ('zona', 'precio_base', 'capacidad_evento', 'nombre_display', 'limite_por_usuario', 'habilitada')


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = (
        'nombre', 'fecha_evento', 'hora_evento',
        'estado_evento', 'lugar'
    )
    list_filter = ('estado_evento', 'fecha_evento')
    search_fields = ('nombre', 'lugar')
    ordering = ('-fecha_evento',)
    list_select_related = ('estado_evento',)
    inlines = [EventoZonaInline]


@admin.register(Zona)
class ZonaAdmin(admin.ModelAdmin):
    list_display = (
        'nombre', 'tipo_zona', 'tipo_asignacion',
        'codigo_color',                            # ← AGREGAR
        'capacidad_base', 'orden_visual'
    )
    ordering = ('orden_visual',)


@admin.register(Asiento)
class AsientoAdmin(admin.ModelAdmin):
    list_display = ('zona', 'fila', 'numero')
    search_fields = ('fila',)
    list_select_related = ('zona',)


@admin.register(EventoZona)
class EventoZonaAdmin(admin.ModelAdmin):
    list_display = (
        'evento', 'zona',
        'nombre_display',                          # ← AGREGAR
        'precio_base', 'capacidad_evento',
        'limite_por_usuario', 'habilitada'
    )
    list_filter = ('evento', 'habilitada')
    list_select_related = ('evento', 'zona')


@admin.register(EventoAsiento)
class EventoAsientoAdmin(admin.ModelAdmin):
    list_display = ('evento_zona', 'asiento', 'estado')
    list_filter = ('estado',)
    list_select_related = ('evento_zona', 'asiento')


# ── Fases de precio ──────────────────────────────────────
class FasePrecioZonaInline(admin.TabularInline):           # ← AGREGAR todo esto
    model = FasePrecioZona
    extra = 0


@admin.register(FasePrecio)
class FasePrecioAdmin(admin.ModelAdmin):
    list_display = (
        'nombre', 'evento', 'orden',
        'fecha_inicio', 'fecha_fin', 'habilitada'
    )
    list_filter = ('habilitada', 'evento')
    ordering = ('evento', 'orden')
    list_select_related = ('evento',)
    inlines = [FasePrecioZonaInline]


@admin.register(FasePrecioZona)
class FasePrecioZonaAdmin(admin.ModelAdmin):
    list_display = ('fase_precio', 'evento_zona', 'precio')
    list_select_related = ('fase_precio', 'evento_zona')