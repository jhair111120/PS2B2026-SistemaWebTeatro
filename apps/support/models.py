from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator

class CategoriaSoporte(models.Model):
    class Tipo(models.TextChoices):
        PAGO       = 'pago',       'Pago'
        ENTRADA    = 'entrada',    'Entrada'
        REEMBOLSO  = 'reembolso',  'Reembolso'
        OTRO       = 'otro',       'Otro'

    id = models.BigAutoField(primary_key=True)

    nombre = models.CharField(
        unique=True,
        max_length=50,
        choices=Tipo.choices
    )

    class Meta:
        managed = True
        db_table = 'categoria_soporte'
        ordering = ['id']

    def __str__(self):
        return self.nombre


class Soporte(models.Model):
    id = models.BigAutoField(primary_key=True)

    numero_reclamo = models.CharField(
        unique=True,
        max_length=30,
        db_index=True
    )

    usuario = models.ForeignKey(
        'users.Usuario',
        on_delete=models.PROTECT,
        related_name='tickets_soporte',
        db_index=True
    )

    categoria_soporte = models.ForeignKey(
        'CategoriaSoporte',
        on_delete=models.PROTECT,
        related_name='tickets'
    )

    estado_soporte = models.ForeignKey(
        'EstadoSoporte',
        on_delete=models.PROTECT,
        related_name='tickets',
        db_index=True
    )

    asunto = models.CharField(
        max_length=150,
        validators=[MinLengthValidator(5)]
    )

    descripcion = models.TextField()

    pago = models.ForeignKey(
        'payments.Pago',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='soportes'
    )

    entrada = models.ForeignKey(
        'tickets.Entrada',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='soportes'
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    fecha_cierre = models.DateTimeField(blank=True, null=True)

    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'soporte'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['estado_soporte', 'fecha_creacion']),
        ]

    def __str__(self):
        return f"{self.numero_reclamo} - {self.asunto}"

    def clean(self):
        if self.fecha_cierre and self.fecha_cierre < self.fecha_creacion:
            raise ValidationError("La fecha de cierre no puede ser anterior a la creación.")

        if self.estado_soporte and self.estado_soporte.nombre == 'cerrado':
            if not self.fecha_cierre:
                raise ValidationError("Un ticket cerrado debe tener fecha de cierre.")

class SoporteMensaje(models.Model):
    id = models.BigAutoField(primary_key=True)

    soporte = models.ForeignKey(
        Soporte,
        on_delete=models.CASCADE,
        related_name='mensajes'
    )

    remitente = models.ForeignKey(
        'users.Usuario',
        on_delete=models.PROTECT,
        related_name='mensajes_soporte'
    )

    mensaje = models.TextField(
        validators=[MinLengthValidator(1)]
    )

    fecha_envio = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        managed = True
        db_table = 'soporte_mensaje'
        ordering = ['fecha_envio']

    def __str__(self):
        return f"Mensaje {self.id} - Ticket {self.soporte_id}"
    
class EstadoSoporte(models.Model):
    class Tipo(models.TextChoices):
        ABIERTO = 'abierto', 'Abierto'
        EN_PROCESO = 'en_proceso', 'En proceso'
        CERRADO = 'cerrado', 'Cerrado'

    id = models.BigAutoField(primary_key=True)

    nombre = models.CharField(
        unique=True,
        max_length=50,
        choices=Tipo.choices,
        db_index=True
    )

    class Meta:
        managed = True
        db_table = 'estado_soporte'
        db_table_comment = 'abierto | en_proceso | cerrado'
        ordering = ['id']

    def __str__(self):
        return self.nombre