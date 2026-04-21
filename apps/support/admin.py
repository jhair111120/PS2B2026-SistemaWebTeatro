from django.contrib import admin
from .models import CategoriaSoporte, EstadoSoporte, Soporte, SoporteMensaje

class SoporteMensajeInline(admin.StackedInline): # Permite leer el chat dentro del ticket
    model = SoporteMensaje
    extra = 1 # Deja un espacio vacío para escribir un mensaje nuevo rápidamente

@admin.register(Soporte)
class SoporteAdmin(admin.ModelAdmin):
    list_display = ('numero_reclamo', 'usuario', 'categoria_soporte', 'estado_soporte', 'fecha_creacion')
    list_filter = ('estado_soporte', 'categoria_soporte', 'fecha_creacion')
    search_fields = ('numero_reclamo', 'asunto', 'usuario__correo')
    inlines = [SoporteMensajeInline] # Aquí verás toda la conversación del ticket

admin.site.register(CategoriaSoporte)
admin.site.register(EstadoSoporte)