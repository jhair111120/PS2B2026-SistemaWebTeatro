from django.db import models
import uuid

class EstadoVenta(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'estado_venta'
        verbose_name = 'Estado de Venta'
        verbose_name_plural = 'Estados de Venta'

    def __str__(self):
        return self.nombre

class Venta(models.Model):
    id = models.BigAutoField(primary_key=True)
    # Relación uno a uno con Reserva (App reservations)
    reserva = models.OneToOneField('reservations.Reserva', on_delete=models.PROTECT)
    # Relaciones con App users
    usuario = models.ForeignKey('users.Usuario', on_delete=models.DO_NOTHING, blank=True, null=True)
    empleado = models.ForeignKey('users.Usuario', on_delete=models.DO_NOTHING, related_name='ventas_atendidas', blank=True, null=True)
    # Relación con App reservations
    canal_venta = models.ForeignKey('reservations.CanalVenta', on_delete=models.PROTECT)
    estado_venta = models.ForeignKey(EstadoVenta, on_delete=models.PROTECT)
    
    total = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_venta = models.DateTimeField(auto_now_add=True)
    observacion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'venta'
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'

    def __str__(self):
        return f"Venta {self.id} - Total: {self.total}"

class EstadoEntrada(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'estado_entrada'
        verbose_name = 'Estado de Entrada'
        verbose_name_plural = 'Estados de Entrada'

    def __str__(self):
        return self.nombre

class Entrada(models.Model):
    id = models.BigAutoField(primary_key=True)
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='entradas')
    # Relación con App reservations
    detalle_reserva = models.ForeignKey('reservations.DetalleReserva', on_delete=models.DO_NOTHING)
    estado_entrada = models.ForeignKey(EstadoEntrada, on_delete=models.PROTECT)
    
    codigo_ticket = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    codigo_qr = models.CharField(unique=True, max_length=255)
    descripcion_ubicacion = models.CharField(max_length=150)
    precio_pagado = models.DecimalField(max_digits=10, decimal_places=2)
    usada = models.BooleanField(default=False)
    
    fecha_emision = models.DateTimeField(auto_now_add=True)
    fecha_validacion = models.DateTimeField(blank=True, null=True)
    # Relación con App users (el portero/empleado que escanea)
    validado_por_usuario = models.ForeignKey('users.Usuario', on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'entrada'
        verbose_name = 'Entrada'
        verbose_name_plural = 'Entradas'

    def __str__(self):
        return f"Ticket {self.codigo_ticket} - {self.descripcion_ubicacion}"