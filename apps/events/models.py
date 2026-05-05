from django.db import models
from django.core.validators import MinLengthValidator
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator


# =============================
# ESTADO EVENTO
# =============================
class EstadoEvento(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = 'estado_evento'

    def __str__(self):
        return self.nombre


# =============================
# EVENTO
# =============================
class Evento(models.Model):
    id = models.BigAutoField(primary_key=True)

    estado_evento = models.ForeignKey(
        EstadoEvento,
        on_delete=models.PROTECT,
        related_name='eventos'
    )

    nombre = models.CharField(max_length=150, validators=[MinLengthValidator(3)])
    descripcion = models.TextField(blank=True, null=True)

    fecha_evento = models.DateField()
    hora_evento = models.TimeField()

    lugar = models.CharField(max_length=200)

    imagen_url = models.URLField(blank=True, null=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'evento'
        ordering = ['-fecha_evento']

    def __str__(self):
        return self.nombre

    def clean(self):
        if self.fecha_evento and self.fecha_creacion:
            if self.fecha_evento < self.fecha_creacion.date():
                raise ValidationError("La fecha del evento no puede ser anterior.")


# =============================
# ZONA
# =============================
class Zona(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.CharField(max_length=150, blank=True, null=True)
    tipo_zona = models.CharField(max_length=10)
    tipo_asignacion = models.CharField(max_length=10)
    codigo_color = models.CharField(max_length=20, blank=True, null=True)
    capacidad_base = models.IntegerField(blank=True, null=True)
    orden_visual = models.IntegerField(default=0)

    class Meta:
        db_table = 'zona'

    def __str__(self):
        return self.nombre


# =============================
# ASIENTO
# =============================
class Asiento(models.Model):
    zona = models.ForeignKey(Zona, on_delete=models.CASCADE)
    fila = models.CharField(max_length=10)
    numero = models.IntegerField()

    class Meta:
        db_table = 'asiento'
        unique_together = ('zona', 'fila', 'numero')

    def __str__(self):
        return f"{self.zona} {self.fila}-{self.numero}"


# =============================
# EVENTO ZONA
# =============================
class EventoZona(models.Model):
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE)
    zona = models.ForeignKey(Zona, on_delete=models.PROTECT)
    precio_base = models.DecimalField(max_digits=10, decimal_places=2)
    capacidad_evento = models.IntegerField(blank=True, null=True)
    nombre_display = models.CharField(max_length=100, blank=True, null=True)
    limite_por_usuario = models.IntegerField(default=4)
    habilitada = models.BooleanField(default=True)

    class Meta:
        db_table = 'evento_zona'
        unique_together = ('evento', 'zona')

    def __str__(self):
        return f"{self.evento} - {self.zona}"


# =============================
# EVENTO ASIENTO
# =============================
class EventoAsiento(models.Model):

    class Estado(models.TextChoices):
        DISPONIBLE = 'DISPONIBLE'
        RESERVADO = 'RESERVADO'
        BLOQUEADO  = 'BLOQUEADO'
        VENDIDO = 'VENDIDO'

    evento_zona = models.ForeignKey(EventoZona, on_delete=models.CASCADE)
    asiento = models.ForeignKey(Asiento, on_delete=models.CASCADE)

    estado = models.CharField(
        max_length=15,
        choices=Estado.choices,
        default=Estado.DISPONIBLE
    )

    class Meta:
        db_table = 'evento_asiento'
        unique_together = ('evento_zona', 'asiento')

    def __str__(self):
        return f"{self.evento_zona} - {self.asiento}"
    
class FasePrecio(models.Model):
    id = models.BigAutoField(primary_key=True)

    evento = models.ForeignKey(
        Evento,
        on_delete=models.CASCADE,
        related_name='fases_precio'
    )

    nombre = models.CharField(max_length=50)
    orden = models.IntegerField()
    fecha_inicio = models.DateTimeField(blank=True, null=True)
    fecha_fin = models.DateTimeField(blank=True, null=True)
    habilitada = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = 'fase_precio'
        unique_together = ('evento', 'orden')
        ordering = ['orden']

    def __str__(self):
        return f"{self.evento} - {self.nombre}"


class FasePrecioZona(models.Model):
    id = models.BigAutoField(primary_key=True)

    fase_precio = models.ForeignKey(
        FasePrecio,
        on_delete=models.CASCADE,
        related_name='precios_zona'
    )

    evento_zona = models.ForeignKey(
        EventoZona,
        on_delete=models.CASCADE,
        related_name='fases_precio'
    )

    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        managed = True
        db_table = 'fase_precio_zona'
        unique_together = ('fase_precio', 'evento_zona')

    def __str__(self):
        return f"{self.fase_precio} - {self.evento_zona}"