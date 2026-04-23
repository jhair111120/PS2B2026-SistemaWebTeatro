# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models    # type: ignore


class Soporte(models.Model):
    id = models.BigAutoField(primary_key=True)
    numero_reclamo = models.CharField(unique=True, max_length=30)
    usuario = models.ForeignKey('users.Usuario', models.DO_NOTHING)
    categoria_soporte = models.ForeignKey('CategoriaSoporte', models.DO_NOTHING)
    estado_soporte = models.ForeignKey('EstadoSoporte', models.DO_NOTHING)
    asunto = models.CharField(max_length=150)
    descripcion = models.TextField()
    pago = models.ForeignKey('payments.Pago', models.DO_NOTHING, blank=True, null=True)
    entrada = models.ForeignKey('tickets.Entrada', models.DO_NOTHING, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_cierre = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'soporte'


class SoporteMensaje(models.Model):
    id = models.BigAutoField(primary_key=True)
    soporte = models.ForeignKey(Soporte, models.DO_NOTHING)
    remitente = models.ForeignKey('users.Usuario', models.DO_NOTHING)
    mensaje = models.TextField()
    fecha_envio = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'soporte_mensaje'


class EstadoSoporte(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = True
        db_table = 'estado_soporte'
        db_table_comment = 'abierto | en_proceso | cerrado'


class CategoriaSoporte(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = True
        db_table = 'categoria_soporte'
        db_table_comment = 'pago | entrada | reembolso | otro'
