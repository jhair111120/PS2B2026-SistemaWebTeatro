"""
Servicio de compra: crea Reserva → DetalleReserva → Pago → Venta → Entrada
en una sola transacción atómica. El pago es simulado (sin pasarela real).
"""
import hashlib
import uuid
from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.events.models import EventoZona
from apps.payments.models import EstadoPago, MetodoPago, Pago
from apps.reservations.models import DetalleReserva, EstadoReserva, Reserva
from apps.tickets.models import CanalVenta, Entrada, EstadoEntrada, EstadoVenta, Venta
from apps.users.models import Usuario


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _get_or_fail(model, **kwargs):
    """Obtiene un objeto o lanza ValueError con mensaje claro."""
    obj = model.objects.filter(**kwargs).first()
    if not obj:
        raise ValueError(f'Registro requerido no encontrado: {model.__name__} {kwargs}')
    return obj


def _codigo_reserva():
    """Genera un código único de reserva tipo RES-XXXXXXXX."""
    return f"RES-{uuid.uuid4().hex[:8].upper()}"


def _codigo_qr(codigo_ticket: str) -> str:
    """Genera un hash HMAC-like para el QR de la entrada."""
    return hashlib.sha256(f"TEATRO-{codigo_ticket}".encode()).hexdigest()[:64]


# ─────────────────────────────────────────────
# SERVICIO PRINCIPAL
# ─────────────────────────────────────────────

@transaction.atomic
def procesar_compra(usuario_id: int, evento_id: int, items: list, metodo_pago_nombre: str) -> Venta:
    """
    Procesa la compra completa en una transacción atómica.

    Parámetros:
        usuario_id: ID del usuario comprador
        evento_id: ID del evento
        items: lista de dicts [{'evento_zona_id': int, 'cantidad': int}]
        metodo_pago_nombre: nombre del método de pago (ej: 'Tarjeta de Crédito')

    Retorna:
        Venta creada con todas sus relaciones
    """
    if not items:
        raise ValueError('No hay ítems en el carrito.')

    usuario = _get_or_fail(Usuario, id=usuario_id)
    canal_web = _get_or_fail(CanalVenta, nombre__iexact='web')
    estado_activa = _get_or_fail(EstadoReserva, nombre__iexact='activa')
    estado_confirmada = _get_or_fail(EstadoReserva, nombre__iexact='confirmada')
    estado_emitida_venta = _get_or_fail(EstadoVenta, nombre__iexact='emitida')
    estado_emitida_entrada = _get_or_fail(EstadoEntrada, nombre__iexact='emitida')
    estado_pago_pagado = _get_or_fail(EstadoPago, nombre__iexact='pagado')

    # Obtener o crear método de pago
    metodo_pago, _ = MetodoPago.objects.get_or_create(nombre=metodo_pago_nombre)

    # Calcular total
    total = Decimal('0')
    detalles_prep = []

    for item in items:
        ez_id = item.get('evento_zona_id')
        cantidad = int(item.get('cantidad', 1))
        if cantidad < 1:
            continue

        ez = EventoZona.objects.select_related('evento', 'zona').filter(
            id=ez_id, evento_id=evento_id, habilitada=True
        ).first()

        if not ez:
            raise ValueError(f'Zona no válida o no habilitada: {ez_id}')

        if cantidad > ez.limite_por_usuario:
            raise ValueError(
                f'Límite de {ez.limite_por_usuario} entradas por usuario para la zona {ez.zona.nombre}.'
            )

        precio_unit = ez.precio_base
        subtotal = precio_unit * cantidad
        total += subtotal

        detalles_prep.append({
            'evento_zona': ez,
            'cantidad': cantidad,
            'precio_unitario': precio_unit,
            'subtotal': subtotal,
        })

    if total <= 0:
        raise ValueError('El total de la compra no puede ser cero.')

    # Cargo por servicio (Bs. 5 fijo si hay items)
    cargo_servicio = Decimal('5.00')
    total_con_cargo = total + cargo_servicio

    # Crear Reserva
    from apps.events.models import Evento
    evento = _get_or_fail(Evento, id=evento_id)

    reserva = Reserva.objects.create(
        usuario=usuario,
        evento=evento,
        estado_reserva=estado_activa,
        canal_venta=canal_web,
        creada_por_usuario=usuario,
        codigo_reserva=_codigo_reserva(),
        total_reserva=total_con_cargo,
        fecha_expiracion=timezone.now() + timedelta(minutes=15),
    )

    # Crear DetalleReserva
    detalles_creados = []
    for d in detalles_prep:
        detalle = DetalleReserva.objects.create(
            reserva=reserva,
            evento_zona=d['evento_zona'],
            evento_asiento=None,  # Zonas sin asiento numerado
            cantidad=d['cantidad'],
            precio_unitario=d['precio_unitario'],
            subtotal=d['subtotal'],
        )
        detalles_creados.append(detalle)

    # Confirmar reserva (pago simulado = inmediato)
    reserva.estado_reserva = estado_confirmada
    reserva.save(update_fields=['estado_reserva', 'actualizado_en'])

    # Crear Pago (simulado)
    pago = Pago.objects.create(
        reserva=reserva,
        metodo_pago=metodo_pago,
        estado_pago=estado_pago_pagado,
        monto=total_con_cargo,
        fecha_confirmacion=timezone.now(),
        observacion='Pago simulado — sin pasarela real',
    )

    # Crear Venta
    venta = Venta.objects.create(
        reserva=reserva,
        usuario=usuario,
        canal_venta=canal_web,
        estado_venta=estado_emitida_venta,
        total=total_con_cargo,
    )

    # Crear Entradas (una por unidad de cada detalle)
    for detalle in detalles_creados:
        for _ in range(detalle.cantidad):
            codigo_ticket = str(uuid.uuid4())
            Entrada.objects.create(
                venta=venta,
                detalle_reserva=detalle,
                estado_entrada=estado_emitida_entrada,
                codigo_ticket=codigo_ticket,
                codigo_qr=_codigo_qr(codigo_ticket),
                descripcion_ubicacion=detalle.evento_zona.zona.nombre,
                precio_pagado=detalle.precio_unitario,
            )

    return venta
