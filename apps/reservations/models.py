from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator


class Reserva(models.Model):
    id = models.BigAutoField(primary_key=True)

    usuario = models.ForeignKey(
        'users.Usuario',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='reservas',
        db_index=True,
        db_comment='NULL permitido para ventas en ventanilla'
    )

    evento = models.ForeignKey(
        'events.Evento',
        on_delete=models.PROTECT,
        related_name='reservas',
        db_index=True
    )

    estado_reserva = models.ForeignKey(
        'EstadoReserva',
        on_delete=models.PROTECT,
        related_name='reservas',
        db_index=True
    )

    canal_venta = models.ForeignKey(
        'tickets.CanalVenta',
        on_delete=models.PROTECT,
        related_name='reservas'
    )

    creada_por_usuario = models.ForeignKey(
        'users.Usuario',
        on_delete=models.PROTECT,
        related_name='reservas_creadas',
        db_comment='Cliente o empleado que genera la reserva'
    )

    fase_precio = models.ForeignKey(
        'events.FasePrecio',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='reservas'
    )

    codigo_reserva = models.CharField(
        unique=True,
        max_length=30,
        db_index=True
    )

    total_reserva = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    fecha_expiracion = models.DateTimeField(
        blank=True,
        null=True,
        db_index=True
    )

    observacion = models.CharField(max_length=255, blank=True, null=True)

    # 🔹 NUEVO
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'reserva'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['evento', 'estado_reserva']),
            models.Index(fields=['fecha_expiracion']),
        ]

    def __str__(self):
        return f"Reserva {self.codigo_reserva}"

    def clean(self):
        """Validaciones críticas de negocio"""
        if self.fecha_expiracion and self.fecha_expiracion < self.fecha_creacion:
            raise ValidationError("La fecha de expiración no puede ser anterior a la creación.")

        if self.total_reserva is not None and self.total_reserva < 0:
            raise ValidationError("El total de la reserva no puede ser negativo.")

class DetalleReserva(models.Model):
    id = models.BigAutoField(primary_key=True)

    reserva = models.ForeignKey(
        Reserva,
        on_delete=models.CASCADE,
        related_name='detalles'
    )

    evento_zona = models.ForeignKey(
        'events.EventoZona',
        on_delete=models.PROTECT,
        related_name='detalles_reserva'
    )

    evento_asiento = models.ForeignKey(
        'events.EventoAsiento',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='detalles_reserva',
        db_comment='NULL para General/Fosa. NOT NULL para VIP'
    )

    cantidad = models.IntegerField(
        validators=[MinValueValidator(1)]
    )

    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        managed = True
        db_table = 'detalle_reserva'
        indexes = [
            models.Index(fields=['reserva']),
        ]
        constraints = [
            models.UniqueConstraint(          # ← AGREGAR ESTO
                fields=['evento_asiento'],
                condition=models.Q(evento_asiento__isnull=False),
                name='unique_evento_asiento_reserva'
            )
        ]

    def __str__(self):
        return f"Detalle {self.id} - Reserva {self.reserva_id}"

    def clean(self):
        """Reglas IMPORTANTES de ticketing"""
        if self.evento_asiento and self.cantidad != 1:
            raise ValidationError("Si hay asiento asignado (VIP), la cantidad debe ser 1.")

        if not self.evento_asiento and self.cantidad < 1:
            raise ValidationError("La cantidad debe ser al menos 1.")

        # Validación matemática
        if self.subtotal and self.precio_unitario:
            expected = self.cantidad * self.precio_unitario
            if self.subtotal != expected:
                raise ValidationError("El subtotal no coincide con cantidad * precio_unitario.")

class EstadoReserva(models.Model):
    class Tipo(models.TextChoices):
        ACTIVA = 'activa', 'Activa'
        CONFIRMADA = 'confirmada', 'Confirmada'
        EXPIRADA = 'expirada', 'Expirada'
        CANCELADA = 'cancelada', 'Cancelada'

    id = models.BigAutoField(primary_key=True)

    nombre = models.CharField(
        unique=True,
        max_length=50,
        choices=Tipo.choices,
        db_index=True
    )

    class Meta:
        managed = True
        db_table = 'estado_reserva'
        db_table_comment = 'activa | confirmada | expirada | cancelada'
        ordering = ['id']

    def __str__(self):
        return self.nombre