"""
Vistas para el pago con PayPal.

Flujo:
1. Usuario hace clic en "Pagar con PayPal" → paypal_create_view
2. Se crea el pago en PayPal y se redirige al usuario
3. Usuario aprueba el pago en PayPal
4. PayPal redirige a paypal_execute_view
5. Se ejecuta el pago y se crea la venta

Seguridad:
- Idempotencia: evita doble clic creando registro pendiente antes del redirect
- Validación de monto: verifica que el monto aprobado coincida con el calculado
- Webhook: recibe notificaciones async de PayPal para pagos huérfanos
"""
import json
import logging
import uuid
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from apps.events.models import Evento, EventoZona
from apps.payments.models import (
    EstadoPago, MetodoPago, Pago, PagoPayPalPendiente,
)
from apps.reservations.models import Reserva, EstadoReserva
from apps.reservations.services import procesar_compra
from apps.tickets.models import CanalVenta
from apps.users.models import Usuario

from .paypal_service import crear_pago, capturar_pago, verificar_orden

logger = logging.getLogger(__name__)


def _calcular_total_carrito(carrito_raw, evento_id):
    """Calcula el total del carrito en BS."""
    subtotal = Decimal('0')
    for item in carrito_raw:
        ez = EventoZona.objects.select_related('zona').filter(
            id=item.get('zona_id'), evento_id=evento_id
        ).first()
        if ez:
            asiento_ids = item.get('asiento_ids', [])
            qty = len(asiento_ids) if asiento_ids else int(item.get('qty', 1))
            subtotal += ez.precio_base * qty
    cargo_servicio = Decimal('5.00') if carrito_raw else Decimal('0')
    return subtotal + cargo_servicio


def _obtener_o_crear_estado_pago(nombre):
    """Obtiene o crea un estado de pago por nombre."""
    estado, _ = EstadoPago.objects.get_or_create(
        nombre=nombre,
        defaults={'nombre': nombre},
    )
    return estado


def _obtener_o_crear_estado_reserva(nombre):
    """Obtiene o crea un estado de reserva por nombre."""
    estado, _ = EstadoReserva.objects.get_or_create(
        nombre=nombre,
        defaults={'nombre': nombre},
    )
    return estado


def _obtener_canal_web():
    """Obtiene o crea el canal de venta web."""
    canal, _ = CanalVenta.objects.get_or_create(
        nombre='web',
        defaults={'nombre': 'web'},
    )
    return canal


@never_cache
@require_POST
def paypal_create_view(request, evento_id):
    """
    Crea un pago en PayPal y redirige al usuario para que lo apruebe.
    Implementa idempotencia: si ya hay un pago pendiente, reutiliza.
    """
    if not request.session.get('usuario_id'):
        messages.error(request, 'Debes iniciar sesión para pagar.')
        return redirect('login')

    carrito_raw = request.session.get(f'carrito_{evento_id}', [])
    if not carrito_raw:
        messages.error(request, 'Tu carrito está vacío. Selecciona las zonas nuevamente.')
        return redirect('seleccionar_zona', evento_id=evento_id)

    total_bs = _calcular_total_carrito(carrito_raw, evento_id)

    if total_bs <= 0:
        messages.error(request, 'El total no puede ser cero.')
        return redirect('seleccionar_zona', evento_id=evento_id)

    # ── Idempotencia: si ya hay un pago pendiente en sesión, reutilizar ──
    existing_pendiente_id = request.session.get('paypal_pendiente_id')
    if existing_pendiente_id:
        try:
            pendiente = PagoPayPalPendiente.objects.get(
                id=existing_pendiente_id,
                estado='pendiente',
            )
            if pendiente.fecha_expiracion > timezone.now():
                logger.info(f'Reutilizando pago pendiente: {pendiente.paypal_payment_id}')
                request.session['paypal_payment_id'] = pendiente.paypal_payment_id
                request.session['paypal_referencia'] = pendiente.referencia
                request.session['paypal_evento_id'] = evento_id
                request.session.modified = True
                order = verificar_orden(pendiente.paypal_payment_id)
                if order and order.get('links'):
                    for link in order['links']:
                        if link.get('rel') == 'approve':
                            return redirect(link['href'])
            else:
                pendiente.estado = 'cancelado'
                pendiente.save(update_fields=['estado'])
                request.session.pop('paypal_pendiente_id', None)
        except PagoPayPalPendiente.DoesNotExist:
            request.session.pop('paypal_pendiente_id', None)

    # ── Crear registro pendiente antes del redirect ──
    rate = settings.PAYPAL_RATE_TO_USD
    total_usd = float(total_bs / Decimal(str(rate)))
    referencia = f"TEATRO-{evento_id}-{uuid.uuid4().hex[:8].upper()}"

    estado_pendiente = _obtener_o_crear_estado_pago('pendiente')
    metodo_paypal, _ = MetodoPago.objects.get_or_create(
        nombre='PayPal',
        defaults={'nombre': 'PayPal'},
    )

    est_pendiente = _obtener_o_crear_estado_reserva('pendiente')
    canal_web = _obtener_canal_web()
    usuario = Usuario.objects.filter(id=request.session['usuario_id']).first()
    evento = Evento.objects.filter(id=evento_id).first()

    reserva = Reserva.objects.create(
        usuario=usuario,
        evento=evento,
        estado_reserva=est_pendiente,
        canal_venta=canal_web,
        creada_por_usuario=usuario,
        codigo_reserva=f"RES-{uuid.uuid4().hex[:8].upper()}",
        total_reserva=total_bs,
        fecha_expiracion=timezone.now() + timedelta(minutes=15),
    )

    pago_pendiente = PagoPayPalPendiente.objects.create(
        paypal_payment_id='',
        usuario_id=request.session['usuario_id'],
        evento_id=evento_id,
        carrito_data=carrito_raw,
        monto_bs=total_bs,
        monto_usd=Decimal(str(total_usd)),
        referencia=referencia,
        estado='pendiente',
        fecha_expiracion=timezone.now() + timedelta(minutes=15),
    )

    pago = Pago.objects.create(
        reserva=reserva,
        metodo_pago=metodo_paypal,
        estado_pago=estado_pendiente,
        monto=total_bs,
        transaccion_interna=uuid.uuid4(),
        observacion=f'Pago pendiente PayPal - Ref: {referencia}',
    )

    # ── Crear pago en PayPal ──
    base_url = request.build_absolute_uri('/').rstrip('/')
    return_url = f'{base_url}/pago/paypal/execute/'
    cancel_url = f'{base_url}/pago/paypal/cancel/{evento_id}/'

    try:
        order_id, approval_url = crear_pago(
            monto_usd=total_usd,
            referencia=referencia,
            evento_id=evento_id,
            return_url=return_url,
            cancel_url=cancel_url,
        )

        pago_pendiente.paypal_payment_id = order_id
        pago_pendiente.save(update_fields=['paypal_payment_id'])

        pago.referencia_externa = order_id
        pago.save(update_fields=['referencia_externa'])

        request.session['paypal_payment_id'] = order_id
        request.session['paypal_referencia'] = referencia
        request.session['paypal_evento_id'] = evento_id
        request.session['paypal_pendiente_id'] = pago_pendiente.id
        request.session['paypal_pago_id'] = pago.id
        request.session['paypal_monto_bs'] = str(total_bs)
        request.session.modified = True

        if approval_url:
            return redirect(approval_url)

        messages.error(request, 'No se pudo obtener la URL de pago de PayPal.')
        return redirect('finalizar_compra', evento_id=evento_id)

    except ValueError as e:
        pago_pendiente.estado = 'rechazado'
        pago_pendiente.save(update_fields=['estado'])
        pago.delete()
        reserva.delete()
        messages.error(request, str(e))
        return redirect('finalizar_compra', evento_id=evento_id)
    except Exception as e:
        logger.exception('Error al crear pago PayPal')
        pago_pendiente.estado = 'rechazado'
        pago_pendiente.save(update_fields=['estado'])
        pago.delete()
        reserva.delete()
        messages.error(request, f'Error al conectar con PayPal: {str(e)}')
        return redirect('finalizar_compra', evento_id=evento_id)


@never_cache
@require_GET
def paypal_execute_view(request):
    """
    Ejecuta el pago después de que PayPal redirige de vuelta.
    PayPal envía: paymentId, PayerID, token
    """
    if not request.session.get('usuario_id'):
        messages.error(request, 'Debes iniciar sesión para completar la compra.')
        return redirect('inicio')

    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')
    evento_id = request.session.get('paypal_evento_id')

    if not payment_id or not payer_id or not evento_id:
        messages.error(request, 'Faltan datos de confirmación de PayPal.')
        if evento_id:
            return redirect('finalizar_compra', evento_id=evento_id)
        return redirect('inicio')

    session_payment_id = request.session.get('paypal_payment_id')
    if session_payment_id and session_payment_id != payment_id:
        messages.error(request, 'El ID de pago no coincide. Intenta nuevamente.')
        return redirect('finalizar_compra', evento_id=evento_id)

    try:
        result = capturar_pago(payment_id)

        if result.get('status') != 'COMPLETED':
            messages.error(request, 'El pago no fue aprobado por PayPal.')
            return redirect('finalizar_compra', evento_id=evento_id)

        # ── Validar monto ──
        try:
            paypal_amount = Decimal(
                result['purchase_units'][0]['payments']['captures'][0]['amount']['value']
            )
        except (KeyError, IndexError):
            paypal_amount = None

        if paypal_amount is not None:
            rate = settings.PAYPAL_RATE_TO_USD
            monto_bs_str = request.session.get('paypal_monto_bs')
            if monto_bs_str:
                monto_bs_esperado = Decimal(monto_bs_str)
                monto_usd_esperado = (monto_bs_esperado / Decimal(str(rate))).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                )
                if paypal_amount != monto_usd_esperado:
                    logger.warning(
                        f'PayPal monto mismatch: esperado={monto_usd_esperado}, '
                        f'recibido={paypal_amount}'
                    )
                    messages.error(request, 'El monto del pago no coincide. Contacta soporte.')
                    return redirect('finalizar_compra', evento_id=evento_id)

        # ── Actualizar registro pendiente ──
        pendiente_id = request.session.get('paypal_pendiente_id')
        if pendiente_id:
            try:
                pendiente = PagoPayPalPendiente.objects.get(id=pendiente_id)
                pendiente.estado = 'aprobado'
                pendiente.save(update_fields=['estado'])
            except PagoPayPalPendiente.DoesNotExist:
                pass

        # ── Procesar compra ──
        referencia = request.session.get('paypal_referencia', '')
        carrito_raw = request.session.get(f'carrito_{evento_id}', [])

        if not carrito_raw and pendiente_id:
            try:
                pendiente = PagoPayPalPendiente.objects.get(id=pendiente_id)
                carrito_raw = pendiente.carrito_data
            except PagoPayPalPendiente.DoesNotExist:
                pass

        if not carrito_raw:
            messages.error(request, 'Tu sesión expiró. Selecciona las zonas nuevamente.')
            return redirect('seleccionar_zona', evento_id=evento_id)

        items = [
            {
                'evento_zona_id': item.get('zona_id'),
                'evento_asiento_ids': item.get('asiento_ids', []),
                'cantidad': item.get('qty', 1),
            }
            for item in carrito_raw
        ]

        venta = procesar_compra(
            usuario_id=request.session['usuario_id'],
            evento_id=evento_id,
            items=items,
            metodo_pago_nombre='PayPal',
        )

        # ── Actualizar Pago creado por procesar_compra con referencia PayPal ──
        pago = venta.reserva.pagos.first()
        if pago:
            estado_pagado = _obtener_o_crear_estado_pago('pagado')
            pago.estado_pago = estado_pagado
            pago.referencia_externa = payment_id
            pago.fecha_confirmacion = timezone.now()
            pago.observacion = f'Pago aprobado vía PayPal - Ref: {referencia}'
            pago.save(update_fields=[
                'estado_pago', 'referencia_externa', 'fecha_confirmacion', 'observacion'
            ])

        # ── Marcar pendiente como procesado ──
        if pendiente_id:
            try:
                pendiente = PagoPayPalPendiente.objects.get(id=pendiente_id)
                pendiente.estado = 'procesado'
                pendiente.save(update_fields=['estado'])
            except PagoPayPalPendiente.DoesNotExist:
                pass

        # ── Limpiar sesión ──
        for key in [
            'paypal_payment_id', 'paypal_referencia', 'paypal_evento_id',
            'paypal_pendiente_id', 'paypal_pago_id', 'paypal_monto_bs',
        ]:
            request.session.pop(key, None)
        request.session.pop(f'carrito_{evento_id}', None)
        request.session.modified = True

        return redirect('compra_exitosa', venta_id=venta.id)

    except ValueError as e:
        pendiente_id = request.session.get('paypal_pendiente_id')
        if pendiente_id:
            try:
                pendiente = PagoPayPalPendiente.objects.get(id=pendiente_id)
                pendiente.estado = 'rechazado'
                pendiente.save(update_fields=['estado'])
            except Exception:
                pass
        messages.error(request, f'Error al procesar el pago: {str(e)}')
        return redirect('finalizar_compra', evento_id=evento_id)
    except Exception as e:
        logger.exception('Error al ejecutar pago PayPal')
        messages.error(request, f'Error al confirmar el pago con PayPal: {str(e)}')
        return redirect('finalizar_compra', evento_id=evento_id)


@never_cache
@require_GET
def paypal_cancel_view(request, evento_id):
    """Vista cuando el usuario cancela el pago en PayPal."""
    messages.warning(request, 'Cancelaste el pago con PayPal. Puedes elegir otro método de pago.')

    pendiente_id = request.session.get('paypal_pendiente_id')
    if pendiente_id:
        try:
            pendiente = PagoPayPalPendiente.objects.get(id=pendiente_id)
            pendiente.estado = 'cancelado'
            pendiente.save(update_fields=['estado'])

            pago_id = request.session.get('paypal_pago_id')
            if pago_id:
                try:
                    pago = Pago.objects.get(id=pago_id)
                    reserva = pago.reserva
                    pago.delete()
                    reserva.delete()
                except Exception:
                    pass
        except Exception:
            pass

    for key in [
        'paypal_payment_id', 'paypal_referencia', 'paypal_evento_id',
        'paypal_pendiente_id', 'paypal_pago_id', 'paypal_monto_bs',
    ]:
        request.session.pop(key, None)
    request.session.modified = True

    return redirect('finalizar_compra', evento_id=evento_id)


@csrf_exempt
@require_POST
def paypal_webhook_view(request):
    """
    Webhook para recibir notificaciones async de PayPal.
    PayPal envía notificaciones cuando el estado de un pago cambia
    (ej: si el redirect falló pero el pago se aprobó en PayPal).
    """
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        logger.warning('PayPal webhook: body inválido')
        return HttpResponse(status=400)

    event_type = body.get('event_type', '')
    resource = body.get('resource', {})
    payment_id = resource.get('id', '')

    logger.info(f'PayPal webhook recibido: {event_type} - payment_id: {payment_id}')

    if not payment_id:
        return HttpResponse(status=400)

    try:
        pendiente = PagoPayPalPendiente.objects.get(paypal_payment_id=payment_id)
    except PagoPayPalPendiente.DoesNotExist:
        logger.warning(f'PayPal webhook: pago pendiente no encontrado: {payment_id}')
        return HttpResponse(status=200)

    if event_type == 'PAYMENT.SALE.COMPLETED':
        if pendiente.estado == 'procesado':
            return HttpResponse(status=200)

        pendiente.estado = 'aprobado'
        pendiente.save(update_fields=['estado'])

        logger.info(f'PayPal webhook: pago {payment_id} aprobado via webhook, procesando...')
        try:
            reserva = Reserva.objects.filter(
                usuario_id=pendiente.usuario_id,
                evento_id=pendiente.evento_id,
            ).order_by('-fecha_creacion').first()

            if reserva:
                existing_pago = Pago.objects.filter(
                    reserva=reserva,
                    estado_pago__nombre__iexact='pagado',
                ).first()

                if not existing_pago:
                    pago_pendiente = Pago.objects.filter(
                        reserva=reserva,
                        estado_pago__nombre__iexact='pendiente',
                    ).first()

                    if pago_pendiente:
                        estado_pagado = _obtener_o_crear_estado_pago('pagado')
                        pago_pendiente.estado_pago = estado_pagado
                        pago_pendiente.referencia_externa = payment_id
                        pago_pendiente.fecha_confirmacion = timezone.now()
                        pago_pendiente.observacion = (
                            f'Pago aprobado via PayPal webhook - '
                            f'Ref: {pendiente.referencia}'
                        )
                        pago_pendiente.save(update_fields=[
                            'estado_pago', 'referencia_externa',
                            'fecha_confirmacion', 'observacion',
                        ])

                        pendiente.estado = 'procesado'
                        pendiente.save(update_fields=['estado'])

                        logger.info(
                            f'PayPal webhook: pago {payment_id} procesado exitosamente'
                        )
        except Exception as e:
            logger.exception(f'PayPal webhook: error al procesar pago {payment_id}')

    elif event_type in ('PAYMENT.SALE.DENIED', 'PAYMENT.SALE.REFUNDED'):
        pendiente.estado = 'rechazado'
        pendiente.save(update_fields=['estado'])

    return HttpResponse(status=200)


@never_cache
@require_GET
def paypal_status_view(request):
    """API para verificar si PayPal está configurado (para el frontend)."""
    configured = (
        settings.PAYPAL_CLIENT_ID != 'TU_CLIENT_ID_AQUI'
        and settings.PAYPAL_CLIENT_SECRET != 'TU_CLIENT_SECRET_AQUI'
    )
    return JsonResponse({
        'configured': configured,
        'mode': settings.PAYPAL_MODE,
    })
