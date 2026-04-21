from django.db import models
import uuid


class EstadoEntrada(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'estado_entrada'
        db_table_comment = 'emitida | usada | cancelada'
        verbose_name = 'Estado de Entrada'
        verbose_name_plural = 'Estados de Entrada'

    def __str__(self):
        return self.nombre


class Entrada(models.Model):
    id = models.BigAutoField(primary_key=True)

    venta = models.ForeignKey(
        'payments.venta',
        on_delete=models.CASCADE,
        related_name='entradas'
    )

    detalle_reserva = models.ForeignKey(
        'reservations.DetalleReserva',
        on_delete=models.DO_NOTHING,
        db_comment='No UNIQUE: zonas General/Fosa generan multiples entradas por detalle'
    )

    estado_entrada = models.ForeignKey(
        EstadoEntrada,
        on_delete=models.PROTECT
    )

    codigo_ticket = models.UUIDField(
        unique=True,
        default=uuid.uuid4,
        editable=False
    )

    codigo_qr = models.CharField(
        unique=True,
        max_length=255,
        db_comment='Contenido del QR escaneado en el acceso. Puede ser UUID o HMAC firmado'
    )

    descripcion_ubicacion = models.CharField(max_length=150)
    precio_pagado = models.DecimalField(max_digits=10, decimal_places=2)

    usada = models.BooleanField(default=False)

    fecha_emision = models.DateTimeField(auto_now_add=True)
    fecha_validacion = models.DateTimeField(blank=True, null=True)

    validado_por_usuario = models.ForeignKey(
        'users.Usuario',
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    class Meta:
        managed = False
        db_table = 'entrada'
        verbose_name = 'Entrada'
        verbose_name_plural = 'Entradas'

    def __str__(self):
        return f"Ticket {self.codigo_ticket} - {self.descripcion_ubicacion}"