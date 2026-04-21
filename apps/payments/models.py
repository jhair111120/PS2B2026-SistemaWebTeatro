from django.db import models
import uuid


class EstadoPago(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'estado_pago'
        db_table_comment = 'pendiente | pagado | rechazado | reembolsado'
        verbose_name = 'Estado de Pago'
        verbose_name_plural = 'Estados de Pago'

    def __str__(self):
        return self.nombre


class MetodoPago(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'metodo_pago'
        db_table_comment = 'transferencia_qr | tarjeta_visa | efectivo'
        verbose_name = 'Método de Pago'
        verbose_name_plural = 'Métodos de Pago'

    def __str__(self):
        return self.nombre


class CanalVenta(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'canal_venta'
        db_table_comment = 'web | ventanilla'

    def __str__(self):
        return self.nombre


class EstadoVenta(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'estado_venta'
        db_table_comment = 'emitida | anulada | reembolsada'

    def __str__(self):
        return self.nombre


class Pago(models.Model):
    id = models.BigAutoField(primary_key=True)

    reserva = models.ForeignKey(
        'reservations.Reserva',
        on_delete=models.DO_NOTHING
    )

    metodo_pago = models.ForeignKey(
        MetodoPago,
        on_delete=models.PROTECT
    )

    estado_pago = models.ForeignKey(
        EstadoPago,
        on_delete=models.PROTECT
    )

    monto = models.DecimalField(max_digits=10, decimal_places=2)

    transaccion_interna = models.UUIDField(
        unique=True,
        default=uuid.uuid4,
        editable=False,
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
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        db_comment='NULL = webhook automatico. NOT NULL = empleado confirmo manualmente'
    )

    observacion = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_confirmacion = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pago'
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'

    def __str__(self):
        return f"Pago {self.id} - Monto: {self.monto} ({self.estado_pago.nombre})"


class Venta(models.Model):
    id = models.BigAutoField(primary_key=True)

    reserva = models.OneToOneField(
        'reservations.Reserva',
        on_delete=models.DO_NOTHING
    )

    usuario = models.ForeignKey(
        'users.Usuario',
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True
    )

    empleado = models.ForeignKey(
        'users.Usuario',
        on_delete=models.DO_NOTHING,
        related_name='venta_empleado_set',
        blank=True,
        null=True
    )

    canal_venta = models.ForeignKey(
        CanalVenta,
        on_delete=models.PROTECT
    )

    estado_venta = models.ForeignKey(
        EstadoVenta,
        on_delete=models.PROTECT
    )

    total = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_venta = models.DateTimeField(auto_now_add=True)
    observacion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'venta'

    def __str__(self):
        return f"Venta {self.id} - Total: {self.total}"