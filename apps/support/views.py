import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone

# Importamos tus modelos de soporte
from .models import Soporte, SoporteMensaje, EstadoSoporte
# Importamos el modelo Usuario desde tu aplicación users
from apps.users.models import Usuario

# ================= FUNCIÓN DE SEGURIDAD PERSONALIZADA =================
def es_personal_autorizado(request):
    """
    Verifica si el usuario inició sesión en nuestro sistema personalizado
    y si tiene un rol permitido (soporte o administrador).
    """
    if 'usuario_id' not in request.session:
        return False
    
    rol = request.session.get('usuario_rol', '').lower()
    return rol in ['soporte', 'administrador', 'admin']


# ================= VISTA PRINCIPAL (CARGA LA ESTRUCTURA) =================
def support_dashboard(request):
    # CANDADO DE SEGURIDAD
    if not es_personal_autorizado(request):
        messages.error(request, "Acceso denegado. Esta área es exclusiva para el personal de soporte.")
        return redirect('/?action=login') # Te manda a tu inicio y abre tu modal bonito

    # Obtenemos todos los tickets que NO estén cerrados
    tickets_abiertos = Soporte.objects.filter(
        fecha_cierre__isnull=True 
    ).select_related('usuario', 'estado_soporte', 'categoria_soporte').order_by('-fecha_creacion')

    # Contadores para las tarjetas superiores
    total_tickets = Soporte.objects.count()
    tickets_no_leidos = Soporte.objects.filter(mensajes__isnull=True).count() 
    tickets_leidos = Soporte.objects.filter(mensajes__isnull=False).count() 

    contexto = {
        'tickets': tickets_abiertos,
        'total_tickets': total_tickets,
        'tickets_no_leidos': tickets_no_leidos,
        'tickets_leidos': tickets_leidos,
    }
    return render(request, 'pages/soporte/soporte.html', contexto)


# ================= APIs PARA AJAX (DEVUELVEN JSON) =================

def ticket_messages_api(request, ticket_id):
    """Devuelve los mensajes de un ticket específico en formato JSON."""
    if not es_personal_autorizado(request):
        return JsonResponse({'error': 'No autorizado'}, status=403)

    if request.method == 'GET':
        # Buscamos el ticket de forma segura
        ticket = get_object_or_404(Soporte, pk=ticket_id)
        mensajes_db = ticket.mensajes.select_related('remitente').all().order_by('fecha_envio')
        
        # Formateamos los mensajes para JSON
        mensajes_list = []
        for msg in mensajes_db:
            mensajes_list.append({
                'id': msg.id,
                'remitente_id': msg.remitente.id,
                'remitente_nombre': f"{msg.remitente.nombre} {msg.remitente.apellido}",
                'mensaje': msg.mensaje,
                'fecha_envio_formateada': msg.fecha_envio.strftime("%d %b, %I:%M %p"), 
                'es_admin_respuesta': (msg.remitente.rol.nombre.lower() in ['soporte', 'administrador']) 
            })
            
        data = {
            'ticket_id': ticket.id,
            'numero_reclamo': ticket.numero_reclamo,
            'usuario_nombre': f"{ticket.usuario.nombre} {ticket.usuario.apellido}",
            'usuario_correo': ticket.usuario.correo,
            'estado_ticket': ticket.estado_soporte.nombre,
            'mensajes': mensajes_list
        }
        return JsonResponse(data)
    return JsonResponse({'error': 'Método no permitido'}, status=405)


def send_message_api(request):
    """Recibe mensaje AJAX, guarda en Supabase y devuelve JSON."""
    if not es_personal_autorizado(request):
        return JsonResponse({'error': 'No autorizado'}, status=403)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ticket_id = data.get('ticket_id')
            mensaje_texto = data.get('mensaje')
            
            if not ticket_id or not mensaje_texto:
                return JsonResponse({'error': 'Datos incompletos'}, status=400)
                
            ticket = get_object_or_404(Soporte, pk=ticket_id)
            admin_usuario = Usuario.objects.get(id=request.session['usuario_id']) 
            
            # Crear el mensaje en Supabase
            nuevo_mensaje = SoporteMensaje.objects.create(
                soporte=ticket,
                remitente=admin_usuario,
                mensaje=mensaje_texto,
                fecha_envio=timezone.now()
            )
            
            # Devolvemos el nuevo mensaje formateado para pintarlo al instante
            return JsonResponse({
                'success': True,
                'id': nuevo_mensaje.id,
                'remitente_nombre': f"{admin_usuario.nombre} {admin_usuario.apellido}",
                'mensaje': nuevo_mensaje.mensaje,
                'fecha_envio_formateada': nuevo_mensaje.fecha_envio.strftime("%d %b, %I:%M %p"),
                'es_admin_respuesta': True 
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)
            
    return JsonResponse({'error': 'Método no permitido'}, status=405)


def close_ticket_api(request):
    """Recibe ID AJAX, cierra ticket en Supabase y devuelve JSON."""
    if not es_personal_autorizado(request):
        return JsonResponse({'error': 'No autorizado'}, status=403)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ticket_id = data.get('ticket_id')
            
            if not ticket_id:
                return JsonResponse({'error': 'ID del ticket faltante'}, status=400)
                
            ticket = get_object_or_404(Soporte, pk=ticket_id)
            
            # Buscamos el objeto EstadoSoporte para "Cerrado"
            try:
                estado_cerrado = EstadoSoporte.objects.get(nombre='Cerrado') 
            except EstadoSoporte.DoesNotExist:
                return JsonResponse({'error': 'Error de configuración: El estado "Cerrado" no existe en la BD.'}, status=500)
            
            # Actualizamos el ticket
            ticket.estado_soporte = estado_cerrado
            ticket.fecha_cierre = timezone.now()
            ticket.save() 
            
            return JsonResponse({'success': True, 'nuevo_estado': estado_cerrado.nombre})
            
        except Exception as e:
            return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)
            
    return JsonResponse({'error': 'Método no permitido'}, status=405)