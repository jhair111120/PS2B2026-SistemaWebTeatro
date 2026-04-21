from django.db import models
import uuid

class EstadoPago(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'estado_pago'
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
        verbose_name = 'Método de Pago'
        verbose_name_plural = 'Métodos de Pago'

    def __str__(self):
        return self.nombre

class Pago(models.Model):
    id = models.BigAutoField(primary_key=True)
    # Referencia a la app reservations
    reserva = models.ForeignKey('reservations.Reserva', on_delete=models.DO_NOTHING)
    metodo_pago = models.ForeignKey(MetodoPago, on_delete=models.PROTECT)
    estado_pago = models.ForeignKey(EstadoPago, on_delete=models.PROTECT)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Configuramos el UUID para que se genere automáticamente si es necesario
    transaccion_interna = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    referencia_externa = models.CharField(max_length=200, blank=True, null=True)
    
    # Podrías usar URLField si son links a la nube (Supabase Storage)
    comprobante_url = models.CharField(max_length=255, blank=True, null=True)
    qr_dato = models.TextField(blank=True, null=True)
    qr_imagen_url = models.CharField(max_length=255, blank=True, null=True)
    
    # Referencia a la app users
    confirmado_por_usuario = models.ForeignKey('users.Usuario', on_delete=models.SET_NULL, blank=True, null=True)
    
    observacion = models.TextField(blank=True, null=True)
    # Fecha automática de creación
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_confirmacion = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pago'
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'

    def __str__(self):
        return f"Pago {self.id} - Monto: {self.monto} ({self.estado_pago.nombre})"