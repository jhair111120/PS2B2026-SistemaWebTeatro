"""
Vista de Mis Entradas para el cliente.
"""


import json
from django.http import JsonResponse
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt

from apps.events.models import Evento, EventoZona
from apps.reservations.models import Reserva, DetalleReserva
from apps.payments.models import Pago, MetodoPago
from .models import Entrada, Venta, EstadoVenta, EstadoEntrada

from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.contrib import messages

from .models import Entrada, Venta


@never_cache
def mis_tickets_view(request):
    if not request.session.get('usuario_id'):
        messages.error(request, 'Debes iniciar sesión para ver tus entradas.')
        return redirect('/?action=login')

    usuario_id = request.session['usuario_id']
    hoy = timezone.localdate()

    ventas = (
        Venta.objects.select_related(
            'reserva__evento',
            'estado_venta',
        )
        .prefetch_related(
            'entradas__detalle_reserva__evento_zona__zona',
            'entradas__estado_entrada',
            'reserva__pagos__metodo_pago',
        )
        .filter(usuario_id=usuario_id)
        .order_by('-fecha_venta')
    )

    proximas = []
    pasadas = []

    for venta in ventas:
        fecha_ev = venta.reserva.evento.fecha_evento
        entradas_list = list(venta.entradas.all())
        primer_pago = venta.reserva.pagos.first()

        item = {
            'venta': venta,
            'evento': venta.reserva.evento,
            'entradas': entradas_list,
            'primer_pago': primer_pago,
        }

        if fecha_ev >= hoy:
            proximas.append(item)
        else:
            pasadas.append(item)

    return render(request, 'pages/tickets/tickets.html', {
        'proximas': proximas,
        'pasadas': pasadas,
    })

# --- VISTAS DE BOLETERÍA (venta presencial) ---

from django.views.decorators.http import require_POST as _require_post_bole
from apps.reservations.services import procesar_compra as _procesar_compra
from datetime import timedelta as _timedelta
import uuid as _uuid

def boleteria_view(request):
    """Interfaz principal de boletería — solo para empleados/admin."""
    if not request.session.get('usuario_id'):
        return redirect('/?action=login')
    rol = (request.session.get('usuario_rol') or '').strip().lower()
    if rol not in ('administrador', 'empleado'):
        messages.error(request, 'Acceso restringido al personal del teatro.')
        return redirect('inicio')

    hoy = timezone.localdate()
    eventos = (
        Evento.objects
        .select_related('estado_evento')
        .filter(
            estado_evento__nombre__icontains='activ',
            fecha_evento__gte=hoy,
        )
        .order_by('fecha_evento', 'hora_evento')
    )
    return render(request, 'pages/tickets/boleteria.html', {'eventos': eventos})


def api_get_zonas(request, evento_id):
    """Endpoint AJAX — devuelve las zonas habilitadas de un evento."""
    if not request.session.get('usuario_id'):
        return JsonResponse({'error': 'No autenticado'}, status=401)

    zonas_qs = (
        EventoZona.objects
        .select_related('zona')
        .filter(evento_id=evento_id, habilitada=True)
        .order_by('-precio_base')
    )
    data = {
        'zonas': [
            {
                'id':     z.id,
                'nombre': z.zona.nombre,
                'precio': float(z.precio_base),
                'limite': z.limite_por_usuario,
                'color':  z.zona.codigo_color or '#1E293B',
            }
            for z in zonas_qs
        ]
    }
    return JsonResponse(data)


@transaction.atomic
def boleteria_confirmar_view(request):
    """Procesa la venta presencial usando el mismo servicio que la web."""
    if request.method != 'POST':
        return redirect('boleteria')

    if not request.session.get('usuario_id'):
        return redirect('/?action=login')

    try:
        carrito_json    = request.POST.get('carrito_json', '[]')
        metodo_pago     = request.POST.get('metodo_pago', 'Efectivo')
        evento_id       = int(request.POST.get('evento_id', 0))
        carrito_raw     = json.loads(carrito_json)

        if not carrito_raw or not evento_id:
            messages.error(request, 'Carrito vacío o evento no seleccionado.')
            return redirect('boleteria')

        # Convertir formato del carrito de boletería al formato de procesar_compra
        items = [
            {
                'evento_zona_id':    item.get('evento_zona_id'),
                'evento_asiento_ids': [],
                'cantidad':          int(item.get('cantidad', 1)),
            }
            for item in carrito_raw
        ]

        venta = _procesar_compra(
            usuario_id=request.session['usuario_id'],
            evento_id=evento_id,
            items=items,
            metodo_pago_nombre=metodo_pago,
        )

        return render(request, 'pages/tickets/boleteria_exitosa.html', {
            'venta':       venta,
            'entradas':    venta.entradas.all(),
            'primer_pago': venta.reserva.pagos.select_related('metodo_pago').first(),
        })

    except ValueError as e:
        messages.error(request, str(e))
    except Exception as e:
        messages.error(request, f'Error al procesar la venta: {e}')

    return redirect('boleteria')