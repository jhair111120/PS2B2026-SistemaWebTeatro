from django.db import models


class Zona(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=100)
    descripcion = models.CharField(max_length=150, blank=True, null=True)
    tipo_zona = models.CharField(max_length=10)
    tipo_asignacion = models.CharField(max_length=10)
    codigo_color = models.CharField(max_length=20, blank=True, null=True)
    capacidad_base = models.IntegerField(blank=True, null=True)
    orden_visual = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'zona'


class Asiento(models.Model):
    id = models.BigAutoField(primary_key=True)

    zona = models.ForeignKey(
        'events.Zona',
        models.DO_NOTHING
    )

    fila = models.CharField(max_length=10)
    numero = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'asiento'
        unique_together = (('zona', 'fila', 'numero'),)


class EstadoEvento(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'estado_evento'


class Evento(models.Model):
    id = models.BigAutoField(primary_key=True)

    estado_evento = models.ForeignKey(
        'events.EstadoEvento',
        models.DO_NOTHING
    )

    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    fecha_evento = models.DateField()
    hora_evento = models.TimeField()
    lugar = models.CharField(max_length=200)
    imagen_url = models.CharField(max_length=255, blank=True, null=True)
    fecha_creacion = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'evento'


class EventoZona(models.Model):
    id = models.BigAutoField(primary_key=True)

    evento = models.ForeignKey(
        'events.Evento',
        models.DO_NOTHING
    )

    zona = models.ForeignKey(
        'events.Zona',
        models.DO_NOTHING
    )

    precio_base = models.DecimalField(max_digits=10, decimal_places=2)
    capacidad_evento = models.IntegerField(blank=True, null=True)
    nombre_display = models.CharField(max_length=100, blank=True, null=True)
    limite_por_usuario = models.IntegerField()
    habilitada = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'evento_zona'
        unique_together = (('evento', 'zona'),)


class EventoAsiento(models.Model):
    id = models.BigAutoField(primary_key=True)

    evento_zona = models.ForeignKey(
        'events.EventoZona',
        models.DO_NOTHING
    )

    asiento = models.ForeignKey(
        'events.Asiento',
        models.DO_NOTHING
    )

    estado = models.CharField(max_length=12)

    class Meta:
        managed = False
        db_table = 'evento_asiento'
        unique_together = (('evento_zona', 'asiento'),)


class FasePrecio(models.Model):
    id = models.BigAutoField(primary_key=True)

    evento = models.ForeignKey(
        'events.Evento',
        models.DO_NOTHING
    )

    nombre = models.CharField(max_length=50)
    orden = models.IntegerField()
    fecha_inicio = models.DateTimeField(blank=True, null=True)
    fecha_fin = models.DateTimeField(blank=True, null=True)
    habilitada = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'fase_precio'
        unique_together = (('evento', 'orden'),)


class FasePrecioZona(models.Model):
    id = models.BigAutoField(primary_key=True)

    fase_precio = models.ForeignKey(
        'events.FasePrecio',
        models.DO_NOTHING
    )

    evento_zona = models.ForeignKey(
        'events.EventoZona',
        models.DO_NOTHING
    )

    precio = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'fase_precio_zona'
        unique_together = (('fase_precio', 'evento_zona'),)