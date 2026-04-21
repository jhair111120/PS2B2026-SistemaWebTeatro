from django.db import models

class CategoriaSoporte(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'categoria_soporte'
        verbose_name = 'Categoría de Soporte'
        verbose_name_plural = 'Categorías de Soporte'

    def __str__(self):
        return self.nombre

class EstadoSoporte(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'estado_soporte'
        verbose_name = 'Estado de Soporte'
        verbose_name_plural = 'Estados de Soporte'

    def __str__(self):
        return self.nombre

class Soporte(models.Model):
    id = models.BigAutoField(primary_key=True)
    numero_reclamo = models.CharField(unique=True, max_length=30)
    # Relación con la app users
    usuario = models.ForeignKey('users.Usuario', on_delete=models.CASCADE)
    categoria_soporte = models.ForeignKey(CategoriaSoporte, on_delete=models.PROTECT)
    estado_soporte = models.ForeignKey(EstadoSoporte, on_delete=models.PROTECT)
    asunto = models.CharField(max_length=150)
    descripcion = models.TextField()
    # Relación con la app payments
    pago = models.ForeignKey('payments.Pago', on_delete=models.SET_NULL, blank=True, null=True)
    # Relación con la app tickets
    entrada = models.ForeignKey('tickets.Entrada', on_delete=models.SET_NULL, blank=True, null=True)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_cierre = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'soporte'
        verbose_name = 'Ticket de Soporte'
        verbose_name_plural = 'Tickets de Soporte'

    def __str__(self):
        return f"Ticket {self.numero_reclamo} - {self.asunto}"


class SoporteMensaje(models.Model):
    id = models.BigAutoField(primary_key=True)
    soporte = models.ForeignKey(Soporte, on_delete=models.CASCADE, related_name='mensajes')
    # Relación con la app users
    remitente = models.ForeignKey('users.Usuario', on_delete=models.DO_NOTHING)
    mensaje = models.TextField()
    fecha_envio = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'soporte_mensaje'
        verbose_name = 'Mensaje de Soporte'
        verbose_name_plural = 'Mensajes de Soporte'

    def __str__(self):
        return f"Mensaje en {self.soporte.numero_reclamo}"