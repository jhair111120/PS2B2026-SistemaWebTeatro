from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
import uuid

class EstadoPago(models.Model):
    id = models.BigAutoField(primary_key=True)

    nombre = models.CharField(
        max_length=50,
        unique=True
    )

    class Meta:
        db_table = 'estado_pago'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class MetodoPago(models.Model):
    id = models.BigAutoField(primary_key=True)

    nombre = models.CharField(
        max_length=50,
        unique=True
    )

    class Meta:
        db_table = 'metodo_pago'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Pago(models.Model):
    id = models.BigAutoField(primary_key=True)

    reserva = models.ForeignKey(
        'reservations.Reserva',
        on_delete=models.PROTECT,
        related_name='pagos',
        db_index=True
    )

    metodo_pago = models.ForeignKey(
        MetodoPago,
        on_delete=models.PROTECT,
        related_name='pagos'
    )

    estado_pago = models.ForeignKey(
        EstadoPago,
        on_delete=models.PROTECT,
        related_name='pagos',
        db_index=True
    )

    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        db_index=True
    )

    transaccion_interna = models.UUIDField(
        unique=True,
        default=uuid.uuid4,
        editable=False,
        db_index=True
    )

    referencia_externa = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        db_index=True
    )

    comprobante_url = models.URLField(
        max_length=255,
        blank=True,
        null=True
    )

    qr_dato = models.TextField(blank=True, null=True)

    qr_imagen_url = models.URLField(
        max_length=255,
        blank=True,
        null=True
    )

    confirmado_por_usuario = models.ForeignKey(
        'users.Usuario',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='pagos_confirmados'
    )

    observacion = models.TextField(blank=True, null=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_confirmacion = models.DateTimeField(blank=True, null=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pago'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['estado_pago', 'fecha_creacion']),
            models.Index(fields=['referencia_externa']),
        ]

    def __str__(self):
        return f"Pago {self.id} - {self.monto}"

    def clean(self):
        if self.monto is not None and self.monto < 0:
            raise ValidationError("El monto no puede ser negativo.")

        if self.fecha_confirmacion and self.fecha_confirmacion < self.fecha_creacion:
            raise ValidationError("La fecha de confirmación no puede ser anterior a la creación.")

        if self.estado_pago and self.estado_pago.nombre.lower() == 'pagado':
            if not self.fecha_confirmacion:
                raise ValidationError("Un pago 'pagado' debe tener fecha de confirmación.")


class PagoPayPalPendiente(models.Model):
    id = models.BigAutoField(primary_key=True)

    paypal_payment_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
    )

    usuario_id = models.IntegerField()

    evento_id = models.IntegerField()

    carrito_data = models.JSONField()

    monto_bs = models.DecimalField(max_digits=10, decimal_places=2)
    monto_usd = models.DecimalField(max_digits=10, decimal_places=2)

    referencia = models.CharField(max_length=100)

    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('cancelado', 'Cancelado'),
        ('procesado', 'Procesado'),
    ]
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField()

    class Meta:
        db_table = 'pago_paypal_pendiente'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"PayPal Pendiente {self.paypal_payment_id[:20]} - {self.estado}"


class MetodoPagoGuardado(models.Model):
    id = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey(
        'users.Usuario', 
        on_delete=models.CASCADE, 
        related_name='metodos_pago_guardados'
    )
    ultimos_cuatro = models.CharField(max_length=4)
    marca = models.CharField(max_length=50)
    fecha_expiracion = models.CharField(max_length=7)
    token_simulado = models.CharField(max_length=255, blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'metodo_pago_guardado'
        ordering = ['-creado_en']

    def __str__(self):
        return f"{self.marca} **** {self.ultimos_cuatro}"