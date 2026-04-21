from django.contrib import admin
from .models import Rol, Usuario

@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    # Esto te permite ver de un vistazo quién es cliente y quién es administrador
    list_display = ('nombre', 'apellido', 'correo', 'rol', 'activo', 'fecha_creacion')
    list_filter = ('rol', 'activo')
    search_fields = ('nombre', 'apellido', 'correo', 'dni')
    # Ordenar por fecha para ver los registros más recientes primero
    ordering = ('-fecha_creacion',)