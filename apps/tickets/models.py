from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
import uuid



class Venta(models.Model):
    id = models.BigAutoField(primary_key=True)

    reserva = models.OneToOneField(
        'reservations.Reserva',
        on_delete=models.PROTECT,
        related_name='venta'
    )

    usuario = models.ForeignKey(
        'users.Usuario',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='compras'
    )

    empleado = models.ForeignKey(
        'users.Usuario',
        on_delete=models.SET_NULL,
        related_name='ventas_realizadas',
        blank=True,
        null=True
    )

    canal_venta = models.ForeignKey(
        'CanalVenta',
        on_delete=models.PROTECT,
        related_name='ventas'
    )

    estado_venta = models.ForeignKey(
        'EstadoVenta',
        on_delete=models.PROTECT,
        related_name='ventas',
        db_index=True
    )

    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    fecha_venta = models.DateTimeField(auto_now_add=True)

    observacion = models.CharField(max_length=255, blank=True, null=True)

    # 🔹 NUEVO
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'venta'
        ordering = ['-fecha_venta']
        indexes = [
            models.Index(fields=['estado_venta', 'fecha_venta']),
        ]

    def __str__(self):
        return f"Venta {self.id} - {self.total}"

    def clean(self):
        if self.total is not None and self.total < 0:
            raise ValidationError("El total no puede ser negativo.")


class EstadoVenta(models.Model):
    class Tipo(models.TextChoices):
        EMITIDA = 'emitida', 'Emitida'
        ANULADA = 'anulada', 'Anulada'
        REEMBOLSADA = 'reembolsada', 'Reembolsada'

    id = models.BigAutoField(primary_key=True)

    nombre = models.CharField(
        unique=True,
        max_length=50,
        choices=Tipo.choices,
        db_index=True
    )

    class Meta:
        managed = True
        db_table = 'estado_venta'
        db_table_comment = 'emitida | anulada | reembolsada'

class Entrada(models.Model):
    id = models.BigAutoField(primary_key=True)

    venta = models.ForeignKey(
        Venta,
        on_delete=models.CASCADE,
        related_name='entradas'
    )

    detalle_reserva = models.ForeignKey(
        'reservations.DetalleReserva',
        on_delete=models.PROTECT,
        related_name='entradas'
    )

    estado_entrada = models.ForeignKey(
        'EstadoEntrada',
        on_delete=models.PROTECT,
        related_name='entradas',
        db_index=True
    )

    codigo_ticket = models.UUIDField(
        unique=True,
        default=uuid.uuid4,
        editable=False,
        db_index=True
    )

    codigo_qr = models.CharField(
        unique=True,
        max_length=255,
        db_index=True,
        db_comment='Contenido QR (ideal: HMAC firmado)'
    )

    descripcion_ubicacion = models.CharField(max_length=150)

    precio_pagado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    usada = models.BooleanField(default=False, db_index=True)

    fecha_emision = models.DateTimeField(auto_now_add=True)

    fecha_validacion = models.DateTimeField(blank=True, null=True)

    validado_por_usuario = models.ForeignKey(
        'users.Usuario',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='entradas_validadas'
    )

    class Meta:
        managed = True
        db_table = 'entrada'
        indexes = [
            models.Index(fields=['codigo_qr']),
            models.Index(fields=['usada', 'estado_entrada']),
        ]

    def __str__(self):
        return f"Entrada {self.id}"

    def clean(self):
        """Validaciones críticas antifraude"""
        if self.usada and not self.fecha_validacion:
            raise ValidationError("Una entrada usada debe tener fecha de validación.")

        if self.fecha_validacion and not self.usada:
            raise ValidationError("Si hay fecha de validación, la entrada debe marcarse como usada.")


class EstadoEntrada(models.Model):
    class Tipo(models.TextChoices):
        EMITIDA = 'emitida', 'Emitida'
        USADA = 'usada', 'Usada'
        CANCELADA = 'cancelada', 'Cancelada'

    id = models.BigAutoField(primary_key=True)

    nombre = models.CharField(
        unique=True,
        max_length=50,
        choices=Tipo.choices,
        db_index=True
    )

    class Meta:
        managed = True
        db_table = 'estado_entrada'

class CanalVenta(models.Model):
    class Tipo(models.TextChoices):
        WEB = 'web', 'Web'
        VENTANILLA = 'ventanilla', 'Ventanilla'

    id = models.BigAutoField(primary_key=True)

    nombre = models.CharField(
        unique=True,
        max_length=50,
        choices=Tipo.choices,
        db_index=True
    )

    class Meta:
        managed = True
        db_table = 'canal_venta'