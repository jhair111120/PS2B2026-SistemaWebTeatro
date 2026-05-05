import calendar
import re
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from .models import Usuario, Rol
from apps.events.models import Evento, EventoAsiento, EventoZona, Zona
from apps.reservations.models import Reserva
from apps.tickets.models import Venta


# =========================
# 🔐 REGISTRO
# =========================
@never_cache
def signup_view(request):
    if request.session.get('usuario_id'):
        return redirect('/')

    if request.method == 'POST':
        nombre    = request.POST.get('nombre', '').strip()
        apellido  = request.POST.get('apellido', '').strip()
        correo    = request.POST.get('correo', '').strip().lower()
        password  = request.POST.get('password', '')
        telefono  = request.POST.get('telefono', '').strip() or None

        if len(nombre) < 2 or len(apellido) < 2:
            messages.error(request, "Nombre y apellido deben tener al menos 2 caracteres.")
            return redirect(f"{reverse('login')}?tab=signup")

        if Usuario.objects.filter(correo=correo).exists():
            messages.error(request, "Este correo ya está registrado.")
            return redirect(f"{reverse('login')}?tab=signup")

        if telefono and Usuario.objects.filter(telefono=telefono).exists():
            messages.error(request, "Este teléfono ya está en uso.")
            return redirect(f"{reverse('login')}?tab=signup")

        rol_cliente, _ = Rol.objects.get_or_create(nombre='cliente')

        try:
            with transaction.atomic():
                usuario = Usuario(
                    nombre=nombre,
                    apellido=apellido,
                    correo=correo,
                    telefono=telefono,
                    rol=rol_cliente,
                    activo=True
                )
                usuario.set_password(password)
                usuario.full_clean()
                usuario.save()

            messages.success(request, "Cuenta creada correctamente.")
            return redirect('login')

        except ValidationError as e:
            messages.error(request, e.messages[0])
        except Exception:
            messages.error(request, "Error inesperado.")

        return redirect('signup')

    return redirect('/')


# =========================
# 🔑 LOGIN
# =========================
@never_cache
def login_view(request):
    if request.session.get('usuario_id'):
        return redirect('/')

    if request.method == 'POST':
        correo   = request.POST.get('correo', '').strip().lower()
        password = request.POST.get('password', '')

        try:
            usuario = Usuario.objects.select_related('rol').get(correo=correo)

            if not usuario.is_active:
                messages.error(request, "Cuenta desactivada.")
                return redirect('login')

            if usuario.check_password(password):
                request.session.flush()

                request.session['usuario_id'] = usuario.id
                request.session['usuario_nombre'] = usuario.nombre
                request.session['usuario_correo'] = usuario.correo
                request.session['usuario_rol'] = usuario.rol.nombre

                request.session.set_expiry(60 * 60 * 4)

                # 🔥 REDIRECCIÓN POR ROL
                rol = (usuario.rol.nombre or '').strip().lower()
                if rol == 'administrador':
                    return redirect('admin_panel')
                else:
                    return redirect('inicio')

            else:
                messages.error(request, "Credenciales incorrectas.")

        except Usuario.DoesNotExist:
            messages.error(request, "Credenciales incorrectas.")

        return redirect('login')

    return redirect('/')


# =========================
# 🚪 LOGOUT
# =========================
def logout_view(request):
    request.session.flush()
    return redirect('/')


# =========================
# 👤 PERFIL
# =========================
def perfil_view(request):
    usuario_id = request.session.get('usuario_id')

    if not usuario_id:
        return redirect('/')

    usuario = Usuario.objects.get(id=usuario_id)

    return render(request, 'pages/users/perfil.html', {
        'usuario': usuario
    })


# =========================
# 🛠️ PANEL ADMIN
# =========================
def _seat_stats_dict(event_ids):
    if not event_ids:
        return {}
    rows = (
        EventoAsiento.objects.filter(evento_zona__evento_id__in=event_ids)
        .values('evento_zona__evento_id')
        .annotate(
            total_seats=Count('id'),
            ocup_seats=Count('id', filter=~Q(estado='DISPONIBLE')),
        )
    )
    out = {}
    for row in rows:
        eid = row['evento_zona__evento_id']
        total = row['total_seats'] or 0
        ocup = row['ocup_seats'] or 0
        out[eid] = {
            'total_seats': total,
            'ocup': ocup,
            'pct': round(100 * ocup / total) if total else 0,
        }
    return out


def _cap_publicada_dict(event_ids):
    if not event_ids:
        return {}
    rows = (
        EventoZona.objects.filter(evento_id__in=event_ids)
        .values('evento_id')
        .annotate(c=Sum('capacidad_evento'))
    )
    return {
        row['evento_id']: int(row['c'] or 0)
        for row in rows
    }


def _ventas_emitidas_qs():
    return Venta.objects.filter(estado_venta__nombre__icontains='emitida')


@never_cache
def admin_panel(request):
    if not request.session.get('usuario_id'):
        return redirect('login')

    rol = (request.session.get('usuario_rol') or '').strip().lower()

    if rol != 'administrador':
        return redirect('inicio')

    hoy = timezone.localdate()
    now = timezone.now()
    tz = timezone.get_current_timezone()

    eventos = (
        Evento.objects.select_related('estado_evento')
        .prefetch_related('eventozona_set__zona')
        .order_by('-fecha_evento', '-hora_evento')
    )

    lista_event_ids = list(eventos.values_list('id', flat=True))
    proximos_queryset = (
        Evento.objects.select_related('estado_evento')
        .filter(fecha_evento__gte=hoy)
        .order_by('fecha_evento', 'hora_evento')[:12]
    )
    proximos_list = list(proximos_queryset)
    proximos_ids = [e.id for e in proximos_list]

    all_ids_needed = sorted(set(lista_event_ids + proximos_ids))
    seat_stats = _seat_stats_dict(all_ids_needed)
    cap_pub = _cap_publicada_dict(all_ids_needed)

    def cap_mostrar(ev_id):
        c = cap_pub.get(ev_id, 0)
        tinfo = seat_stats.get(ev_id) or {'total_seats': 0, 'ocup': 0, 'pct': 0}
        return c if c > 0 else tinfo['total_seats']

    ventas_emit = _ventas_emitidas_qs()

    agg_ventas = ventas_emit.aggregate(s=Sum('total'))
    kpi_total_ventas = agg_ventas['s'] or Decimal('0')

    kpi_reservas_activas = Reserva.objects.filter(
        estado_reserva__nombre__icontains='activa'
    ).count()

    asientos_prog = EventoAsiento.objects.filter(evento_zona__evento__fecha_evento__gte=hoy)
    tot_asientos = asientos_prog.count()
    ocup_asientos = asientos_prog.exclude(estado='DISPONIBLE').count()
    kpi_ocupacion_pct = round(100 * ocup_asientos / tot_asientos) if tot_asientos else 0

    kpi_eventos_activos = Evento.objects.filter(
        estado_evento__nombre__icontains='activ'
    ).filter(fecha_evento__gte=hoy).count()

    # Gráficos: ventas últimos 7 días por día civil local
    inicio_week = timezone.localtime(now, tz).date()
    dias = [(inicio_week - timedelta(days=6)) + timedelta(days=i) for i in range(7)]
    etiquetas_sem = []
    valores_sem = []
    day_sum = defaultdict(lambda: Decimal('0'))

    fecha_min = dias[0]
    fecha_max = dias[-1] + timedelta(days=1)
    desde_dt = timezone.make_aware(datetime.combine(fecha_min, datetime.min.time()), tz)
    hasta_dt = timezone.make_aware(datetime.combine(fecha_max, datetime.min.time()), tz)

    rows_v = ventas_emit.filter(fecha_venta__gte=desde_dt, fecha_venta__lt=hasta_dt).values_list(
        'fecha_venta', 'total'
    )
    for fv, total in rows_v:
        ld = timezone.localtime(fv, tz).date()
        if ld < fecha_min:
            ld = fecha_min
        day_sum[ld] += total

    for i, di in enumerate(dias):
        nomb_dia = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'][di.weekday()]
        etiquetas_sem.append(f'{nomb_dia}')
        valores_sem.append(float(day_sum.get(di, Decimal('0'))))
    vmax = max(valores_sem + [1.0])

    zonas_agg = (
        EventoAsiento.objects.filter(evento_zona__evento__fecha_evento__gte=hoy)
        .values('evento_zona__zona__nombre')
        .annotate(
            tot=Count('id'),
            no_lib=Count('id', filter=~Q(estado='DISPONIBLE')),
        )
        .order_by('-tot')[:12]
    )
    pie_labels = []
    pie_data = []
    for z in zonas_agg:
        nombre_z = z['evento_zona__zona__nombre'] or '—'
        t = z['tot'] or 1
        oc = z['no_lib'] or 0
        pie_labels.append(nombre_z)
        pie_data.append(round(100 * oc / t) if t else 0)

    if not pie_labels:
        pie_labels = ['Sin datos']
        pie_data = [0]

    # Tendencia: últimos 3 meses naturales / calendario
    def subtract_month(y, mo, backward):
        mo -= backward
        while mo <= 0:
            mo += 12
            y -= 1
        return y, mo

    primer_mes_actual = timezone.localtime(now, tz).date().replace(day=1)
    mes_etiquetas = []
    mes_valores = []
    for atras in (2, 1, 0):
        y, m = subtract_month(primer_mes_actual.year, primer_mes_actual.month, atras)
        first_d = date(y, m, 1)
        last_dom = calendar.monthrange(y, m)[1]
        last_d = date(y, m, last_dom)

        desde_m = timezone.make_aware(datetime.combine(first_d, datetime.min.time()), tz)
        hasta_m = timezone.make_aware(datetime.combine(last_d + timedelta(days=1), datetime.min.time()), tz)

        monto_m = ventas_emit.filter(fecha_venta__gte=desde_m, fecha_venta__lt=hasta_m).aggregate(
            s=Sum('total')
        )['s'] or Decimal('0')

        mes_etiquetas.append(calendar.month_abbr[m])
        mes_valores.append(float(monto_m))

    proximos_filas = []
    for ev in proximos_list:
        st = seat_stats.get(ev.id, {'total_seats': 0, 'ocup': 0, 'pct': 0})
        cap = cap_mostrar(ev.id)
        vend = st['ocup']
        pct = st['pct'] if cap else 0
        proximos_filas.append(
            {
                'evento': ev,
                'vendidos': vend,
                'capacidad': cap,
                'pct': pct,
            }
        )

    eventos_filas = []
    for ev in eventos:
        st = seat_stats.get(ev.id, {'total_seats': 0, 'ocup': 0, 'pct': 0})
        cap_d = cap_mostrar(ev.id)
        eventos_filas.append(
            {
                'evento': ev,
                'ocup': st['ocup'],
                'capacidad': cap_d,
                'pct': st['pct'],
            }
        )

    chart_payload = {
        'ventas_semana_labels': etiquetas_sem,
        'ventas_semana_vals': valores_sem,
        'ventas_semana_ymax': max(round(vmax * 1.1, 2), 1000.0),
        'zonas_labels': pie_labels,
        'zonas_data': pie_data,
        'mensual_labels': mes_etiquetas,
        'mensual_vals': mes_valores,
    }

    zonas_lista = (
        Zona.objects.annotate(num_asientos=Count('asiento')).order_by('orden_visual', 'nombre')
    )

    return render(
        request,
        'pages/admin/dashboard.html',
        {
            'eventos': eventos,
            'seat_stats': seat_stats,
            'eventos_filas': eventos_filas,
            'cap_publicada': cap_pub,
            'proximos_filas': proximos_filas,
            'kpi_total_ventas': kpi_total_ventas,
            'kpi_reservas_activas': kpi_reservas_activas,
            'kpi_ocupacion_pct': kpi_ocupacion_pct,
            'kpi_eventos_activos': kpi_eventos_activos,
            'zonas_lista': zonas_lista,
            'chart_payload': chart_payload,
        },
    )