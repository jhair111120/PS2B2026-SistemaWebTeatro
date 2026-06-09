from django.contrib import admin
from .models import CategoriaSoporte, EstadoSoporte, Soporte, SoporteMensaje


@admin.register(CategoriaSoporte)
class CategoriaSoporteAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    ordering = ('id',)


@admin.register(EstadoSoporte)
class EstadoSoporteAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    ordering = ('id',)


class SoporteMensajeInline(admin.TabularInline):
    model = SoporteMensaje
    extra = 0
    readonly_fields = ('fecha_envio',)
    ordering = ('fecha_envio',)


@admin.register(Soporte)
class SoporteAdmin(admin.ModelAdmin):
    list_display = (
        'numero_reclamo', 'usuario',
        'categoria_soporte', 'estado_soporte',
        'fecha_creacion', 'fecha_cierre'
    )
    list_filter = ('estado_soporte', 'categoria_soporte', 'fecha_creacion')
    search_fields = ('numero_reclamo', 'asunto', 'usuario__correo')
    readonly_fields = ('fecha_creacion', 'actualizado_en')
    list_select_related = ('usuario', 'estado_soporte', 'categoria_soporte')
    inlines = [SoporteMensajeInline]
    ordering = ('-fecha_creacion',)


@admin.register(SoporteMensaje)
class SoporteMensajeAdmin(admin.ModelAdmin):
    list_display = ('id', 'soporte', 'remitente', 'fecha_envio')
    ordering = ('fecha_envio',)
    list_select_related = ('soporte', 'remitente')