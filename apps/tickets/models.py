# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models    # type: ignore


class Venta(models.Model):
    id = models.BigAutoField(primary_key=True)
    reserva = models.OneToOneField('reservations.Reserva', models.DO_NOTHING)
    usuario = models.ForeignKey('users.Usuario', models.DO_NOTHING, blank=True, null=True)
    empleado = models.ForeignKey('users.Usuario', models.DO_NOTHING, related_name='venta_empleado_set', blank=True, null=True)
    canal_venta = models.ForeignKey('CanalVenta', models.DO_NOTHING)
    estado_venta = models.ForeignKey('EstadoVenta', models.DO_NOTHING)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_venta = models.DateTimeField(auto_now_add=True)
    observacion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'venta'


class EstadoVenta(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = True
        db_table = 'estado_venta'
        db_table_comment = 'emitida | anulada | reembolsada'


class Entrada(models.Model):
    id = models.BigAutoField(primary_key=True)
    venta = models.ForeignKey(Venta, models.DO_NOTHING)
    detalle_reserva = models.ForeignKey('reservations.DetalleReserva', models.DO_NOTHING, db_comment='No UNIQUE: zonas General/Fosa generan multiples entradas por detalle')
    estado_entrada = models.ForeignKey('EstadoEntrada', models.DO_NOTHING)
    codigo_ticket = models.UUIDField(unique=True)
    codigo_qr = models.CharField(unique=True, max_length=255, db_comment='Contenido del QR escaneado en el acceso. Puede ser UUID o HMAC firmado')
    descripcion_ubicacion = models.CharField(max_length=150, db_comment='Texto en el ticket: "VIP - Fila C - Asiento 12" o "Fosa - Entrada General"')
    precio_pagado = models.DecimalField(max_digits=10, decimal_places=2)
    usada = models.BooleanField()
    fecha_emision = models.DateTimeField(auto_now_add=True)
    fecha_validacion = models.DateTimeField(blank=True, null=True)
    validado_por_usuario = models.ForeignKey('users.Usuario', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'entrada'


class EstadoEntrada(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = True
        db_table = 'estado_entrada'
        db_table_comment = 'emitida | usada | cancelada'


class CanalVenta(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = True
        db_table = 'canal_venta'
        db_table_comment = 'web | ventanilla'
