from django.db import models


class EstadoEntrada(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'estado_entrada'
        db_table_comment = 'emitida | usada | cancelada'


class Entrada(models.Model):
    id = models.BigAutoField(primary_key=True)

    venta = models.ForeignKey(
        'payments.Venta',
        models.DO_NOTHING
    )

    detalle_reserva = models.ForeignKey(
        'reservations.DetalleReserva',
        models.DO_NOTHING,
        db_comment='No UNIQUE: zonas General/Fosa generan multiples entradas por detalle'
    )

    estado_entrada = models.ForeignKey(
        'tickets.EstadoEntrada',
        models.DO_NOTHING
    )

    codigo_ticket = models.UUIDField(unique=True)

    codigo_qr = models.CharField(
        unique=True,
        max_length=255,
        db_comment='Contenido del QR escaneado en el acceso. Puede ser UUID o HMAC firmado'
    )

    descripcion_ubicacion = models.CharField(max_length=150)
    precio_pagado = models.DecimalField(max_digits=10, decimal_places=2)

    usada = models.BooleanField()
    fecha_emision = models.DateTimeField()
    fecha_validacion = models.DateTimeField(blank=True, null=True)

    validado_por_usuario = models.ForeignKey(
        'users.Usuario',
        models.DO_NOTHING,
        blank=True,
        null=True
    )

    class Meta:
        managed = False
        db_table = 'entrada'