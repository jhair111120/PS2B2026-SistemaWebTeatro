from django.db import models


class EstadoEvento(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'estado_evento'
        verbose_name = 'Estado de Evento'
        verbose_name_plural = 'Estados de Evento'

    def __str__(self):
        return self.nombre


class Evento(models.Model):
    id = models.BigAutoField(primary_key=True)

    estado_evento = models.ForeignKey(
        EstadoEvento,
        on_delete=models.PROTECT
    )

    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    fecha_evento = models.DateField()
    hora_evento = models.TimeField()

    lugar = models.CharField(
        max_length=200,
        default='Teatro al Aire Libre Jaime Laredo'
    )

    imagen_url = models.URLField(max_length=255, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'evento'
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'

    def __str__(self):
        return self.nombre


class Zona(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=100)
    descripcion = models.CharField(max_length=150, blank=True, null=True)
    tipo_zona = models.CharField(max_length=10)  # VIP, GENERAL, FOSA
    tipo_asignacion = models.CharField(max_length=10)  # NUMERADA, GENERAL
    codigo_color = models.CharField(max_length=20, blank=True, null=True)
    capacidad_base = models.IntegerField(blank=True, null=True)
    orden_visual = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'zona'
        verbose_name = 'Zona Física'
        verbose_name_plural = 'Zonas Físicas'

    def __str__(self):
        return self.nombre


class Asiento(models.Model):
    id = models.BigAutoField(primary_key=True)

    zona = models.ForeignKey(
        Zona,
        on_delete=models.CASCADE
    )

    fila = models.CharField(max_length=10)
    numero = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'asiento'
        unique_together = (('zona', 'fila', 'numero'),)
        verbose_name = 'Asiento Físico'
        verbose_name_plural = 'Asientos Físicos'

    def __str__(self):
        return f"{self.zona.nombre} - Fila: {self.fila}, Nº: {self.numero}"


class EventoZona(models.Model):
    id = models.BigAutoField(primary_key=True)

    evento = models.ForeignKey(
        Evento,
        on_delete=models.CASCADE
    )

    zona = models.ForeignKey(
        Zona,
        on_delete=models.PROTECT
    )

    precio_base = models.DecimalField(max_digits=10, decimal_places=2)
    capacidad_evento = models.IntegerField(blank=True, null=True)
    nombre_display = models.CharField(max_length=100, blank=True, null=True)
    limite_por_usuario = models.IntegerField(default=4)
    habilitada = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = 'evento_zona'
        unique_together = (('evento', 'zona'),)
        verbose_name = 'Configuración de Zona por Evento'
        verbose_name_plural = 'Configuraciones de Zonas por Evento'

    def __str__(self):
        return f"{self.evento.nombre} - {self.nombre_display or self.zona.nombre}"


class EventoAsiento(models.Model):
    id = models.BigAutoField(primary_key=True)

    evento_zona = models.ForeignKey(
        EventoZona,
        on_delete=models.CASCADE
    )

    asiento = models.ForeignKey(
        Asiento,
        on_delete=models.PROTECT
    )

    estado = models.CharField(
        max_length=12,
        default='DISPONIBLE'  # DISPONIBLE, RESERVADO, BLOQUEADO, VENDIDO
    )

    class Meta:
        managed = False
        db_table = 'evento_asiento'
        unique_together = (('evento_zona', 'asiento'),)
        verbose_name = 'Estado de Asiento por Evento'
        verbose_name_plural = 'Estados de Asientos por Evento'


class FasePrecio(models.Model):
    id = models.BigAutoField(primary_key=True)

    evento = models.ForeignKey(
        Evento,
        on_delete=models.CASCADE
    )

    nombre = models.CharField(max_length=50)  # Preventa, Venta Normal
    orden = models.IntegerField()
    fecha_inicio = models.DateTimeField(blank=True, null=True)
    fecha_fin = models.DateTimeField(blank=True, null=True)
    habilitada = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = 'fase_precio'
        unique_together = (('evento', 'orden'),)
        verbose_name = 'Fase de Precio'
        verbose_name_plural = 'Fases de Precios'

    def __str__(self):
        return f"{self.nombre} ({self.evento.nombre})"


class FasePrecioZona(models.Model):
    id = models.BigAutoField(primary_key=True)

    fase_precio = models.ForeignKey(
        FasePrecio,
        on_delete=models.CASCADE
    )

    evento_zona = models.ForeignKey(
        EventoZona,
        on_delete=models.CASCADE
    )

    precio = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'fase_precio_zona'
        unique_together = (('fase_precio', 'evento_zona'),)
        verbose_name = 'Precio de Fase por Zona'
        verbose_name_plural = 'Precios de Fases por Zonas'