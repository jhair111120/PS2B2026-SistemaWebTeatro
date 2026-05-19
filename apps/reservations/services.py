"""
Servicio de compra: Reserva -> DetalleReserva -> Pago -> Venta -> Entrada
Soporta asientos numerados (EventoAsiento) y zonas sin numeracion.
"""
import hashlib
import uuid
from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.events.models import EventoZona, EventoAsiento
from apps.payments.models import EstadoPago, MetodoPago, Pago
from apps.reservations.models import DetalleReserva, EstadoReserva, Reserva
from apps.tickets.models import CanalVenta, Entrada, EstadoEntrada, EstadoVenta, Venta
from apps.users.models import Usuario


def _get_or_fail(model, **kwargs):
    obj = model.objects.filter(**kwargs).first()
    if not obj:
        raise ValueError(f'Catalogo requerido no encontrado: {model.__name__} {kwargs}')
    return obj


def _codigo_reserva():
    return f"RES-{uuid.uuid4().hex[:8].upper()}"


def _codigo_qr(codigo_ticket: str) -> str:
    return hashlib.sha256(f"TEATRO-{codigo_ticket}".encode()).hexdigest()[:64]


@transaction.atomic
def procesar_compra(usuario_id: int, evento_id: int, items: list, metodo_pago_nombre: str) -> Venta:
    """
    items puede contener:
      - {'evento_zona_id': int, 'evento_asiento_ids': [int, ...]}  <- asientos numerados
      - {'evento_zona_id': int, 'cantidad': int}                   <- zona sin numeracion
    """
    if not items:
        raise ValueError('No hay items en el carrito.')

    usuario       = _get_or_fail(Usuario,       id=usuario_id)
    canal_web     = _get_or_fail(CanalVenta,     nombre__iexact='web')
    est_activa    = _get_or_fail(EstadoReserva,  nombre__iexact='activa')
    est_confirm   = _get_or_fail(EstadoReserva,  nombre__iexact='confirmada')
    est_venta     = _get_or_fail(EstadoVenta,    nombre__iexact='emitida')
    est_entrada   = _get_or_fail(EstadoEntrada,  nombre__iexact='emitida')
    est_pagado    = _get_or_fail(EstadoPago,     nombre__iexact='pagado')
    metodo_pago, _ = MetodoPago.objects.get_or_create(nombre=metodo_pago_nombre)

    from apps.events.models import Evento
    evento = _get_or_fail(Evento, id=evento_id)

    total = Decimal('0')
    detalles_prep = []

    for item in items:
        ez_id = item.get('evento_zona_id')
        asiento_ids = item.get('evento_asiento_ids', [])
        cantidad = int(item.get('cantidad', len(asiento_ids) or 1))

        ez = EventoZona.objects.select_related('zona').filter(
            id=ez_id, evento_id=evento_id, habilitada=True
        ).first()
        if not ez:
            raise ValueError(f'Zona no valida: {ez_id}')

        if asiento_ids:
            # Asientos numerados — bloquear con SELECT FOR UPDATE
            ea_qs = EventoAsiento.objects.select_for_update().filter(
                id__in=asiento_ids,
                evento_zona=ez,
                estado=EventoAsiento.Estado.DISPONIBLE,
            )
            ea_list = list(ea_qs)
            if len(ea_list) != len(asiento_ids):
                raise ValueError(
                    f'Algunos asientos de {ez.zona.nombre} ya no estan disponibles. '
                    'Por favor vuelve a seleccionar.'
                )
            if len(ea_list) > ez.limite_por_usuario:
                raise ValueError(
                    f'Limite de {ez.limite_por_usuario} asientos por usuario en {ez.zona.nombre}.'
                )
            cantidad = len(ea_list)
        else:
            ea_list = []
            if cantidad > ez.limite_por_usuario:
                raise ValueError(
                    f'Limite de {ez.limite_por_usuario} entradas en {ez.zona.nombre}.'
                )

        precio_unit = ez.precio_base
        subtotal = precio_unit * cantidad
        total += subtotal

        detalles_prep.append({
            'evento_zona': ez,
            'ea_list': ea_list,
            'cantidad': cantidad,
            'precio_unitario': precio_unit,
            'subtotal': subtotal,
        })

    if total <= 0:
        raise ValueError('El total no puede ser cero.')

    cargo_servicio = Decimal('5.00')
    total_final = total + cargo_servicio

    reserva = Reserva.objects.create(
        usuario=usuario,
        evento=evento,
        estado_reserva=est_activa,
        canal_venta=canal_web,
        creada_por_usuario=usuario,
        codigo_reserva=_codigo_reserva(),
        total_reserva=total_final,
        fecha_expiracion=timezone.now() + timedelta(minutes=15),
    )

    detalles_creados = []
    for d in detalles_prep:
        if d['ea_list']:
            # Un DetalleReserva por asiento numerado
            for ea in d['ea_list']:
                # Marcar asiento como RESERVADO
                ea.estado = EventoAsiento.Estado.RESERVADO
                ea.save(update_fields=['estado'])

                detalle = DetalleReserva.objects.create(
                    reserva=reserva,
                    evento_zona=d['evento_zona'],
                    evento_asiento=ea,
                    cantidad=1,
                    precio_unitario=d['precio_unitario'],
                    subtotal=d['precio_unitario'],
                )
                detalles_creados.append((detalle, ea))
        else:
            detalle = DetalleReserva.objects.create(
                reserva=reserva,
                evento_zona=d['evento_zona'],
                evento_asiento=None,
                cantidad=d['cantidad'],
                precio_unitario=d['precio_unitario'],
                subtotal=d['subtotal'],
            )
            detalles_creados.append((detalle, None))

    # Confirmar reserva
    reserva.estado_reserva = est_confirm
    reserva.save(update_fields=['estado_reserva', 'actualizado_en'])

    # Pago simulado
    transaccion_id = uuid.uuid4()
    qr_dato = None
    qr_imagen_url = None

    if metodo_pago_nombre == 'QR Bancario':
        qr_ref = f"PAGO-{transaccion_id.hex[:12].upper()}-MONTO-{total_final}"
        qr_dato = qr_ref
        qr_imagen_url = f"https://api.qrserver.com/v1/create-qr-code/?size=256x256&data={qr_ref}"

    Pago.objects.create(
        reserva=reserva,
        metodo_pago=metodo_pago,
        estado_pago=est_pagado,
        monto=total_final,
        transaccion_interna=transaccion_id,
        fecha_confirmacion=timezone.now(),
        observacion='Pago simulado' + (' via QR' if qr_dato else ''),
        qr_dato=qr_dato,
        qr_imagen_url=qr_imagen_url,
    )

    venta = Venta.objects.create(
        reserva=reserva,
        usuario=usuario,
        canal_venta=canal_web,
        estado_venta=est_venta,
        total=total_final,
    )

    # Crear entradas y marcar asientos como VENDIDO
    for detalle, ea in detalles_creados:
        codigo_ticket = str(uuid.uuid4())
        zona_nombre = detalle.evento_zona.zona.nombre
        if ea:
            ubicacion = f"{zona_nombre} - Fila {ea.asiento.fila}, Asiento {ea.asiento.numero}"
            ea.estado = EventoAsiento.Estado.VENDIDO
            ea.save(update_fields=['estado'])
        else:
            ubicacion = zona_nombre

        Entrada.objects.create(
            venta=venta,
            detalle_reserva=detalle,
            estado_entrada=est_entrada,
            codigo_ticket=codigo_ticket,
            codigo_qr=_codigo_qr(codigo_ticket),
            descripcion_ubicacion=ubicacion,
            precio_pagado=detalle.precio_unitario,
        )

    return venta
