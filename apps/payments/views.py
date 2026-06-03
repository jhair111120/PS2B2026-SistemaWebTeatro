"""
Vistas para el pago con PayPal.

Flujo:
1. Usuario hace clic en "Pagar con PayPal" → paypal_create_view
2. Se crea el pago en PayPal y se redirige al usuario
3. Usuario aprueba el pago en PayPal
4. PayPal redirige a paypal_execute_view
5. Se ejecuta el pago y se crea la venta
"""
import json
import logging

from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from apps.events.models import Evento
from apps.reservations.services import procesar_compra

from .paypal_service import crear_pago, ejecutar_pago

logger = logging.getLogger(__name__)


@never_cache
@require_POST
def paypal_create_view(request, evento_id):
    """
    Crea un pago en PayPal y redirige al usuario para que lo apruebe.
    """
    # Verificar login
    if not request.session.get('usuario_id'):
        messages.error(request, 'Debes iniciar sesión para pagar.')
        return redirect('login')

    # Obtener carrito de sesión
    carrito_raw = request.session.get(f'carrito_{evento_id}', [])
    if not carrito_raw:
        messages.error(request, 'Tu carrito está vacío. Selecciona las zonas nuevamente.')
        return redirect('seleccionar_zona', evento_id=evento_id)

    # Calcular total (misma lógica que finalizar_compra_view)
    from decimal import Decimal
    from apps.events.models import EventoZona

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
    total_bs = subtotal + cargo_servicio

    if total_bs <= 0:
        messages.error(request, 'El total no puede ser cero.')
        return redirect('seleccionar_zona', evento_id=evento_id)

    # Convertir a USD para PayPal
    rate = settings.PAYPAL_RATE_TO_USD
    total_usd = float(total_bs / Decimal(str(rate)))

    # Referencia única
    import uuid
    referencia = f"TEATRO-{evento_id}-{uuid.uuid4().hex[:8].upper()}"

    # URLs de retorno
    base_url = request.build_absolute_uri('/').rstrip('/')
    return_url = f'{base_url}/pago/paypal/execute/'
    cancel_url = f'{base_url}/comprar-entrada/{evento_id}/finalizar/'

    try:
        payment = crear_pago(
            monto_bs=total_bs,
            monto_usd=total_usd,
            referencia=referencia,
            evento_id=evento_id,
            return_url=return_url,
            cancel_url=cancel_url,
        )

        # Guardar datos en sesión para ejecutar después
        request.session['paypal_payment_id'] = payment.id
        request.session['paypal_referencia'] = referencia
        request.session['paypal_evento_id'] = evento_id
        request.session.modified = True

        # Redirigir a PayPal
        for link in payment.links:
            if link.rel == 'approval_url':
                return redirect(link.href)

        messages.error(request, 'No se pudo obtener la URL de pago de PayPal.')
        return redirect('finalizar_compra', evento_id=evento_id)

    except ValueError as e:
        messages.error(request, str(e))
        return redirect('finalizar_compra', evento_id=evento_id)
    except Exception as e:
        logger.exception('Error al crear pago PayPal')
        messages.error(request, f'Error al conectar con PayPal: {str(e)}')
        return redirect('finalizar_compra', evento_id=evento_id)


@never_cache
@require_GET
def paypal_execute_view(request):
    """
    Ejecuta el pago después de que PayPal redirige de vuelta.
    PayPal envía: paymentId, PayerID, token
    """
    # Verificar login
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

    # Verificar que el payment_id coincida con el de sesión
    session_payment_id = request.session.get('paypal_payment_id')
    if session_payment_id and session_payment_id != payment_id:
        messages.error(request, 'El ID de pago no coincide. Intenta nuevamente.')
        return redirect('finalizar_compra', evento_id=evento_id)

    try:
        # Ejecutar el pago en PayPal
        payment = ejecutar_pago(payment_id, payer_id)

        if payment.state != 'approved':
            messages.error(request, 'El pago no fue aprobado por PayPal.')
            return redirect('finalizar_compra', evento_id=evento_id)

        # Obtener referencia y carrito
        referencia = request.session.get('paypal_referencia', '')
        carrito_raw = request.session.get(f'carrito_{evento_id}', [])

        if not carrito_raw:
            messages.error(request, 'Tu sesión expiró. Selecciona las zonas nuevamente.')
            return redirect('seleccionar_zona', evento_id=evento_id)

        # Preparar items para procesar_compra
        items = [
            {
                'evento_zona_id': item.get('zona_id'),
                'evento_asiento_ids': item.get('asiento_ids', []),
                'cantidad': item.get('qty', 1),
            }
            for item in carrito_raw
        ]

        # Procesar la compra
        venta = procesar_compra(
            usuario_id=request.session['usuario_id'],
            evento_id=evento_id,
            items=items,
            metodo_pago_nombre='PayPal',
        )

        # Actualizar el pago con referencia de PayPal
        from apps.payments.models import Pago
        pago = venta.reserva.pagos.first()
        if pago:
            pago.referencia_externa = payment_id
            pago.observacion = f'Pago aprobado vía PayPal - Ref: {referencia}'
            pago.save(update_fields=['referencia_externa', 'observacion'])

        # Limpiar sesión
        for key in ['paypal_payment_id', 'paypal_referencia', 'paypal_evento_id']:
            request.session.pop(key, None)
        request.session.pop(f'carrito_{evento_id}', None)
        request.session.modified = True

        return redirect('compra_exitosa', venta_id=venta.id)

    except ValueError as e:
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

    # Limpiar datos de PayPal de sesión
    for key in ['paypal_payment_id', 'paypal_referencia', 'paypal_evento_id']:
        request.session.pop(key, None)
    request.session.modified = True

    return redirect('finalizar_compra', evento_id=evento_id)


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
