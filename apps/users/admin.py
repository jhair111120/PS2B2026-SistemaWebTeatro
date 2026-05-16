from django.contrib import admin
from .models import Rol, Usuario


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)
    ordering = ('id',)


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'nombre', 'apellido', 'correo',
        'rol', 'activo', 'is_staff', 'fecha_creacion'
    )
    list_filter = ('rol', 'activo', 'is_staff')
    search_fields = ('nombre', 'apellido', 'correo', 'dni')
    ordering = ('-fecha_creacion',)
    readonly_fields = ('fecha_creacion', 'actualizado_en', 'last_login')
    list_select_related = ('rol',)