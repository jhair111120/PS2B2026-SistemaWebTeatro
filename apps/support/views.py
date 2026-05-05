import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.views.decorators.http import require_GET, require_POST

from .models import Soporte, SoporteMensaje, EstadoSoporte
from apps.users.models import Usuario


# ================= 🔐 SEGURIDAD =================
def es_personal_autorizado(request):
    usuario_id = request.session.get('usuario_id')
    rol = request.session.get('usuario_rol', '').lower()

    if not usuario_id:
        return False

    return rol in ['soporte', 'administrador', 'admin']


def obtener_usuario(request):
    usuario_id = request.session.get('usuario_id')
    return Usuario.objects.filter(id=usuario_id).first()


# ================= 📊 DASHBOARD =================
def support_dashboard(request):
    if not es_personal_autorizado(request):
        messages.error(request, "Acceso restringido.")
        return redirect('/?action=login')

    tickets = Soporte.objects.select_related(
        'usuario',
        'estado_soporte',
        'categoria_soporte'
    ).order_by('-fecha_creacion')

    # Métricas más reales
    total_tickets = tickets.count()
    tickets_abiertos = tickets.filter(fecha_cierre__isnull=True).count()
    tickets_cerrados = tickets.filter(fecha_cierre__isnull=False).count()

    contexto = {
        'tickets': tickets[:50],  # ⚡ evita cargar miles
        'total_tickets': total_tickets,
        'tickets_abiertos': tickets_abiertos,
        'tickets_cerrados': tickets_cerrados,
    }

    return render(request, 'pages/soporte/soporte.html', contexto)


# ================= 💬 MENSAJES =================
@require_GET
def ticket_messages_api(request, ticket_id):
    if not es_personal_autorizado(request):
        return JsonResponse({'error': 'No autorizado'}, status=403)

    ticket = get_object_or_404(
        Soporte.objects.select_related('usuario', 'estado_soporte'),
        pk=ticket_id
    )

    mensajes = ticket.mensajes.select_related('remitente').order_by('fecha_envio')

    data = {
        'ticket_id': ticket.id,
        'numero_reclamo': ticket.numero_reclamo,
        'usuario_nombre': str(ticket.usuario),
        'usuario_correo': ticket.usuario.correo,
        'estado_ticket': ticket.estado_soporte.nombre,
        'mensajes': [
            {
                'id': m.id,
                'remitente_id': m.remitente.id,
                'remitente_nombre': str(m.remitente),
                'mensaje': m.mensaje,
                'fecha_envio': m.fecha_envio.isoformat(),
                'es_staff': m.remitente.rol.nombre.lower() in ['soporte', 'administrador']
            }
            for m in mensajes
        ]
    }

    return JsonResponse(data)


# ================= ✉️ ENVIAR MENSAJE =================
@require_POST
def send_message_api(request):
    if not es_personal_autorizado(request):
        return JsonResponse({'error': 'No autorizado'}, status=403)

    usuario = obtener_usuario(request)
    if not usuario:
        return JsonResponse({'error': 'Sesión inválida'}, status=401)

    try:
        data = json.loads(request.body)

        ticket_id = data.get('ticket_id')
        mensaje_texto = data.get('mensaje', '').strip()

        if not ticket_id or not mensaje_texto:
            return JsonResponse({'error': 'Datos incompletos'}, status=400)

        ticket = get_object_or_404(Soporte, pk=ticket_id)

        if ticket.fecha_cierre:
            return JsonResponse({'error': 'El ticket está cerrado'}, status=400)

        with transaction.atomic():
            mensaje = SoporteMensaje.objects.create(
                soporte=ticket,
                remitente=usuario,
                mensaje=mensaje_texto
            )

            # 🔥 Auto reabrir si estaba cerrado (opcional)
            if ticket.estado_soporte.nombre.lower() == 'cerrado':
                estado_abierto = EstadoSoporte.objects.filter(nombre='abierto').first()
                if estado_abierto:
                    ticket.estado_soporte = estado_abierto
                    ticket.fecha_cierre = None
                    ticket.save()

        return JsonResponse({
            'success': True,
            'mensaje': {
                'id': mensaje.id,
                'remitente': str(usuario),
                'texto': mensaje.mensaje,
                'fecha': mensaje.fecha_envio.isoformat()
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    except Exception:
        return JsonResponse({'error': 'Error interno'}, status=500)


# ================= 🔒 CERRAR TICKET =================
@require_POST
def close_ticket_api(request):
    if not es_personal_autorizado(request):
        return JsonResponse({'error': 'No autorizado'}, status=403)

    try:
        data = json.loads(request.body)
        ticket_id = data.get('ticket_id')

        if not ticket_id:
            return JsonResponse({'error': 'ID requerido'}, status=400)

        ticket = get_object_or_404(Soporte, pk=ticket_id)

        estado_cerrado = EstadoSoporte.objects.filter(nombre='cerrado').first()
        if not estado_cerrado:
            return JsonResponse({'error': 'Estado no configurado'}, status=500)

        with transaction.atomic():
            ticket.estado_soporte = estado_cerrado
            ticket.fecha_cierre = timezone.now()
            ticket.save()

        return JsonResponse({
            'success': True,
            'estado': estado_cerrado.nombre
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    except Exception:
        return JsonResponse({'error': 'Error interno'}, status=500)