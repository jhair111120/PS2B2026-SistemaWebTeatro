from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode

from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.dateparse import parse_date, parse_time
from django.core.exceptions import ValidationError
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from .models import Evento, EstadoEvento, EventoZona, Zona


def _require_admin(request):
    if not request.session.get('usuario_id'):
        return redirect('login')
    if (request.session.get('usuario_rol') or '').strip().lower() != 'administrador':
        messages.error(request, 'No tienes permisos para acceder a esa sección.')
        return redirect('inicio')
    return None


def _parse_money(raw):
    if raw is None:
        return None
    s = str(raw).strip()
    if s == '':
        return None
    try:
        return Decimal(s.replace(',', '.'))
    except (InvalidOperation, ValueError):
        return None


def _zona_primera_patrones(*keywords):
    for kw in keywords:
        z = Zona.objects.filter(nombre__icontains=kw.strip()).exclude(nombre='').first()
        if z:
            return z
    return None


def _resolver_estados():
    qs = EstadoEvento.objects.all()
    if not qs.exists():
        return None, None

    estado_activo = (
        qs.filter(nombre__icontains='activ')
        .exclude(nombre__icontains='inactiv')
        .order_by('id')
        .first()
        or qs.filter(nombre__icontains='activ').exclude(nombre__icontains='suspend').first()
        or qs.order_by('id').first()
    )

    estado_inactivo = (
        qs.filter(nombre__icontains='inactiv').order_by('id').first()
        or qs.filter(nombre__icontains='cerrad').order_by('id').first()
        or qs.filter(nombre__icontains='borrador').order_by('id').first()
        or estado_activo
    )

    return estado_activo, estado_inactivo


def _split_cap(total, n):
    if total is None or total <= 0 or n <= 0:
        return [None] * n
    base = total // n
    rem = total % n
    return [base + (1 if i < rem else 0) for i in range(n)]


def _payload_errors(request):
    errs = []

    estado_activo_obj, estado_inactivo_obj = _resolver_estados()
    if not estado_activo_obj:
        errs.append(
            'No hay estados de evento en la base. Carga al menos un registro en la tabla de estados (por ejemplo «activo»).'
        )
        return errs, None

    nombre = (request.POST.get('nombre') or '').strip()
    fecha_raw = request.POST.get('fecha_evento')
    hora_raw = request.POST.get('hora_evento')
    lugar = (request.POST.get('lugar') or '').strip() or 'Teatro al Aire Libre'
    capacidad_total_raw = request.POST.get('capacidad_total')

    precio_specs = []
    vip = _zona_primera_patrones('VIP', 'Preferencial')
    graderia = _zona_primera_patrones('Gradería', 'Graderia', 'Preferente')
    general = _zona_primera_patrones('General', 'Fosa', 'Popular')

    for field, zona_obj, label in (
        ('precio_vip', vip, 'VIP'),
        ('precio_graderia', graderia, 'Gradería'),
        ('precio_general', general, 'General'),
    ):
        p = _parse_money(request.POST.get(field))
        if p is None:
            continue
        if p < 0:
            errs.append(f'Precio «{label}» no válido.')
            continue
        if not zona_obj:
            errs.append(
                f'Hay precio para «{label}» pero no existe una zona con ese tipo en catálogo. Mira la pestaña Zonas.'
            )
            continue
        precio_specs.append((zona_obj, p, label))

    if len(nombre) < 3:
        errs.append('El nombre debe tener al menos 3 caracteres.')

    fecha = parse_date((fecha_raw or '').strip())
    hora = parse_time((hora_raw or '').strip())
    if not fecha:
        errs.append('Fecha inválida.')
    if not hora:
        errs.append('Hora inválida.')

    capacidad_total = None
    if capacidad_total_raw not in (None, ''):
        try:
            capacidad_total = int(str(capacidad_total_raw).strip())
            if capacidad_total < 0:
                errs.append('La capacidad total no puede ser negativa.')
                capacidad_total = None
        except ValueError:
            errs.append('Capacidad total inválida.')
            capacidad_total = None

    if not precio_specs:
        errs.append(
            'Indica al menos un precio válido y que existan las zonas correspondientes en el catálogo (VIP, Gradería y/o General).'
        )

    activo = request.POST.get('evento_activo') == 'on'
    estado_pick = estado_activo_obj if activo else (estado_inactivo_obj or estado_activo_obj)

    if errs:
        return errs, None

    data = {
        'nombre': nombre,
        'descripcion': (request.POST.get('descripcion') or '').strip() or None,
        'fecha_evento': fecha,
        'hora_evento': hora,
        'lugar': lugar,
        'imagen_url': (request.POST.get('imagen_url') or '').strip() or None,
        'estado_evento': estado_pick,
        'precio_specs': precio_specs,
        'capacidad_total': capacidad_total if capacidad_total is not None else 0,
    }
    return None, data


@never_cache
@require_http_methods(['GET', 'POST'])
def admin_evento_create(request):
    gate = _require_admin(request)
    if gate:
        return gate

    redirect_ok = lambda: redirect(reverse('admin_panel') + '?' + urlencode({'tab': 'eventos'}))

    if request.method == 'GET':
        return redirect_ok()

    errs, payload = _payload_errors(request)
    if errs:
        for m in errs:
            messages.error(request, m)
        return redirect_ok()

    caps = _split_cap(payload['capacidad_total'], len(payload['precio_specs']))
    try:
        with transaction.atomic():
            ev = Evento(
                nombre=payload['nombre'],
                descripcion=payload['descripcion'],
                fecha_evento=payload['fecha_evento'],
                hora_evento=payload['hora_evento'],
                lugar=payload['lugar'],
                imagen_url=payload['imagen_url'] or None,
                estado_evento=payload['estado_evento'],
            )
            ev.full_clean()
            ev.save()

            for i, spec in enumerate(payload['precio_specs']):
                zona_obj, precio, _lbl = spec
                cap_zone = caps[i]
                ez = EventoZona(
                    evento=ev,
                    zona=zona_obj,
                    precio_base=precio,
                    capacidad_evento=cap_zone,
                    nombre_display=zona_obj.nombre,
                    limite_por_usuario=4,
                    habilitada=True,
                )
                ez.full_clean()
                ez.save()

        messages.success(request, 'Evento creado correctamente.')
    except ValidationError as e:
        if getattr(e, 'error_dict', None):
            for msg_list in e.error_dict.values():
                for msg in msg_list:
                    messages.error(request, str(msg))
        elif getattr(e, 'messages', None):
            for msg in e.messages:
                messages.error(request, str(msg))
        else:
            messages.error(request, str(e))
    except Exception:
        messages.error(request, 'No se pudo guardar. Comprueba la base de datos o datos duplicados.')

    return redirect_ok()
