from django.db import models


class EstadoReserva(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'estado_reserva'
        db_table_comment = 'activa | confirmada | expirada | cancelada'


class Reserva(models.Model):
    id = models.BigAutoField(primary_key=True)

    usuario = models.ForeignKey(
        'users.Usuario',
        models.DO_NOTHING,
        blank=True,
        null=True,
        db_comment='NULL permitido para ventas en ventanilla sin cuenta registrada'
    )

    evento = models.ForeignKey(
        'events.Evento',
        models.DO_NOTHING
    )

    estado_reserva = models.ForeignKey(
        'reservations.EstadoReserva',
        models.DO_NOTHING
    )

    canal_venta = models.ForeignKey(
        'payments.CanalVenta', 
        models.DO_NOTHING
    )

    creada_por_usuario = models.ForeignKey(
        'users.Usuario',
        models.DO_NOTHING,
        related_name='reserva_creada_por_usuario_set',
        db_comment='El cliente (web) o el empleado (ventanilla) que genero la reserva'
    )

    fase_precio = models.ForeignKey(
        'events.FasePrecio',
        models.DO_NOTHING,
        blank=True,
        null=True
    )

    codigo_reserva = models.CharField(unique=True, max_length=30)
    total_reserva = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_creacion = models.DateTimeField()

    fecha_expiracion = models.DateTimeField(
        blank=True,
        null=True,
        db_comment='NULL en ventanilla. Web: now() + intervalo configurado (ej: 15 min)'
    )

    observacion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'reserva'


class DetalleReserva(models.Model):
    id = models.BigAutoField(primary_key=True)

    reserva = models.ForeignKey(
        'reservations.Reserva',
        models.DO_NOTHING
    )

    evento_zona = models.ForeignKey(
        'events.EventoZona',
        models.DO_NOTHING
    )

    evento_asiento = models.OneToOneField(
        'events.EventoAsiento',
        models.DO_NOTHING,
        blank=True,
        null=True,
        db_comment='NULL para General/Fosa. NOT NULL para VIP (asiento especifico)'
    )

    cantidad = models.IntegerField(
        db_comment='VIP = siempre 1. General/Fosa = numero de personas'
    )

    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'detalle_reserva'