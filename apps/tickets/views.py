"""
Vista de Mis Entradas para el cliente.
"""
from django.shortcuts import redirect, render
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
