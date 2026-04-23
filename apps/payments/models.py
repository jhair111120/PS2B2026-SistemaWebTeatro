# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models 
import uuid


class Pago(models.Model):
    id = models.BigAutoField(primary_key=True)
    reserva = models.ForeignKey('reservations.Reserva', models.DO_NOTHING)
    metodo_pago = models.ForeignKey('MetodoPago', models.DO_NOTHING)
    estado_pago = models.ForeignKey('EstadoPago', models.DO_NOTHING)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    transaccion_interna = models.UUIDField(unique=True, default=uuid.uuid4, db_comment='UUID unico del sistema. Usar como idempotency_key para webhooks')
    referencia_externa = models.CharField(max_length=200, blank=True, null=True, db_comment='Codigo de transaccion del banco boliviano (viene en el webhook)')
    comprobante_url = models.CharField(max_length=255, blank=True, null=True)
    qr_dato = models.TextField(blank=True, null=True, db_comment='String de datos del QR de pago (formato del banco: BCP, Union, etc.)')
    qr_imagen_url = models.CharField(max_length=255, blank=True, null=True)
    confirmado_por_usuario = models.ForeignKey('users.Usuario', models.DO_NOTHING, blank=True, null=True, db_comment='NULL = webhook automatico. NOT NULL = empleado confirma manualmente')
    observacion = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_confirmacion = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'pago'


class EstadoPago(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = True
        db_table = 'estado_pago'
        db_table_comment = 'pendiente | pagado | rechazado | reembolsado'


class MetodoPago(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = True
        db_table = 'metodo_pago'
        db_table_comment = 'transferencia_qr | tarjeta_visa | efectivo'
