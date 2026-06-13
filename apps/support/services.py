"""
Motor de asistente virtual para soporte al cliente.
- Prioridad: API de IA (Gemini / Groq / OpenAI) si hay clave en .env
- Respaldo: respuestas contextuales con datos reales de la BD
"""
import json
import logging
import re
import unicodedata
from decimal import Decimal

import requests
from django.conf import settings
from django.db.models import Min
from django.utils import timezone

logger = logging.getLogger(__name__)

TZ_BOLIVIA = 'America/La_Paz'


def _norm(texto: str) -> str:
    if not texto:
        return ''
    t = texto.lower().strip()
    t = unicodedata.normalize('NFKD', t).encode('ASCII', 'ignore').decode('ASCII')
    return re.sub(r'\s+', ' ', t)


def _fmt_bs(valor) -> str:
    if valor is None:
        return '—'
    try:
        return f'Bs. {Decimal(valor):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    except Exception:
        return str(valor)


def obtener_horario_soporte():
    from apps.users.models import ConfiguracionSistema

    config = ConfiguracionSistema.objects.first()
    if config and config.soporte_humano_habilitado:
        return {
            'habilitado': True,
            'inicio': config.soporte_humano_hora_inicio.strftime('%H:%M'),
            'fin': config.soporte_humano_hora_fin.strftime('%H:%M'),
        }
    return {'habilitado': False, 'inicio': '08:00', 'fin': '14:00'}


def es_horario_soporte_humano():
    from zoneinfo import ZoneInfo
    from datetime import time

    try:
        from apps.users.models import ConfiguracionSistema

        config = ConfiguracionSistema.objects.first()
        if not config or not config.soporte_humano_habilitado:
            return False

        ahora = timezone.now().astimezone(ZoneInfo(TZ_BOLIVIA)).time()
        ini, fin = config.soporte_humano_hora_inicio, config.soporte_humano_hora_fin
        if fin < ini:
            return ahora >= ini or ahora < fin
        return ini <= ahora < fin
    except Exception:
        ahora = timezone.now().astimezone(ZoneInfo(TZ_BOLIVIA)).time()
        return time(8, 0) <= ahora < time(14, 0)


def _eventos_proximos_texto(limite=8):
    from apps.events.models import Evento

    hoy = timezone.localdate()
    eventos = (
        Evento.objects.select_related('estado_evento')
        .prefetch_related('eventozona_set__zona')
        .filter(estado_evento__nombre__icontains='activ', fecha_evento__gte=hoy)
        .order_by('fecha_evento', 'hora_evento')[:limite]
    )
    if not eventos:
        return 'No hay eventos activos publicados en este momento.'

    lineas = []
    for ev in eventos:
        zonas = ev.eventozona_set.filter(habilitada=True).order_by('precio_base')
        precio_min = zonas.aggregate(m=Min('precio_base'))['m']
        partes_zona = []
        for ez in zonas:
            partes_zona.append(f"{ez.zona.nombre}: {_fmt_bs(ez.precio_base)}")
        zonas_txt = '; '.join(partes_zona) if partes_zona else 'sin zonas configuradas'
        lineas.append(
            f"- {ev.nombre} | {ev.fecha_evento.strftime('%d/%m/%Y')} {ev.hora_evento.strftime('%H:%M')} "
            f"| {ev.lugar} | desde {_fmt_bs(precio_min)} | zonas: {zonas_txt}"
        )
    return '\n'.join(lineas)


def _contexto_usuario(usuario_id):
    if not usuario_id:
        return 'Usuario no identificado (sin sesión).'

    from apps.users.models import Usuario
    from apps.support.models import Soporte
    from apps.tickets.models import Venta

    try:
        u = Usuario.objects.get(pk=usuario_id)
    except Usuario.DoesNotExist:
        return 'Usuario no encontrado.'

    tickets = Soporte.objects.filter(usuario_id=usuario_id).order_by('-fecha_creacion')[:5]
    ventas = (
        Venta.objects.filter(usuario_id=usuario_id)
        .select_related('reserva__evento', 'estado_venta')
        .order_by('-fecha_venta')[:5]
    )

    partes = [f"Nombre: {u.nombre} {u.apellido}", f"Correo: {u.correo}"]
    if tickets:
        partes.append('Tickets de soporte recientes:')
        for t in tickets:
            estado = 'cerrado' if t.fecha_cierre else 'abierto'
            partes.append(f"  • {t.numero_reclamo} — {t.asunto} ({estado})")
    else:
        partes.append('Sin tickets de soporte previos.')

    if ventas:
        partes.append('Compras recientes:')
        for v in ventas:
            ev = v.reserva.evento if v.reserva_id else None
            ev_nombre = ev.nombre if ev else '—'
            partes.append(f"  • Venta #{v.id} — {ev_nombre} — {_fmt_bs(v.total)} — {v.estado_venta.nombre}")
    else:
        partes.append('Sin compras registradas.')

    return '\n'.join(partes)


def construir_contexto_sistema(usuario_id=None):
    from apps.events.zonas_catalogo import ZONAS_TEATRO
    from apps.payments.models import MetodoPago

    horario = obtener_horario_soporte()
    humano_ahora = es_horario_soporte_humano()
    metodos = list(MetodoPago.objects.values_list('nombre', flat=True)[:12])

    zonas_txt = '\n'.join(
        f"- {z['nombre']} (código {z['tipo_zona']}): capacidad {z['capacidad_base']}, color {z['codigo_color']}"
        for z in ZONAS_TEATRO
    )

    maps_url = getattr(settings, 'TEATRO_MAPS_URL', 'https://maps.app.goo.gl/L2vCegKyoDNpwncJ8')
    ubicacion = getattr(settings, 'TEATRO_UBICACION_TEXTO', 'Avenida del Poeta, La Paz, Bolivia')

    return f"""DATOS EN TIEMPO REAL DEL SISTEMA (usa solo esta información, no inventes):

TEATRO: Teatro Al Aire Libre "Jaime Laredo", La Paz, Bolivia.
Ubicación: {ubicacion}
Google Maps: {maps_url}

ZONAS DEL TEATRO (asientos numerados):
{zonas_txt}

EVENTOS PRÓXIMOS ACTIVOS:
{_eventos_proximos_texto()}

MÉTODOS DE PAGO REGISTRADOS: {', '.join(metodos) if metodos else 'Tarjeta, QR Bancario, Transferencia'}

PROCESO DE COMPRA:
1. Ir a Eventos en el menú
2. Elegir evento → Comprar entrada
3. Seleccionar zona (SUPER VIP, VIP, PLATEA o GENERAL)
4. Elegir asientos en el mapa interactivo (si la zona tiene numeración)
5. Finalizar compra y pagar
6. Ver entradas en "Mis tickets"

SOPORTE HUMANO:
- Horario configurado: {horario['inicio']} a {horario['fin']} (hora Bolivia)
- Estado ahora: {'DISPONIBLE' if humano_ahora else 'FUERA DE HORARIO'}
- Para casos complejos (reembolsos, reclamos): crear ticket en Soporte Humano dentro del horario

ASISTENTE IA: disponible 24/7.

REEMBOLSOS: solo si el evento fue cancelado por el teatro; plazo ~15 días hábiles al mismo método de pago.

CUENTA: registro con nombre, apellido, correo, celular boliviano (8 dígitos, empieza 6 o 7), contraseña segura.

DATOS DEL USUARIO ACTUAL:
{_contexto_usuario(usuario_id)}
"""


def _system_prompt(contexto: str) -> str:
    return f"""Eres el asistente virtual oficial del Teatro Al Aire Libre "Jaime Laredo" en La Paz, Bolivia.
Responde SIEMPRE en español, de forma clara, amable y profesional.
Usa emojis con moderación (máximo 1-2 por respuesta).

REGLAS ESTRICTAS:
1. Basa tus respuestas en el CONTEXTO del sistema abajo. No inventes eventos, precios, fechas ni políticas.
2. Si no tienes datos suficientes, dilo honestamente y sugiere crear un ticket de soporte humano en horario {obtener_horario_soporte()['inicio']}-{obtener_horario_soporte()['fin']}.
3. Respuestas concisas pero completas (máximo ~200 palabras salvo listados de eventos).
4. Para pasos de compra, usa listas numeradas.
5. No des consejos legales ni médicos. Solo temas del teatro, entradas, pagos y soporte web.
6. Si preguntan algo fuera del teatro, redirige amablemente al ámbito del servicio.

{contexto}
"""


def _historial_a_mensajes(historial):
    msgs = []
    if not historial:
        return msgs
    for item in historial[-10:]:
        rol = item.get('role') or item.get('rol')
        texto = (item.get('content') or item.get('mensaje') or '').strip()
        if not texto:
            continue
        if rol in ('user', 'usuario'):
            msgs.append({'role': 'user', 'content': texto})
        elif rol in ('assistant', 'ia', 'model'):
            msgs.append({'role': 'assistant', 'content': texto})
    return msgs


def _call_gemini(system_prompt, messages, api_key, model):
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
    contents = []
    for msg in messages:
        role = 'user' if msg['role'] == 'user' else 'model'
        contents.append({'role': role, 'parts': [{'text': msg['content']}]})

    payload = {
        'systemInstruction': {'parts': [{'text': system_prompt}]},
        'contents': contents,
        'generationConfig': {
            'temperature': 0.35,
            'maxOutputTokens': 1200,
            'topP': 0.9,
        },
    }
    r = requests.post(url, params={'key': api_key}, json=payload, timeout=45)
    r.raise_for_status()
    data = r.json()
    candidates = data.get('candidates') or []
    if not candidates:
        raise ValueError('Gemini sin candidatos')
    parts = candidates[0].get('content', {}).get('parts') or []
    text = ''.join(p.get('text', '') for p in parts).strip()
    if not text:
        raise ValueError('Gemini respuesta vacía')
    return text


def _call_openai_compatible(system_prompt, messages, api_key, base_url, model):
    url = base_url.rstrip('/') + '/chat/completions'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    chat_messages = [{'role': 'system', 'content': system_prompt}] + [
        {'role': 'user' if m['role'] == 'user' else 'assistant', 'content': m['content']}
        for m in messages
    ]
    payload = {
        'model': model,
        'messages': chat_messages,
        'temperature': 0.35,
        'max_tokens': 1200,
    }
    r = requests.post(url, headers=headers, json=payload, timeout=45)
    r.raise_for_status()
    data = r.json()
    return data['choices'][0]['message']['content'].strip()


def _llm_respuesta(mensaje_usuario, historial, usuario_id):
    provider = getattr(settings, 'SUPPORT_AI_PROVIDER', 'auto').lower()
    gemini_key = getattr(settings, 'GEMINI_API_KEY', '') or ''
    groq_key = getattr(settings, 'GROQ_API_KEY', '') or ''
    openai_key = getattr(settings, 'OPENAI_API_KEY', '') or ''

    contexto = construir_contexto_sistema(usuario_id)
    system_prompt = _system_prompt(contexto)
    messages = _historial_a_mensajes(historial)
    messages.append({'role': 'user', 'content': mensaje_usuario})

    intentos = []
    if provider in ('auto', 'gemini') and gemini_key:
        model = getattr(settings, 'GEMINI_MODEL', 'gemini-2.0-flash')
        intentos.append(('gemini', lambda: _call_gemini(system_prompt, messages, gemini_key, model)))
    if provider in ('auto', 'groq') and groq_key:
        model = getattr(settings, 'GROQ_MODEL', 'llama-3.3-70b-versatile')
        base = getattr(settings, 'GROQ_API_BASE', 'https://api.groq.com/openai/v1')
        intentos.append(('groq', lambda: _call_openai_compatible(system_prompt, messages, groq_key, base, model)))
    if provider in ('auto', 'openai') and openai_key:
        model = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')
        base = getattr(settings, 'OPENAI_API_BASE', 'https://api.openai.com/v1')
        intentos.append(('openai', lambda: _call_openai_compatible(system_prompt, messages, openai_key, base, model)))

    if provider == 'gemini' and not gemini_key:
        return None
    if provider == 'groq' and not groq_key:
        return None
    if provider == 'none':
        return None

    for nombre, fn in intentos:
        try:
            texto = fn()
            logger.info('Soporte IA: respuesta vía %s', nombre)
            return texto
        except Exception as exc:
            logger.warning('Soporte IA %s falló: %s', nombre, exc)

    return None


def _contiene_alguno(texto, palabras):
    return any(p in texto for p in palabras)


def _respuesta_fallback(mensaje_usuario, historial, usuario_id):
    """Motor local con datos reales cuando no hay API de IA."""
    msg = _norm(mensaje_usuario)
    horario = obtener_horario_soporte()
    humano = es_horario_soporte_humano()

    if _contiene_alguno(msg, ['hola', 'buenos', 'buenas', 'saludos', 'hey', 'hi']):
        return (
            '¡Hola! 👋 Soy el asistente del Teatro Al Aire Libre. '
            'Puedo ayudarte con eventos, precios, compra de entradas, métodos de pago, '
            f'ubicación y soporte técnico.\n\n'
            f'Soporte humano: {"disponible ahora" if humano else "fuera de horario"} '
            f'({horario["inicio"]}–{horario["fin"]}, hora Bolivia).'
        )

    if _contiene_alguno(msg, ['gracias', 'agradezco', 'perfecto', 'genial', 'excelente']):
        return '¡Con gusto! 😊 Si necesitas algo más sobre eventos o entradas, escríbeme.'

    if _contiene_alguno(msg, ['evento', 'funcion', 'concierto', 'obra', 'calendario', 'programacion', 'cartelera']):
        return f'📅 **Eventos próximos:**\n\n{_eventos_proximos_texto()}\n\nPuedes comprar desde el menú **Eventos**.'

    if _contiene_alguno(msg, ['precio', 'cuesta', 'costo', 'valor', 'cuanto', 'tarifa']):
        return (
            '🎟️ **Zonas del teatro:** SUPER VIP, VIP, PLATEA y GENERAL. '
            'Los precios dependen de cada evento:\n\n'
            f'{_eventos_proximos_texto()}\n\n'
            'Al entrar a un evento verás el precio exacto por zona antes de pagar.'
        )

    if _contiene_alguno(msg, ['comprar', 'entrada', 'ticket', 'boleto', 'asiento', 'reservar']):
        return (
            '**Cómo comprar entradas:**\n'
            '1. Menú **Eventos** → elige tu función\n'
            '2. **Comprar entrada** → selecciona zona (SUPER VIP, VIP, PLATEA o GENERAL)\n'
            '3. Elige asientos en el mapa interactivo\n'
            '4. Finaliza el pago\n'
            '5. Revisa **Mis tickets** para ver tus entradas\n\n'
            '¿En qué paso necesitas ayuda?'
        )

    if _contiene_alguno(msg, ['pago', 'pagar', 'tarjeta', 'qr', 'transferencia', 'paypal']):
        from apps.payments.models import MetodoPago
        metodos = list(MetodoPago.objects.values_list('nombre', flat=True))
        lista = '\n'.join(f'• {m}' for m in metodos) if metodos else '• Tarjeta • QR Bancario • Transferencia'
        return f'💳 **Métodos de pago disponibles:**\n{lista}\n\nElige uno al finalizar la compra en el checkout.'

    if _contiene_alguno(msg, ['horario', 'hora', 'cuando', 'disponible', 'atencion', 'humano', 'agente', 'persona']):
        estado = '✅ **Disponible ahora**' if humano else '⏳ **Fuera de horario**'
        return (
            f'👥 **Soporte humano:** {estado}\n'
            f'Horario: **{horario["inicio"]} a {horario["fin"]}** (hora Bolivia, La Paz)\n\n'
            '🤖 **Asistente IA:** disponible 24/7.\n\n'
            'Para un ticket humano: Soporte → Soporte Humano → crear ticket.'
        )

    if _contiene_alguno(msg, ['ubicacion', 'direccion', 'donde', 'mapa', 'llegar', 'teatro']):
        maps = getattr(settings, 'TEATRO_MAPS_URL', 'https://maps.app.goo.gl/L2vCegKyoDNpwncJ8')
        ubi = getattr(settings, 'TEATRO_UBICACION_TEXTO', 'Avenida del Poeta, La Paz, Bolivia')
        return (
            f'📍 **Ubicación:** {ubi}\n'
            f'Teatro Al Aire Libre "Jaime Laredo", La Paz.\n\n'
            f'[Ver en Google Maps]({maps})\n\n'
            'Recomendación: llegar 30 minutos antes del evento.'
        )

    if _contiene_alguno(msg, ['reembolso', 'devolucion', 'devolver', 'dinero', 'cancel']):
        return (
            '💰 **Reembolsos:** se procesan si el **teatro cancela** el evento. '
            'Plazo aproximado: 15 días hábiles al mismo método de pago.\n\n'
            'Para solicitarlo: Soporte Humano → ticket con asunto "Reembolso", '
            'número de compra, evento y monto.'
        )

    if _contiene_alguno(msg, ['cuenta', 'registro', 'login', 'sesion', 'contraseña', 'password', 'olvide']):
        return (
            '📝 **Cuenta:** regístrate desde **Registrarse** (nombre, apellido, correo, '
            'celular 8 dígitos empezando en 6 o 7, contraseña segura).\n\n'
            '¿Olvidaste la contraseña? Usa **Recuperar contraseña** en el login.'
        )

    if _contiene_alguno(msg, ['ticket', 'reclamo', 'soporte', 'problema', 'error', 'no funciona', 'falla']):
        ctx_user = _contexto_usuario(usuario_id)
        return (
            f'🔧 **Tu historial:**\n{ctx_user}\n\n'
            f'Soporte humano: {"disponible" if humano else "fuera de horario"} '
            f'({horario["inicio"]}–{horario["fin"]}).\n'
            'Describe el error (pantalla, paso, mensaje) y te oriento.'
        )

    if _contiene_alguno(msg, ['zona', 'vip', 'platea', 'general', 'svip', 'asiento']):
        from apps.events.zonas_catalogo import ZONAS_TEATRO
        lineas = [
            f"• **{z['nombre']}** — {z['capacidad_base']} cupos — color {z['codigo_color']}"
            for z in ZONAS_TEATRO
        ]
        return (
            '🎭 **Zonas del teatro:**\n' + '\n'.join(lineas) + '\n\n'
            'Precios por evento en la ficha de cada función.'
        )

    # Contexto de conversación reciente
    if historial:
        ultimo_user = ''
        for h in reversed(historial):
            if h.get('role') in ('user', 'usuario'):
                ultimo_user = _norm(h.get('content') or h.get('mensaje') or '')
                break
        if ultimo_user and _contiene_alguno(ultimo_user, ['comprar', 'entrada', 'evento']):
            return _respuesta_fallback(ultimo_user, [], usuario_id)

    return (
        'No tengo certeza sobre eso con la información actual. Puedo ayudarte con:\n'
        '• Eventos y precios\n• Compra de entradas\n• Métodos de pago\n'
        '• Ubicación del teatro\n• Horario de soporte humano\n• Problemas con tu cuenta o compra\n\n'
        f'Soporte humano: {horario["inicio"]}–{horario["fin"]} (Bolivia). '
        'Reformula tu pregunta con más detalle o crea un ticket en Soporte Humano.'
    )


def generar_respuesta_ia(mensaje_usuario, historial_conversacion=None, usuario_id=None):
    mensaje = (mensaje_usuario or '').strip()
    if not mensaje:
        return 'Por favor escribe tu pregunta.'

    historial = historial_conversacion or []

    llm = _llm_respuesta(mensaje, historial, usuario_id)
    if llm:
        return llm

    return _respuesta_fallback(mensaje, historial, usuario_id)


def info_estado_ia():
    """Indica si hay proveedor de IA configurado (para la UI)."""
    provider = getattr(settings, 'SUPPORT_AI_PROVIDER', 'auto')
    tiene = bool(
        getattr(settings, 'GEMINI_API_KEY', '')
        or getattr(settings, 'GROQ_API_KEY', '')
        or getattr(settings, 'OPENAI_API_KEY', '')
    )
    if provider == 'none':
        tiene = False
    return {
        'ia_avanzada': tiene,
        'provider': provider,
    }
