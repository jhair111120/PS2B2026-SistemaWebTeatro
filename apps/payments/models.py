from django.db import models


class EstadoPago(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'estado_pago'
        db_table_comment = 'pendiente | pagado | rechazado | reembolsado'


class MetodoPago(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'metodo_pago'
        db_table_comment = 'transferencia_qr | tarjeta_visa | efectivo'


class CanalVenta(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'canal_venta'
        db_table_comment = 'web | ventanilla'


class EstadoVenta(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'estado_venta'
        db_table_comment = 'emitida | anulada | reembolsada'


class Pago(models.Model):
    id = models.BigAutoField(primary_key=True)

    reserva = models.ForeignKey(
        'reservations.Reserva',
        models.DO_NOTHING
    )

    metodo_pago = models.ForeignKey(
        'payments.MetodoPago',
        models.DO_NOTHING
    )

    estado_pago = models.ForeignKey(
        'payments.EstadoPago',
        models.DO_NOTHING
    )

    monto = models.DecimalField(max_digits=10, decimal_places=2)

    transaccion_interna = models.UUIDField(
        unique=True,
        db_comment='UUID unico del sistema. Usar como idempotency_key para webhooks'
    )

    referencia_externa = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        db_comment='Codigo de transaccion del banco boliviano (viene en el webhook)'
    )

    comprobante_url = models.CharField(max_length=255, blank=True, null=True)
    qr_dato = models.TextField(blank=True, null=True)
    qr_imagen_url = models.CharField(max_length=255, blank=True, null=True)

    confirmado_por_usuario = models.ForeignKey(
        'users.Usuario',
        models.DO_NOTHING,
        blank=True,
        null=True,
        db_comment='NULL = webhook automatico. NOT NULL = empleado confirmo manualmente'
    )

    observacion = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField()
    fecha_confirmacion = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pago'


class Venta(models.Model):
    id = models.BigAutoField(primary_key=True)

    reserva = models.OneToOneField(
        'reservations.Reserva',
        models.DO_NOTHING
    )

    usuario = models.ForeignKey(
        'users.Usuario',
        models.DO_NOTHING,
        blank=True,
        null=True
    )

    empleado = models.ForeignKey(
        'users.Usuario',
        models.DO_NOTHING,
        related_name='venta_empleado_set',
        blank=True,
        null=True
    )

    canal_venta = models.ForeignKey(
        'payments.CanalVenta',
        models.DO_NOTHING
    )

    estado_venta = models.ForeignKey(
        'payments.EstadoVenta',
        models.DO_NOTHING
    )

    total = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_venta = models.DateTimeField()
    observacion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'venta'