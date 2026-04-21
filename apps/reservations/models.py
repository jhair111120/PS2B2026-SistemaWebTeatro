from django.db import models

class EstadoReserva(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'estado_reserva'
        verbose_name = 'Estado de Reserva'
        verbose_name_plural = 'Estados de Reserva'

    def __str__(self):
        return self.nombre

class CanalVenta(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'canal_venta'
        verbose_name = 'Canal de Venta'
        verbose_name_plural = 'Canales de Venta'

    def __str__(self):
        return self.nombre

class Reserva(models.Model):
    id = models.BigAutoField(primary_key=True)
    # Relación con la app users
    usuario = models.ForeignKey('users.Usuario', on_delete=models.DO_NOTHING, blank=True, null=True)
    # Relación con la app events
    evento = models.ForeignKey('events.Evento', on_delete=models.DO_NOTHING)
    estado_reserva = models.ForeignKey(EstadoReserva, on_delete=models.PROTECT)
    canal_venta = models.ForeignKey(CanalVenta, on_delete=models.PROTECT)
    # Relación secundaria con users (quien creó físicamente el registro)
    creada_por_usuario = models.ForeignKey('users.Usuario', on_delete=models.DO_NOTHING, related_name='reservas_creadas')
    # Relación con la app events
    fase_precio = models.ForeignKey('events.FasePrecio', on_delete=models.DO_NOTHING, blank=True, null=True)
    
    codigo_reserva = models.CharField(unique=True, max_length=30)
    total_reserva = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    # Fecha automática
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField(blank=True, null=True)
    observacion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'reserva'
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'

    def __str__(self):
        return f"Reserva: {self.codigo_reserva} - {self.evento.nombre if self.evento else 'Sin Evento'}"

class DetalleReserva(models.Model):
    id = models.BigAutoField(primary_key=True)
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='detalles')
    # Relaciones con la app events
    evento_zona = models.ForeignKey('events.EventoZona', on_delete=models.DO_NOTHING)
    evento_asiento = models.OneToOneField('events.EventoAsiento', on_delete=models.DO_NOTHING, blank=True, null=True)
    
    cantidad = models.IntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'detalle_reserva'
        verbose_name = 'Detalle de la Reserva'
        verbose_name_plural = 'Detalles de las Reservas'

    def __str__(self):
        return f"Detalle de {self.reserva.codigo_reserva}"