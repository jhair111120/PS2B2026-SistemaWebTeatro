from django.db import models

class Rol(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'rol'
        db_table_comment = 'Roles del sistema: administrador, cliente, empleado, soporte'

class Usuario(models.Model):
    id = models.BigAutoField(primary_key=True)
    rol = models.ForeignKey(Rol, models.DO_NOTHING)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    correo = models.TextField(unique=True, db_comment='CITEXT: busquedas case-insensitive sin lower()')  # This field type is a guess.
    telefono = models.CharField(max_length=30, blank=True, null=True)
    dni = models.CharField(max_length=20, blank=True, null=True)
    contrasena_hash = models.CharField(max_length=255, db_comment='Hash bcrypt/argon2  nunca texto plano')
    activo = models.BooleanField()
    fecha_creacion = models.DateTimeField()
    verbose_name = 'Rol'
    verbose_name_plural = 'Roles'

    def __str__(self):
        return self.nombre

class Usuario(models.Model):
    id = models.BigAutoField(primary_key=True)
    rol = models.ForeignKey(Rol, on_delete=models.PROTECT) 
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    correo = models.EmailField(unique=True) 
    telefono = models.CharField(max_length=30, blank=True, null=True)
    dni = models.CharField(max_length=20, blank=True, null=True)
    contrasena_hash = models.CharField(max_length=255)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'usuario'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f"{self.nombre} {self.apellido}"
