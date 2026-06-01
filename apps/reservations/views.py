"""
Vistas del flujo de compra para el cliente:
  seleccionar_zona → seleccionar_asientos → finalizar_compra → compra_exitosa
"""
import json
from decimal import Decimal

from django.contrib import messages
from django.db.models import Min, Sum, Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST, require_GET

from apps.events.models import Evento, EventoZona, EventoAsiento, Asiento
from apps.tickets.models import Entrada, Venta

from .services import procesar_compra


# ─────────────────────────────────────────────
# GUARD
# ─────────────────────────────────────────────

def _require_login(request, next_url=None):
    if not request.session.get('usuario_id'):
        messages.error(request, 'Debes iniciar sesión para comprar entradas.')
        dest = '/?action=login'
        if next_url:
            dest += f'&next={next_url}'
        return redirect(dest)
    return None


# ─────────────────────────────────────────────
# PASO 2: SELECCIONAR ZONA
# ─────────────────────────────────────────────

@never_cache
def seleccionar_zona_view(request, evento_id):
    hoy = timezone.localdate()
    evento = get_object_or_404(
        Evento.objects.select_related('estado_evento').prefetch_related('eventozona_set__zona'),
        pk=evento_id,
        estado_evento__nombre__icontains='activ',
        fecha_evento__gte=hoy,
    )

    zonas = (
        evento.eventozona_set
        .select_related('zona')
        .filter(habilitada=True)
        .order_by('-precio_base')
    )

    zonas_data = []
    for ez in zonas:
        disponibles = EventoAsiento.objects.filter(
            evento_zona=ez, estado=EventoAsiento.Estado.DISPONIBLE
        ).count()
        zonas_data.append({
            'id': ez.id,
            'nombre': ez.zona.nombre.upper(),
            'nombre_display': (ez.nombre_display or ez.zona.nombre).upper(),
            'precio': float(ez.precio_base),
            'limite': ez.limite_por_usuario,
            'color': ez.zona.codigo_color or '#1E293B',
            'capacidad': ez.capacidad_evento or 0,
            'disponibles': disponibles,
        })

    user_logged_in = request.session.get('usuario_id') is not None
    return render(request, 'pages/users/seleccionar_zona.html', {
        'evento': evento,
        'zonas_data': zonas_data,
        'zonas_json': json.dumps(zonas_data),
        'user_logged_in': user_logged_in,
    })


# ─────────────────────────────────────────────
# PASO 2b: SELECCIONAR ASIENTOS (nueva vista)
# ─────────────────────────────────────────────

@never_cache
def seleccionar_asientos_view(request, evento_id, evento_zona_id):
    hoy = timezone.localdate()
    evento = get_object_or_404(
        Evento.objects.select_related('estado_evento'),
        pk=evento_id,
        estado_evento__nombre__icontains='activ',
        fecha_evento__gte=hoy,
    )
    ez = get_object_or_404(
        EventoZona.objects.select_related('zona'),
        pk=evento_zona_id,
        evento=evento,
        habilitada=True,
    )

    # Obtener todos los asientos con su estado
    evento_asientos = (
        EventoAsiento.objects
        .select_related('asiento')
        .filter(evento_zona=ez)
        .order_by('asiento__fila', 'asiento__numero')
    )

    # Agrupar por fila
    filas = {}
    for ea in evento_asientos:
        fila = ea.asiento.fila
        if fila not in filas:
            filas[fila] = []
        filas[fila].append({
            'id': ea.id,
            'fila': fila,
            'numero': ea.asiento.numero,
            'estado': ea.estado,
            'disponible': ea.estado == EventoAsiento.Estado.DISPONIBLE,
        })

    filas_ordenadas = sorted(filas.items())
    asientos_json = json.dumps([
        {
            'id': ea.id,
            'fila': ea.asiento.fila,
            'numero': ea.asiento.numero,
            'estado': ea.estado,
        }
        for ea in evento_asientos
    ])

    user_logged_in = request.session.get('usuario_id') is not None
    return render(request, 'pages/users/seleccionar_asientos.html', {
        'evento': evento,
        'ez': ez,
        'filas': filas_ordenadas,
        'asientos_json': asientos_json,
        'limite': ez.limite_por_usuario,
        'precio': ez.precio_base,
        'color': ez.zona.codigo_color or '#1E293B',
        'user_logged_in': user_logged_in,
    })


# ─────────────────────────────────────────────
# API: ASIENTOS DISPONIBLES (JSON)
# ─────────────────────────────────────────────

@require_GET
def api_asientos_view(request, evento_id, evento_zona_id):
    if not request.session.get('usuario_id'):
        return JsonResponse({'error': 'No autenticado'}, status=401)

    ez = get_object_or_404(EventoZona, pk=evento_zona_id, evento_id=evento_id)
    asientos = (
        EventoAsiento.objects
        .select_related('asiento')
        .filter(evento_zona=ez)
        .order_by('asiento__fila', 'asiento__numero')
    )

    data = [
        {
            'id': ea.id,
            'fila': ea.asiento.fila,
            'numero': ea.asiento.numero,
            'estado': ea.estado,
            'disponible': ea.estado == EventoAsiento.Estado.DISPONIBLE,
        }
        for ea in asientos
    ]
    return JsonResponse({'asientos': data, 'limite': ez.limite_por_usuario})

# ─────────────────────────────────────────────

@never_cache
def carrito_view(request):
    """Página independiente del carrito de compras."""
    from decimal import Decimal as _D
    from apps.events.models import Evento as _Evento, EventoAsiento as _EA

    carritos = []
    prefix = 'carrito_'
    for key in list(request.session.keys()):
        if not key.startswith(prefix):
            continue
        evento_id_str = key[len(prefix):]
        try:
            evento_id = int(evento_id_str)
        except ValueError:
            continue
        carrito_raw = request.session.get(key, [])
        if not carrito_raw:
            continue
        evento = _Evento.objects.filter(id=evento_id).first()
        if not evento:
            continue
        items = []
        subtotal = _D('0')
        for item in carrito_raw:
            ez = EventoZona.objects.select_related('zona').filter(
                id=item.get('zona_id'), evento_id=evento_id
            ).first()
            if not ez:
                continue
            asiento_ids = item.get('asiento_ids', [])
            qty = len(asiento_ids) if asiento_ids else int(item.get('qty', 1))
            item_subtotal = ez.precio_base * qty
            subtotal += item_subtotal
            asientos_info = []
            if asiento_ids:
                eas = _EA.objects.select_related('asiento').filter(
                    id__in=asiento_ids, evento_zona=ez
                )
                asientos_info = [f"F {ea.asiento.fila}-{ea.asiento.numero}" for ea in eas]
            items.append({
                'zona_id': ez.id,
                'zona_nombre': ez.zona.nombre,
                'precio': ez.precio_base,
                'qty': qty,
                'subtotal': item_subtotal,
                'asientos_info': asientos_info,
                'asiento_ids': asiento_ids,
            })
        if items:
            cargo_servicio = _D('5.00')
            total = subtotal + cargo_servicio
            import json as _json
            carritos.append({
                'evento_id': evento_id,
                'evento': evento,
                'items': items,
                'items_json': _json.dumps([{
                    'zona_id': it['zona_id'],
                    'qty': it['qty'],
                    'asiento_ids': it.get('asiento_ids', []),
                } for it in items]),
                'subtotal': subtotal,
                'cargo_servicio': cargo_servicio,
                'total': total,
                'item_count': sum(it['qty'] for it in items),
            })

    return render(request, 'pages/users/carrito.html', {
        'carritos': carritos,
        'total_general': sum(c['total'] for c in carritos),
        'cart_count': sum(c['item_count'] for c in carritos),
    })


@never_cache
def finalizar_compra_view(request, evento_id):
    guard = _require_login(request, next_url=f'/comprar-entrada/{evento_id}/')
    if guard:
        return guard

    hoy = timezone.localdate()
    evento = get_object_or_404(
        Evento.objects.select_related('estado_evento'),
        pk=evento_id,
        estado_evento__nombre__icontains='activ',
        fecha_evento__gte=hoy,
    )

    if request.method == 'POST':
        # Recibir carrito desde el form (JSON)
        carrito_json = request.POST.get('carrito_json', '[]')
        try:
            carrito_raw = json.loads(carrito_json)
        except (json.JSONDecodeError, ValueError):
            carrito_raw = []

        if not carrito_raw:
            messages.error(request, 'No has seleccionado ninguna zona.')
            return redirect('seleccionar_zona', evento_id=evento_id)

        # Guardar en sesión para el segundo POST (confirmar pago)
        request.session[f'carrito_{evento_id}'] = carrito_raw
        request.session.modified = True

        # Enriquecer carrito con datos de BD para mostrar resumen
        carrito_enriquecido = []
        subtotal = Decimal('0')
        for item in carrito_raw:
            ez = EventoZona.objects.select_related('zona').filter(
                id=item.get('zona_id'), evento_id=evento_id
            ).first()
            if ez:
                asiento_ids = item.get('asiento_ids', [])
                qty = len(asiento_ids) if asiento_ids else int(item.get('qty', 1))
                item_subtotal = ez.precio_base * qty
                subtotal += item_subtotal

                # Obtener info de asientos si los hay
                asientos_info = []
                if asiento_ids:
                    from apps.events.models import EventoAsiento
                    eas = EventoAsiento.objects.select_related('asiento').filter(
                        id__in=asiento_ids, evento_zona=ez
                    )
                    asientos_info = [f"Fila {ea.asiento.fila}-{ea.asiento.numero}" for ea in eas]

                carrito_enriquecido.append({
                    'zona_id': ez.id,
                    'zona_nombre': ez.zona.nombre,
                    'precio': ez.precio_base,
                    'qty': qty,
                    'subtotal': item_subtotal,
                    'asientos_info': asientos_info,
                    'asiento_ids': asiento_ids,
                })

        cargo_servicio = Decimal('5.00') if carrito_enriquecido else Decimal('0')
        total = subtotal + cargo_servicio

        return render(request, 'pages/users/finalizar_compra.html', {
            'evento': evento,
            'carrito': carrito_enriquecido,
            'carrito_json': carrito_json,
            'subtotal': subtotal,
            'cargo_servicio': cargo_servicio,
            'total': total,
        })

@never_cache
@require_POST
def confirmar_compra_view(request, evento_id):
    """Procesa el pago simulado y crea la venta en BD."""
    guard = _require_login(request, next_url=f'/comprar-entrada/{evento_id}/')
    if guard:
        return guard

    hoy = timezone.localdate()
    evento = get_object_or_404(
        Evento.objects.select_related('estado_evento'),
        pk=evento_id,
        estado_evento__nombre__icontains='activ',
        fecha_evento__gte=hoy,
    )

    # Leer carrito desde sesión (guardado en el paso anterior)
    carrito_raw = request.session.get(f'carrito_{evento_id}', [])

    if not carrito_raw:
        messages.error(request, 'Tu sesión expiró o el carrito está vacío. Selecciona las zonas nuevamente.')
        return redirect('seleccionar_zona', evento_id=evento_id)

    metodo_pago = request.POST.get('metodo_pago', 'Tarjeta de Crédito')

    items = [
        {
            'evento_zona_id': item.get('zona_id'),
            'evento_asiento_ids': item.get('asiento_ids', []),
            'cantidad': item.get('qty', 1),
        }
        for item in carrito_raw
    ]

    try:
        venta = procesar_compra(
            usuario_id=request.session['usuario_id'],
            evento_id=evento_id,
            items=items,
            metodo_pago_nombre=metodo_pago,
        )
        # Limpiar carrito de sesión
        request.session.pop(f'carrito_{evento_id}', None)
        request.session.modified = True

        return redirect('compra_exitosa', venta_id=venta.id)

    except ValueError as e:
        messages.error(request, str(e))
    except Exception as e:
        messages.error(request, f'Error al procesar la compra: {str(e)}')

    return redirect('seleccionar_zona', evento_id=evento_id)


# ─────────────────────────────────────────────
# PASO 4: COMPRA EXITOSA
# ─────────────────────────────────────────────

@never_cache
def compra_exitosa_view(request, venta_id):
    guard = _require_login(request)
    if guard:
        return guard

    venta = get_object_or_404(
        Venta.objects.select_related(
            'reserva__evento',
            'estado_venta',
        ).prefetch_related(
            'reserva__pagos__metodo_pago',
            'entradas__detalle_reserva__evento_zona__zona',
            'entradas__estado_entrada',
            'reserva__detalles__evento_zona__zona',
        ),
        pk=venta_id,
        usuario_id=request.session['usuario_id'],
    )

    primer_pago = venta.reserva.pagos.select_related('metodo_pago').first()

    return render(request, 'pages/users/compra_exitosa.html', {
        'venta': venta,
        'primer_pago': primer_pago,
        'entradas': venta.entradas.all(),
        'detalles': venta.reserva.detalles.all(),
    })


# ─────────────────────────────────────────────
# API: GUARDAR CARRITO EN SESIÓN (AJAX)
# ─────────────────────────────────────────────

@require_POST
def guardar_carrito_api(request, evento_id):
    if not request.session.get('usuario_id'):
        return JsonResponse({'error': 'No autenticado'}, status=401)

    try:
        data = json.loads(request.body)
        carrito = data.get('carrito', [])
        request.session[f'carrito_{evento_id}'] = carrito
        request.session.modified = True
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
