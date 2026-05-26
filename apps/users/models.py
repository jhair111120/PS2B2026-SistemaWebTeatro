from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from datetime import time

class UsuarioManager(BaseUserManager):
    def create_user(self, correo, password=None, **extra):
        if not correo:
            raise ValueError("El correo es obligatorio")

        correo = self.normalize_email(correo)

        user = self.model(correo=correo, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, correo, password=None, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        extra.setdefault('activo', True)

        if extra.get('is_staff') is not True:
            raise ValueError('Superuser debe tener is_staff=True')

        if extra.get('is_superuser') is not True:
            raise ValueError('Superuser debe tener is_superuser=True')

        if not extra.get('rol'):
            from apps.users.models import Rol
            rol_admin, _ = Rol.objects.get_or_create(
                nombre='administrador'
            )
            extra['rol'] = rol_admin

        return self.create_user(correo, password, **extra)


class Usuario(AbstractBaseUser, PermissionsMixin):
    id = models.BigAutoField(primary_key=True)

    rol = models.ForeignKey(
        'Rol',
        on_delete=models.PROTECT,
        related_name='usuarios'
    )

    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)

    correo = models.EmailField(
        unique=True,
        db_index=True
    )

    telefono = models.CharField(
        max_length=8,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^[67]\d{7}$',
                message="El celular debe tener 8 dígitos y comenzar con 6 o 7."
            )
        ]
    )

    dni = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        db_index=True,
        validators=[
            RegexValidator(
                regex=r'^\d{7,8}(-[A-Z0-9]{1,3})?$',
                message="Formato de DNI inválido. Ej: 1234567 o 12345678-1B"
            )
        ]
    )

    password = models.CharField(
        max_length=255,
        db_column='contrasena_hash'
    )

    activo = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    # Notificaciones
    notif_eventos = models.BooleanField(default=True)
    notif_promociones = models.BooleanField(default=True)
    notif_recordatorios = models.BooleanField(default=False)
    notif_push = models.BooleanField(default=True)

    # 2FA (Autenticación de 2 Factores)
    totp_secret = models.CharField(max_length=32, blank=True, null=True)
    is_2fa_enabled = models.BooleanField(default=False)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    objects = UsuarioManager()

    USERNAME_FIELD = 'correo'
    REQUIRED_FIELDS = ['nombre', 'apellido']

    class Meta:
        managed = True
        db_table = 'usuario'
        indexes = [
            models.Index(fields=['correo']),
            models.Index(fields=['dni']),
        ]

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    @property
    def is_active(self):
        return self.activo

    def clean(self):
        if self.correo:
            self.correo = self.correo.lower()

        if self.dni and len(self.dni) < 5:
            raise ValidationError("El DNI es demasiado corto.")


class Rol(models.Model):
    class Tipo(models.TextChoices):
        ADMIN = 'administrador', 'Administrador'
        CLIENTE = 'cliente', 'Cliente'
        EMPLEADO = 'empleado', 'Empleado'
        SOPORTE = 'soporte', 'Soporte'

    id = models.BigAutoField(primary_key=True)

    nombre = models.CharField(
        unique=True,
        max_length=50,
        db_index=True
    )

    class Meta:
        managed = True
        db_table = 'rol'
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
        ordering = ['id']

    def __str__(self):
        return self.nombre


class SesionDispositivo(models.Model):
    id = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='sesiones_dispositivo'
    )
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    navegador = models.CharField(max_length=255, blank=True, null=True)
    sistema_operativo = models.CharField(max_length=255, blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    ultimo_acceso = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'sesion_dispositivo'
        ordering = ['-ultimo_acceso']

    def __str__(self):
        return f"{self.sistema_operativo} • {self.navegador} ({self.usuario.correo})"


class ConfiguracionSistema(models.Model):
    id = models.BigAutoField(primary_key=True)
    soporte_humano_hora_inicio = models.TimeField(default=time(8, 0))
    soporte_humano_hora_fin = models.TimeField(default=time(14, 0))
    soporte_humano_habilitado = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = 'configuracion_sistema'
        verbose_name = 'Configuración del Sistema'
        verbose_name_plural = 'Configuraciones del Sistema'

    def __str__(self):
        return f"Configuración del Sistema"