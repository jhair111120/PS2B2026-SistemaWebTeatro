import json
import random
from zoneinfo import ZoneInfo
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.cache import never_cache

from .models import Soporte, SoporteMensaje, EstadoSoporte, CategoriaSoporte
from apps.users.models import Usuario

# ================= FUNCIÓN DE SEGURIDAD (ADMIN) =================
def es_personal_autorizado(request):
    if 'usuario_id' not in request.session:
        return False
    rol = request.session.get('usuario_rol', '').lower()
    return rol in ['soporte', 'administrador', 'admin']


# ================= VISTAS DE SOPORTE (ADMINISTRADOR) =================
@never_cache
def support_dashboard(request):
    if not es_personal_autorizado(request):
        messages.error(request, "Acceso denegado. Área exclusiva para personal.")
        return redirect('/?action=login')

    # 🔥 CORRECCIÓN: Traemos TODOS los tickets para que los botones de filtro funcionen
    todos_los_tickets = Soporte.objects.select_related('usuario', 'estado_soporte', 'categoria_soporte').order_by('-fecha_creacion')
    
    # 🔥 CORRECCIÓN: Conteo exacto sin multiplicar por cantidad de mensajes
    total_tickets = todos_los_tickets.count()
    tickets_no_leidos = todos_los_tickets.filter(fecha_cierre__isnull=True).count() # Abiertos (No leídos/Pendientes)
    tickets_leidos = todos_los_tickets.filter(fecha_cierre__isnull=False).count() # Cerrados (Leídos/Resueltos)

    contexto = {
        'tickets': todos_los_tickets,
        'total_tickets': total_tickets,
        'tickets_no_leidos': tickets_no_leidos,
        'tickets_leidos': tickets_leidos,
    }
    return render(request, 'pages/soporte/soporte.html', contexto)


def ticket_messages_api(request, ticket_id):
    if not es_personal_autorizado(request): return JsonResponse({'error': 'No autorizado'}, status=403)
    if request.method == 'GET':
        ticket = get_object_or_404(Soporte, pk=ticket_id)
        mensajes_db = ticket.mensajes.select_related('remitente').all().order_by('fecha_envio')
        
        tz_bolivia = ZoneInfo('America/La_Paz')
        mensajes_list = []
        for msg in mensajes_db:
            hora_local = msg.fecha_envio.astimezone(tz_bolivia)
            mensajes_list.append({
                'id': msg.id,
                'remitente_id': msg.remitente.id,
                'remitente_nombre': f"{msg.remitente.nombre} {msg.remitente.apellido}",
                'mensaje': msg.mensaje,
                'fecha_envio_formateada': hora_local.strftime("%d %b, %I:%M %p"), 
                'es_admin_respuesta': (msg.remitente.rol.nombre.lower() in ['soporte', 'administrador']) 
            })
            
        return JsonResponse({
            'ticket_id': ticket.id,
            'numero_reclamo': ticket.numero_reclamo,
            'usuario_nombre': f"{ticket.usuario.nombre} {ticket.usuario.apellido}",
            'usuario_correo': ticket.usuario.correo,
            'estado_ticket': ticket.estado_soporte.nombre,
            'mensajes': mensajes_list
        })
    return JsonResponse({'error': 'Método no permitido'}, status=405)


def send_message_api(request):
    if not es_personal_autorizado(request): return JsonResponse({'error': 'No autorizado'}, status=403)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ticket_id, mensaje_texto = data.get('ticket_id'), data.get('mensaje')
            if not ticket_id or not mensaje_texto: return JsonResponse({'error': 'Datos incompletos'}, status=400)
                
            ticket = get_object_or_404(Soporte, pk=ticket_id)
            admin_usuario = Usuario.objects.get(id=request.session['usuario_id']) 
            
            nuevo_mensaje = SoporteMensaje.objects.create(
                soporte=ticket, remitente=admin_usuario, mensaje=mensaje_texto, fecha_envio=timezone.now()
            )
            
            tz_bolivia = ZoneInfo('America/La_Paz')
            hora_local = nuevo_mensaje.fecha_envio.astimezone(tz_bolivia)
            return JsonResponse({
                'success': True, 'id': nuevo_mensaje.id,
                'remitente_nombre': f"{admin_usuario.nombre} {admin_usuario.apellido}",
                'mensaje': nuevo_mensaje.mensaje,
                'fecha_envio_formateada': hora_local.strftime("%d %b, %I:%M %p"),
                'es_admin_respuesta': True 
            })
        except Exception as e: return JsonResponse({'error': f'Error: {str(e)}'}, status=500)
    return JsonResponse({'error': 'Método no permitido'}, status=405)


def close_ticket_api(request):
    if not es_personal_autorizado(request): return JsonResponse({'error': 'No autorizado'}, status=403)
    if request.method == 'POST':
        try:
            ticket_id = json.loads(request.body).get('ticket_id')
            if not ticket_id: return JsonResponse({'error': 'ID faltante'}, status=400)
            ticket = get_object_or_404(Soporte, pk=ticket_id)
            
            estado_cerrado, _ = EstadoSoporte.objects.get_or_create(nombre='Cerrado') 
            ticket.estado_soporte = estado_cerrado
            ticket.fecha_cierre = timezone.now()
            ticket.save() 
            return JsonResponse({'success': True, 'nuevo_estado': estado_cerrado.nombre})
        except Exception as e: return JsonResponse({'error': f'Error: {str(e)}'}, status=500)
    return JsonResponse({'error': 'Método no permitido'}, status=405)


# ================= VISTAS DE SOPORTE (CLIENTE) =================

@never_cache 
def cliente_soporte_view(request, ticket_id=None):
    if 'usuario_id' not in request.session:
        messages.error(request, "Debes iniciar sesión para contactar a soporte.")
        return redirect('/?action=login')

    usuario_id = request.session['usuario_id']
    
    mis_tickets = Soporte.objects.filter(usuario_id=usuario_id).order_by('-fecha_creacion')
    
    ticket_seleccionado = None
    if ticket_id:
        ticket_seleccionado = get_object_or_404(Soporte, id=ticket_id, usuario_id=usuario_id)

    if request.method == 'POST':
        asunto = request.POST.get('asunto', '').strip()
        categoria_id = request.POST.get('categoria')
        descripcion = request.POST.get('descripcion', '').strip()

        if asunto and categoria_id and descripcion:
            try:
                estado_abierto, _ = EstadoSoporte.objects.get_or_create(nombre='Abierto')
                
                try:
                    categoria = CategoriaSoporte.objects.get(id=categoria_id)
                except CategoriaSoporte.DoesNotExist:
                    categoria, _ = CategoriaSoporte.objects.get_or_create(nombre='Soporte General')
                
                usuario = Usuario.objects.get(id=usuario_id)
                
                nuevo_ticket = Soporte.objects.create(
                    numero_reclamo=f"TKT-{random.randint(100000, 999999)}",
                    usuario=usuario,
                    categoria_soporte=categoria,
                    estado_soporte=estado_abierto,
                    asunto=asunto,
                    descripcion=descripcion,
                    fecha_creacion=timezone.now()
                )
                
                SoporteMensaje.objects.create(
                    soporte=nuevo_ticket, remitente=usuario, mensaje=descripcion, fecha_envio=timezone.now()
                )
                
                messages.success(request, "Ticket creado con éxito. Te responderemos pronto.")
                return redirect('cliente_soporte_detalle', ticket_id=nuevo_ticket.id)
            except Exception as e:
                print(f"\n--- ERROR AL CREAR TICKET ---\n{str(e)}\n-----------------------------\n")
                messages.error(request, "Ocurrió un error al crear el ticket. Inténtalo de nuevo.")

    categorias = CategoriaSoporte.objects.all()

    return render(request, 'pages/usuarios/cliente_soporte.html', {
        'mis_tickets': mis_tickets,
        'ticket_seleccionado': ticket_seleccionado,
        'categorias': categorias
    })


def cliente_mensajes_api(request, ticket_id):
    if 'usuario_id' not in request.session: return JsonResponse({'error': 'No autorizado'}, status=403)
    usuario_id = request.session['usuario_id']
    
    ticket = Soporte.objects.filter(id=ticket_id, usuario_id=usuario_id).first()
    if not ticket: return JsonResponse({'error': 'Ticket no encontrado'}, status=404)
        
    mensajes_db = ticket.mensajes.select_related('remitente').all().order_by('fecha_envio')
    
    tz_bolivia = ZoneInfo('America/La_Paz') 
    mensajes_list = []
    
    for msg in mensajes_db:
        hora_local = msg.fecha_envio.astimezone(tz_bolivia)
        mensajes_list.append({
            'id': msg.id,
            'remitente_nombre': "Tú" if msg.remitente.id == usuario_id else "Soporte Teatro La Paz",
            'mensaje': msg.mensaje,
            'fecha_envio_formateada': hora_local.strftime("%I:%M %p"), 
            'es_mio': (msg.remitente.id == usuario_id)
        })
    
    return JsonResponse({'mensajes': mensajes_list, 'ticket_cerrado': ticket.fecha_cierre is not None})


def cliente_enviar_mensaje_api(request, ticket_id):
    if 'usuario_id' not in request.session: return JsonResponse({'error': 'No autorizado'}, status=403)
    if request.method == 'POST':
        try:
            mensaje_texto = json.loads(request.body).get('mensaje')
            if not mensaje_texto: return JsonResponse({'error': 'Mensaje vacío'}, status=400)
                
            usuario_id = request.session['usuario_id']
            ticket = Soporte.objects.filter(id=ticket_id, usuario_id=usuario_id).first()
            if not ticket: return JsonResponse({'error': 'Ticket no encontrado'}, status=404)
            if ticket.fecha_cierre is not None: return JsonResponse({'error': 'El ticket está cerrado'}, status=400)
                
            usuario = Usuario.objects.get(id=usuario_id)
            nuevo_msg = SoporteMensaje.objects.create(
                soporte=ticket, remitente=usuario, mensaje=mensaje_texto, fecha_envio=timezone.now()
            )
            
            tz_bolivia = ZoneInfo('America/La_Paz') 
            hora_local = nuevo_msg.fecha_envio.astimezone(tz_bolivia)
            
            return JsonResponse({
                'success': True,
                'remitente_nombre': "Tú",
                'mensaje': nuevo_msg.mensaje,
                'fecha_envio_formateada': hora_local.strftime("%I:%M %p"),
                'es_mio': True
            })
        except Exception as e: return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Método no permitido'}, status=405)