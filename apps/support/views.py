import json
import random
from zoneinfo import ZoneInfo
from datetime import time
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .models import Soporte, SoporteMensaje, EstadoSoporte, CategoriaSoporte
from apps.users.models import Usuario, ConfiguracionSistema

def es_personal_autorizado(request):
    if 'usuario_id' not in request.session:
        return False
    rol = request.session.get('usuario_rol', '').lower()
    return rol in ['soporte', 'administrador', 'admin']


def es_horario_soporte_humano():
    """Verifica si está dentro del horario de soporte humano según configuración"""
    try:
        config = ConfiguracionSistema.objects.first()
        if not config or not config.soporte_humano_habilitado:
            return False

        tz_bolivia = ZoneInfo('America/La_Paz')
        ahora = timezone.now().astimezone(tz_bolivia)
        hora_actual = ahora.time()

        hora_inicio = config.soporte_humano_hora_inicio
        hora_fin = config.soporte_humano_hora_fin

        # Si la hora de fin es menor que la hora de inicio, significa que cruza la medianoche
        if hora_fin < hora_inicio:
            # Ejemplo: 20:00 a 02:00 (del siguiente día)
            return hora_actual >= hora_inicio or hora_actual < hora_fin
        else:
            # Horario normal del mismo día
            return hora_inicio <= hora_actual < hora_fin
    except Exception:
        # Si hay error, usar valores por defecto (8:00 - 14:00)
        tz_bolivia = ZoneInfo('America/La_Paz')
        ahora = timezone.now().astimezone(tz_bolivia)
        hora_actual = ahora.time()
        return time(8, 0) <= hora_actual < time(14, 0)


def generar_respuesta_ia(mensaje_usuario):
    """Genera una respuesta automática de la IA basada en preguntas comunes sobre el sistema"""
    mensaje_lower = mensaje_usuario.lower()
    
    # Base de conocimiento del sistema
    respuestas = {
        'horario': {
            'palabras_clave': ['horario', 'hora', 'cuando', 'abierto', 'funciona', 'atencion'],
            'respuesta': 'El teatro está abierto de martes a domingo de 18:00 a 23:00. La taquilla abre 2 horas antes de cada función. Para soporte humano, estamos disponibles de 8:00 a 14:00.'
        },
        'entradas': {
            'palabras_clave': ['entrada', 'ticket', 'boleto', 'comprar', 'reservar', 'precio'],
            'respuesta': 'Puedes comprar entradas directamente desde nuestra página web. Los precios varían según la zona: SUPER VIP, VIP, PLATEA y GENERAL. También puedes reservar entradas y pagarlas después.'
        },
        'zonas': {
            'palabras_clave': ['zona', 'ubicacion', 'asiento', 'lugar', 'super vip', 'vip', 'platea', 'general'],
            'respuesta': 'Contamos con 4 zonas: SUPER VIP (mejor ubicación), VIP, PLATEA y GENERAL. Cada zona tiene su propio precio y capacidad. Puedes ver el mapa del teatro al seleccionar tus asientos.'
        },
        'pago': {
            'palabras_clave': ['pago', 'tarjeta', 'metodo', 'dinero', 'transferencia', 'qr'],
            'respuesta': 'Aceptamos pagos con tarjeta de crédito/débito, transferencia bancaria y QR. Los pagos se procesan de forma segura a través de nuestra plataforma.'
        },
        'reembolso': {
            'palabras_clave': ['reembolso', 'devolucion', 'cancelar', 'devolver', 'dinero'],
            'respuesta': 'Los reembolsos solo se realizan si el evento es cancelado por el teatro. En caso de cancelación, el reembolso se procesa en un plazo máximo de 15 días hábiles.'
        },
        'cuenta': {
            'palabras_clave': ['cuenta', 'registro', 'perfil', 'contraseña', 'sesion', 'login'],
            'respuesta': 'Para crear una cuenta, haz clic en "Registrarse" en la página principal. Necesitarás proporcionar tu nombre, correo, teléfono y una contraseña segura. Puedes recuperar tu contraseña si la olvidas.'
        },
        'evento': {
            'palabras_clave': ['evento', 'funcion', 'show', 'concierto', 'obra', 'calendario'],
            'respuesta': 'Puedes ver todos los eventos programados en la sección "Eventos" de nuestra página. Cada evento muestra la fecha, hora, precios y disponibilidad de asientos.'
        },
        'contacto': {
            'palabras_clave': ['contacto', 'telefono', 'correo', 'email', 'ubicacion', 'direccion'],
            'respuesta': 'Puedes contactarnos a través de este chat de soporte, por correo a info@teatrolapaz.bo o llamando al +591 2 123-4567. Estamos ubicados en el Teatro al Aire Libre "Jaime Laredo".'
        },
        'parking': {
            'palabras_clave': ['parking', 'estacionamiento', 'auto', 'coche'],
            'respuesta': 'Contamos con estacionamiento gratuito para los asistentes. Recomendamos llegar con 30 minutos de anticipación para asegurar lugar.'
        },
        'accesibilidad': {
            'palabras_clave': ['accesibilidad', 'discapacidad', 'silla', 'ruedas', 'acceso'],
            'respuesta': 'El teatro cuenta con accesibilidad para personas con discapacidad. Contamos con rampas, espacios reservados y asistentes capacitados para ayudar. Por favor contáctanos antes para coordinar.'
        }
    }
    
    # Buscar respuesta basada en palabras clave
    mejor_respuesta = None
    mejor_coincidencia = 0
    
    for categoria, data in respuestas.items():
        coincidencias = sum(1 for palabra in data['palabras_clave'] if palabra in mensaje_lower)
        if coincidencias > mejor_coincidencia:
            mejor_coincidencia = coincidencias
            mejor_respuesta = data['respuesta']
    
    if mejor_respuesta:
        return mejor_respuesta
    
    # Respuesta por defecto si no hay coincidencia
    respuestas_default = [
        "Entiendo tu consulta. Para ayudarte mejor, ¿podrías proporcionar más detalles sobre tu problema?",
        "Lamento no tener una respuesta específica para eso. ¿Te gustaría hablar con un agente de soporte humano?",
        "Estoy aquí para ayudarte con preguntas sobre el teatro, eventos, entradas y pagos. ¿Podrías reformular tu pregunta?",
        "Si necesitas ayuda más específica, te recomiendo crear un ticket de soporte para que un humano te asista."
    ]
    
    return random.choice(respuestas_default)


@require_POST
def soporte_ia_api(request):
    """Endpoint para la IA de soporte"""
    if 'usuario_id' not in request.session:
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    try:
        data = json.loads(request.body)
        mensaje_usuario = data.get('mensaje', '').strip()
        
        if not mensaje_usuario:
            return JsonResponse({'error': 'Mensaje vacío'}, status=400)
        
        # Generar respuesta de la IA
        respuesta_ia = generar_respuesta_ia(mensaje_usuario)
        
        tz_bolivia = ZoneInfo('America/La_Paz')
        hora_actual = timezone.now().astimezone(tz_bolivia)
        
        return JsonResponse({
            'success': True,
            'respuesta': respuesta_ia,
            'fecha_envio_formateada': hora_actual.strftime("%I:%M %p"),
            'es_ia': True
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@never_cache
def support_dashboard(request):
    if not es_personal_autorizado(request):
        messages.error(request, "Acceso denegado. Área exclusiva para personal.")
        return redirect('/?action=login')

    todos_los_tickets = Soporte.objects.select_related('usuario', 'estado_soporte', 'categoria_soporte').order_by('-fecha_creacion')
    
    total_tickets = todos_los_tickets.count()
    tickets_no_leidos = todos_los_tickets.filter(fecha_cierre__isnull=True).count()
    tickets_leidos = todos_los_tickets.filter(fecha_cierre__isnull=False).count()

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
            
            estado_cerrado, _ = EstadoSoporte.objects.get_or_create(nombre='cerrado') 
            ticket.estado_soporte = estado_cerrado
            ticket.fecha_cierre = timezone.now()
            ticket.save() 
            return JsonResponse({'success': True, 'nuevo_estado': estado_cerrado.nombre})
        except Exception as e: return JsonResponse({'error': f'Error: {str(e)}'}, status=500)
    return JsonResponse({'error': 'Método no permitido'}, status=405)

def tickets_list_api(request):
    if not es_personal_autorizado(request): return JsonResponse({'error': 'No autorizado'}, status=403)
    
    tickets_db = Soporte.objects.select_related('usuario').order_by('-fecha_creacion')
    
    tz_bolivia = ZoneInfo('America/La_Paz')
    tickets_list = []
    for t in tickets_db:
        hora_local = t.fecha_creacion.astimezone(tz_bolivia)
        tickets_list.append({
            'id': t.id,
            'inicial': t.usuario.nombre[0].upper() if t.usuario.nombre else 'U',
            'nombre': f"{t.usuario.nombre} {t.usuario.apellido}",
            'correo': t.usuario.correo,
            'asunto': t.asunto,
            'fecha_formateada': hora_local.strftime("%d %b %Y, %I:%M %p"),
            'is_closed': t.fecha_cierre is not None
        })
        
    return JsonResponse({'tickets': tickets_list})

@never_cache
def cliente_soporte_view(request, ticket_id=None, modo='ia'):
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
                messages.error(request, "Ocurrió un error al crear el ticket. Inténtalo de nuevo.")

    categorias = CategoriaSoporte.objects.all()
    horario_humano = es_horario_soporte_humano()

    return render(request, 'pages/users/cliente_soporte.html', {
        'mis_tickets': mis_tickets,
        'ticket_seleccionado': ticket_seleccionado,
        'categorias': categorias,
        'horario_humano': horario_humano,
        'modo_actual': modo
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