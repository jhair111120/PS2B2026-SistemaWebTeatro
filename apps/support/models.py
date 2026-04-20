from django.db import models


class CategoriaSoporte(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'categoria_soporte'


class EstadoSoporte(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'estado_soporte'


class Soporte(models.Model):
    id = models.BigAutoField(primary_key=True)

    numero_reclamo = models.CharField(unique=True, max_length=30)

    usuario = models.ForeignKey(
        'users.Usuario',
        models.DO_NOTHING
    )

    categoria_soporte = models.ForeignKey(
        'support.CategoriaSoporte',
        models.DO_NOTHING
    )

    estado_soporte = models.ForeignKey(
        'support.EstadoSoporte',
        models.DO_NOTHING
    )

    asunto = models.CharField(max_length=150)
    descripcion = models.TextField()

    pago = models.ForeignKey(
        'payments.Pago',
        models.DO_NOTHING,
        blank=True,
        null=True
    )

    entrada = models.ForeignKey(
        'tickets.Entrada',
        models.DO_NOTHING,
        blank=True,
        null=True
    )

    fecha_creacion = models.DateTimeField()
    fecha_cierre = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'soporte'


class SoporteMensaje(models.Model):
    id = models.BigAutoField(primary_key=True)

    soporte = models.ForeignKey(
        'support.Soporte',
        models.DO_NOTHING
    )

    remitente = models.ForeignKey(
        'users.Usuario',
        models.DO_NOTHING
    )

    mensaje = models.TextField()
    fecha_envio = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'soporte_mensaje'