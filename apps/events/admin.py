from django.contrib import admin
from .models import EstadoEvento, Evento, Zona, Asiento, EventoZona, EventoAsiento

@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_evento', 'hora_evento', 'estado_evento')
    list_filter = ('estado_evento', 'fecha_evento')
    search_fields = ('nombre', 'lugar')

@admin.register(Zona)
class ZonaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo_zona', 'capacidad_base')

@admin.register(EventoZona)
class EventoZonaAdmin(admin.ModelAdmin):
    list_display = ('evento', 'zona', 'precio_base', 'habilitada')
    list_filter = ('evento', 'habilitada')

admin.site.register(EstadoEvento)
admin.site.register(Asiento)
admin.site.register(EventoAsiento)