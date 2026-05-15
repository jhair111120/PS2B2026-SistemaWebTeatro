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

# --- NUEVAS VISTAS PARA BOLETERÍA ---

def boleteria_view(request):
    """Muestra la interfaz principal de boletería con eventos activos."""
    # Filtrar eventos que no han pasado y están publicados
    eventos = Evento.objects.filter(
        fecha_evento__gte=timezone.localdate(),
        estado_evento__nombre__in=['Publicado', 'Activo']
    ).order_by('fecha_evento')

    return render(request, 'pages/tickets/boleteria.html', {
        'eventos': eventos
    })

def api_get_zonas(request, evento_id):
    """Endpoint para cargar las zonas del evento vía AJAX."""
    zonas_evento = EventoZona.objects.filter(evento_id=evento_id)
    data = {
        'zonas': [
            {
                'id': z.id,
                'nombre': z.zona.nombre,
                'precio': float(z.precio),
                'limite': 10,  # Máximo por transacción en ventanilla
                'color': z.color_hex or '#00FFD1'
            } for z in zonas_evento
        ]
    }
    return JsonResponse(data)

@transaction.atomic
def boleteria_confirmar_view(request):
    """Procesa el POST del formulario, crea la venta y las entradas."""
    if request.method == 'POST':
        try:
            evento_id = request.POST.get('evento_id')
            carrito_json = request.POST.get('carrito_json')
            metodo_pago_nombre = request.POST.get('metodo_pago', 'Efectivo')
            carrito = json.loads(carrito_json)

            if not carrito:
                messages.error(request, "El carrito está vacío.")
                return redirect('boleteria')

            evento = Evento.objects.get(id=evento_id)
            
            # 1. Crear la Reserva
            reserva = Reserva.objects.create(
                evento=evento,
                usuario_id=None, # Es venta presencial, no requiere usuario cliente
                codigo_reserva=f"BOL-{timezone.now().strftime('%H%M%S')}",
                fecha_reserva=timezone.now(),
                expiracion=timezone.now() + timezone.timedelta(minutes=10)
            )

            total_venta = 0
            entradas_creadas = []

            # 2. Procesar Carrito (Detalles y Entradas)
            estado_ent = EstadoEntrada.objects.get(nombre='Válida')
            
            for item in carrito:
                ez = EventoZona.objects.get(id=item['evento_zona_id'])
                cantidad = int(item['cantidad'])
                subtotal = ez.precio * cantidad
                total_venta += subtotal

                # Crear detalle de reserva
                detalle = DetalleReserva.objects.create(
                    reserva=reserva,
                    evento_zona=ez,
                    cantidad=cantidad,
                    precio_unitario=ez.precio,
                    subtotal=subtotal
                )

                # Crear las entradas físicas (un registro por cada una)
                for _ in range(cantidad):
                    ticket = Entrada.objects.create(
                        detalle_reserva=detalle,
                        codigo_ticket=f"TKT-{timezone.now().timestamp()}",
                        descripcion_ubicacion=ez.zona.nombre,
                        precio_pagado=ez.precio,
                        estado_entrada=estado_ent
                    )
                    entradas_creadas.append(ticket)

            # 3. Registrar el Pago
            metodo = MetodoPago.objects.get(nombre__iexact=metodo_pago_nombre)
            pago = Pago.objects.create(
                reserva=reserva,
                metodo_pago=metodo,
                monto=total_venta,
                fecha_pago=timezone.now(),
                referencia_transaccion="VENTA_VENTANILLA",
                estado_pago='Completado'
            )

            # 4. Crear la Venta final
            estado_v = EstadoVenta.objects.get(nombre='Completado')
            venta = Venta.objects.create(
                reserva=reserva,
                total=total_venta,
                fecha_venta=timezone.now(),
                estado_venta=estado_v,
                # empleado=request.user.empleado (si tienes relación con empleado)
            )

            return render(request, 'pages/tickets/venta_exitosa.html', {
                'venta': venta,
                'entradas': entradas_creadas,
                'primer_pago': pago
            })

        except Exception as e:
            messages.error(request, f"Error al procesar la venta: {str(e)}")
            return redirect('boleteria')

    return redirect('boleteria')