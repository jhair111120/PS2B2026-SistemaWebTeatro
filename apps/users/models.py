# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models    # type: ignore


# users/models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UsuarioManager(BaseUserManager):
    def create_user(self, correo, contrasena, **extra):
        user = self.model(correo=correo.lower(), **extra)
        user.set_password(contrasena)
        user.save()
        return user

    def create_superuser(self, correo, contrasena, **extra):
        extra.setdefault('activo', True)
        return self.create_user(correo, contrasena, **extra)

class Usuario(AbstractBaseUser):
    id = models.BigAutoField(primary_key=True)
    rol = models.ForeignKey('Rol', models.DO_NOTHING)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    correo = models.TextField(unique=True)
    telefono = models.CharField(max_length=30, blank=True, null=True)
    dni = models.CharField(max_length=20, blank=True, null=True)
    password = models.CharField(max_length=255, db_column='contrasena_hash')
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    objects = UsuarioManager()
    USERNAME_FIELD = 'correo'
    REQUIRED_FIELDS = ['nombre', 'apellido']

    @property
    def is_active(self):
        return self.activo

    class Meta:
        managed = True
        db_table = 'usuario'


class Rol(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = True
        db_table = 'rol'
        db_table_comment = 'Roles del sistema: administrador, cliente, empleado, soporte'
