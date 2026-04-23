# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models    # type: ignore


class Evento(models.Model):
    id = models.BigAutoField(primary_key=True)
    estado_evento = models.ForeignKey('EstadoEvento', models.DO_NOTHING)
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    fecha_evento = models.DateField()
    hora_evento = models.TimeField()
    lugar = models.CharField(max_length=200)
    imagen_url = models.CharField(max_length=255, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'evento'


class EstadoEvento(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = True
        db_table = 'estado_evento'
        db_table_comment = 'programado | activo | finalizado | cancelado'


class Zona(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=100, db_comment='Nombre de Zona: "VIP", "General", "Fosa", "Platea Alta", "Platea Baja"')
    descripcion = models.CharField(max_length=150, blank=True, null=True)
    tipo_zona = models.CharField(max_length=10)
    tipo_asignacion = models.CharField(max_length=10)
    codigo_color = models.CharField(max_length=20, blank=True, null=True, db_comment='Color hex para el mapa de asientos en el frontend')
    capacidad_base = models.IntegerField(blank=True, null=True, db_comment='Capacidad fisica del recinto. Puede sobreescribirse por evento en evento_zona')
    orden_visual = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'zona'
        db_table_comment = 'Zonas fisicas del teatro. El admin las vincula a eventos via evento_zona con precio y capacidad propios. Si General no se divide, usar solo Platea Alta con la capacidad total. Si se divide, habilitar Platea Alta + Platea Baja con capacidades parciales.'


class Asiento(models.Model):
    id = models.BigAutoField(primary_key=True)
    zona = models.ForeignKey(Zona, models.DO_NOTHING)
    fila = models.CharField(max_length=10)
    numero = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'asiento'
        unique_together = (('zona', 'fila', 'numero'),)


class EventoZona(models.Model):
    id = models.BigAutoField(primary_key=True)
    evento = models.ForeignKey(Evento, models.DO_NOTHING)
    zona = models.ForeignKey(Zona, models.DO_NOTHING)
    precio_base = models.DecimalField(max_digits=10, decimal_places=2)
    capacidad_evento = models.IntegerField(blank=True, null=True, db_comment='Capacidad habilitada para este evento. NULL hereda de zona.capacidad_base')
    nombre_display = models.CharField(max_length=100, blank=True, null=True, db_comment='Nombre visible al publico. NULL = usa zona.nombre')
    limite_por_usuario = models.IntegerField(db_comment='Maximo de entradas por usuario en esta zona/evento. Evita revendedores')
    habilitada = models.BooleanField()

    class Meta:
        managed = True
        db_table = 'evento_zona'
        unique_together = (('evento', 'zona'),)
    
class EventoAsiento(models.Model):
    class Estado(models.TextChoices):
        DISPONIBLE = 'DISPONIBLE'
        RESERVADO  = 'RESERVADO'
        BLOQUEADO  = 'BLOQUEADO'
        VENDIDO    = 'VENDIDO'

    id = models.BigAutoField(primary_key=True)
    evento_zona = models.ForeignKey(EventoZona, models.DO_NOTHING)
    asiento = models.ForeignKey(Asiento, models.DO_NOTHING)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.DISPONIBLE)

    class Meta:
        managed = True
        db_table = 'evento_asiento'
        unique_together = (('evento_zona', 'asiento'),)


class FasePrecio(models.Model):
    id = models.BigAutoField(primary_key=True)
    evento = models.ForeignKey(Evento, models.DO_NOTHING)
    nombre = models.CharField(max_length=50)
    orden = models.IntegerField()
    fecha_inicio = models.DateTimeField(blank=True, null=True)
    fecha_fin = models.DateTimeField(blank=True, null=True)
    habilitada = models.BooleanField()

    class Meta:
        managed = True
        db_table = 'fase_precio'
        unique_together = (('evento', 'orden'),)


class FasePrecioZona(models.Model):
    id = models.BigAutoField(primary_key=True)
    fase_precio = models.ForeignKey(FasePrecio, models.DO_NOTHING)
    evento_zona = models.ForeignKey(EventoZona, models.DO_NOTHING)
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = True
        db_table = 'fase_precio_zona'
        unique_together = (('fase_precio', 'evento_zona'),)
