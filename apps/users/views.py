import calendar
import csv
import io
import re
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models import Count, Prefetch, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .models import Usuario, Rol
from apps.events.models import Evento, EventoAsiento, EventoZona, Zona
from apps.payments.models import EstadoPago, MetodoPago, Pago
from apps.reservations.models import DetalleReserva, EstadoReserva, Reserva
from apps.support.models import EstadoSoporte, Soporte, SoporteMensaje
from apps.tickets.models import CanalVenta, Entrada, EstadoVenta, Venta


# =========================
# 🔐 REGISTRO
# =========================
@never_cache
def signup_view(request):
    if request.session.get('usuario_id'):
        return redirect('/')

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        apellido = request.POST.get('apellido', '').strip()
        correo = request.POST.get('correo', '').strip().lower()
        password = request.POST.get('password', '')
        telefono = request.POST.get('telefono', '').strip() or None

        # Validaciones (Combinación Nuevo y Antiguo para mantener máxima seguridad)
        if not re.match(r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,10}$', correo or ''):
            messages.error(request, "Correo electrónico no válido.")
            return redirect('/?action=signup')

        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&.-])[A-Za-z\d@$!%*?&.-]{8,}$', password or ''):
            messages.error(request, "La contraseña no cumple con el formato seguro requerido.")
            return redirect('/?action=signup')

        if not re.match(r'^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(\s[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*$', nombre):
            messages.error(request, "El nombre debe empezar con mayúscula y no tener mayúsculas dobles.")
            return redirect('/?action=signup')

        if not re.match(r'^[A-ZÁÉÍÓÚÑ][a-zA-ZáéíóúñÁÉÍÓÚÑ]*(\s[A-ZÁÉÍÓÚÑ][a-zA-ZáéíóúñÁÉÍÓÚÑ]*)*$', apellido):
            messages.error(request, "El apellido debe tener la primera letra de cada palabra en mayúscula.")
            return redirect('/?action=signup')

        if telefono and not re.match(r'^[67]\d{7}$', telefono):
            messages.error(request, "El celular en Bolivia debe empezar con 6 o 7 y tener 8 dígitos.")
            return redirect('/?action=signup')

        if Usuario.objects.filter(correo=correo).exists():
            messages.error(request, "Este correo ya está registrado.")
            return redirect('/?action=signup')

        if telefono and Usuario.objects.filter(telefono=telefono).exists():
            messages.error(request, "Este teléfono ya está en uso.")
            return redirect('/?action=signup')

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
            return redirect('/?action=login')

        except ValidationError as e:
            messages.error(request, e.messages[0])
        except Exception:
            messages.error(request, "Error inesperado al registrarte.")

        return redirect('/?action=signup')

    return redirect('/')


# =========================
# 🔑 LOGIN
# =========================
@never_cache
def login_view(request):
    # Si ya hay sesión activa, redirigir según el rol actual
    # (no bloquear — permite que un admin logueado como cliente vuelva a loguearse)
    if request.session.get('usuario_id') and request.method == 'GET':
        rol = (request.session.get('usuario_rol') or '').strip().lower()
        if rol == 'administrador':
            return redirect('admin_panel')
        elif rol == 'soporte':
            return redirect('support_dashboard')
        return redirect('/')

    if request.method == 'POST':
        correo = request.POST.get('correo', '').strip().lower()
        password = request.POST.get('password', '')

        if not correo or not password:
            messages.error(request, "Ingresa tu correo y contraseña.")
            return redirect('/?action=login')

        if not re.match(r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,10}$', correo or ''):
            messages.error(request, "Correo electrónico no válido.")
            return redirect('/?action=login')

        try:
            usuario = Usuario.objects.select_related('rol').get(correo=correo)

            if not usuario.is_active:
                messages.error(request, "Tu cuenta está desactivada.")
                return redirect('/?action=login')

            if usuario.check_password(password):
                request.session.flush()

                request.session['usuario_id'] = usuario.id
                request.session['usuario_nombre'] = usuario.nombre
                request.session['usuario_nombre_completo'] = str(usuario)
                request.session['usuario_correo'] = usuario.correo
                request.session['usuario_rol'] = usuario.rol.nombre

                request.session.set_expiry(60 * 60 * 4)

                messages.success(request, f"Bienvenido {usuario.nombre}")

                # 🔥 REDIRECCIÓN POR ROL
                rol = (usuario.rol.nombre or '').strip().lower()
                if rol == 'administrador':
                    return redirect('admin_panel')
                elif rol == 'soporte':
                    return redirect('support_dashboard')
                else:
                    return redirect('/')

            else:
                messages.error(request, "Credenciales incorrectas.")

        except Usuario.DoesNotExist:
            messages.error(request, "Credenciales incorrectas.")

        return redirect('/?action=login')

    return redirect('/')


# =========================
# 🚪 LOGOUT
# =========================
def logout_view(request):
    request.session.flush()
    messages.success(request, "Sesión cerrada correctamente.")
    return redirect('/')


# =========================
# 👤 PERFIL
# =========================
@never_cache
def perfil_view(request):
    usuario_id = request.session.get('usuario_id')

    if not usuario_id:
        messages.error(request, "Debes iniciar sesión.")
        return redirect('/?action=login')

    try:
        usuario = Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        request.session.flush()
        return redirect('/')

    if request.method == 'POST':
        action = request.POST.get('action')

        # -------------------------
        # 🧾 ACTUALIZAR PERFIL
        # -------------------------
        if action == 'update_profile':
            nombre = request.POST.get('nombre', '').strip()
            apellido = request.POST.get('apellido', '').strip()
            nuevo_correo = request.POST.get('correo', '').strip().lower()
            telefono = request.POST.get('telefono', '').strip() or None
            dni = request.POST.get('dni', '').strip() or None

            if not re.match(r'^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(\s[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*$', nombre):
                messages.error(request, "El nombre debe empezar con mayúscula y no tener mayúsculas dobles.")
                return redirect('perfil')

            if not re.match(r'^[A-ZÁÉÍÓÚÑ][a-zA-ZáéíóúñÁÉÍÓÚÑ]*(\s[A-ZÁÉÍÓÚÑ][a-zA-ZáéíóúñÁÉÍÓÚÑ]*)*$', apellido):
                messages.error(request, "El apellido debe tener la primera letra de cada palabra en mayúscula.")
                return redirect('perfil')

            if telefono and not re.match(r'^[67]\d{7}$', telefono):
                messages.error(request, "El celular en Bolivia debe empezar con 6 o 7 y tener 8 dígitos.")
                return redirect('perfil')

            if dni and not re.match(r'^\d{7,8}(-[A-Z0-9]{1,3})?$', dni):
                messages.error(request, "Formato de DNI inválido. Ej: 1234567 o 12345678-1B")
                return redirect('perfil')

            usuario.nombre = nombre
            usuario.apellido = apellido
            usuario.telefono = telefono
            usuario.dni = dni

            if nuevo_correo != usuario.correo and Usuario.objects.filter(correo=nuevo_correo).exists():
                messages.error(request, "Ese correo ya está en uso.")
                return redirect('perfil')

            usuario.correo = nuevo_correo

            try:
                usuario.full_clean()
                usuario.save()

                request.session['usuario_nombre'] = usuario.nombre
                request.session['usuario_nombre_completo'] = str(usuario)
                request.session['usuario_correo'] = usuario.correo

                messages.success(request, "Perfil actualizado correctamente.")

            except ValidationError as e:
                messages.error(request, e.messages[0])

            return redirect('perfil')

        # -------------------------
        # 🔔 ACTUALIZAR NOTIFICACIONES
        # -------------------------
        elif action == 'update_notifications':
            usuario.notif_eventos = request.POST.get('notif_eventos') == 'on'
            usuario.notif_promociones = request.POST.get('notif_promociones') == 'on'
            usuario.notif_recordatorios = request.POST.get('notif_recordatorios') == 'on'
            usuario.notif_push = request.POST.get('notif_push') == 'on'
            
            usuario.save()
            messages.success(request, "Preferencias de notificaciones actualizadas.")
            
            return redirect('perfil')

        # -------------------------
        # 🔐 CAMBIAR PASSWORD
        # -------------------------
        elif action == 'update_password':
            current_password = request.POST.get('current_password', '')
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')

            if not usuario.check_password(current_password):
                messages.error(request, "Contraseña actual incorrecta.")

            elif new_password != confirm_password:
                messages.error(request, "Las contraseñas no coinciden.")

            elif not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&.-])[A-Za-z\d@$!%*?&.-]{8,}$', new_password):
                messages.error(request, "La nueva contraseña no cumple con el formato seguro requerido.")

            else:
                usuario.set_password(new_password)
                usuario.save()
                messages.success(request, "Contraseña actualizada.")

            return redirect('perfil')

    return render(request, 'pages/users/perfil.html', {'usuario': usuario})


# =========================
# 🛠️ PANEL ADMIN (CÓDIGO DE TUS COMPAÑEROS INTACTO)
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


def _admin_gate(request):
    if not request.session.get('usuario_id'):
        return redirect('login')
    if (request.session.get('usuario_rol') or '').strip().lower() != 'administrador':
        return redirect('inicio')
    return None


@never_cache
@require_POST
def admin_usuario_action(request):
    gate = _admin_gate(request)
    if gate:
        return gate

    uid = request.POST.get('usuario_id')
    action = (request.POST.get('action') or '').strip().lower()
    next_tab = request.POST.get('next_tab') or 'cuentas'

    try:
        uid_int = int(uid)
    except (TypeError, ValueError):
        messages.error(request, 'Usuario inválido.')
        return redirect(reverse('admin_panel') + f'?tab={next_tab}')

    usuario = Usuario.objects.select_related('rol').filter(pk=uid_int).first()
    if not usuario:
        messages.error(request, 'Usuario no encontrado.')
        return redirect(reverse('admin_panel') + f'?tab={next_tab}')

    current_admin_id = request.session.get('usuario_id')

    # No permitir acciones destructivas sobre sí mismo
    if current_admin_id and int(current_admin_id) == usuario.id and action in ('desactivar', 'eliminar'):
        messages.warning(request, 'No puedes desactivarte o eliminarte a ti mismo.')
        return redirect(reverse('admin_panel') + f'?tab={next_tab}')

    if action == 'activar':
        if usuario.activo:
            messages.info(request, 'La cuenta ya está activa.')
        else:
            usuario.activo = True
            usuario.save(update_fields=['activo', 'actualizado_en'])
            messages.success(request, 'Cuenta activada.')

    elif action == 'desactivar':
        if not usuario.activo:
            messages.info(request, 'La cuenta ya está desactivada.')
        else:
            # Evitar desactivar el último administrador activo
            rol_nombre = (usuario.rol.nombre or '').strip().lower()
            if rol_nombre == 'administrador':
                admins_activos = Usuario.objects.filter(rol__nombre__iexact='administrador', activo=True).count()
                if admins_activos <= 1:
                    messages.error(request, 'No se puede desactivar el último administrador activo.')
                    return redirect(reverse('admin_panel') + f'?tab={next_tab}')
            usuario.activo = False
            usuario.save(update_fields=['activo', 'actualizado_en'])
            messages.success(request, 'Cuenta desactivada.')

    elif action == 'set_rol':
        rol_id = request.POST.get('rol_id')
        try:
            rol_id_int = int(rol_id)
        except (TypeError, ValueError):
            messages.error(request, 'Rol inválido.')
            return redirect(reverse('admin_panel') + f'?tab={next_tab}')

        nuevo_rol = Rol.objects.filter(pk=rol_id_int).first()
        if not nuevo_rol:
            messages.error(request, 'Rol no encontrado.')
            return redirect(reverse('admin_panel') + f'?tab={next_tab}')

        # Evitar quitar rol admin al último admin activo
        if (usuario.rol.nombre or '').strip().lower() == 'administrador' and (nuevo_rol.nombre or '').strip().lower() != 'administrador':
            admins_activos = Usuario.objects.filter(rol__nombre__iexact='administrador', activo=True).count()
            if usuario.activo and admins_activos <= 1:
                messages.error(request, 'No se puede quitar el rol de administrador al último administrador activo.')
                return redirect(reverse('admin_panel') + f'?tab={next_tab}')

        usuario.rol = nuevo_rol
        usuario.save(update_fields=['rol', 'actualizado_en'])
        messages.success(request, 'Rol actualizado.')

    elif action == 'eliminar':
        # Evitar borrar el último administrador activo
        rol_nombre = (usuario.rol.nombre or '').strip().lower()
        if rol_nombre == 'administrador' and usuario.activo:
            admins_activos = Usuario.objects.filter(rol__nombre__iexact='administrador', activo=True).count()
            if admins_activos <= 1:
                messages.error(request, 'No se puede eliminar el último administrador activo.')
                return redirect(reverse('admin_panel') + f'?tab={next_tab}')

        usuario.delete()
        messages.success(request, 'Cuenta eliminada.')

    else:
        messages.error(request, 'Acción no válida.')

    return redirect(reverse('admin_panel') + f'?tab={next_tab}')


@never_cache
@require_POST
def admin_usuario_create(request):
    gate = _admin_gate(request)
    if gate:
        return gate

    back = reverse('admin_panel') + '?tab=cuentas'

    nombre = request.POST.get('nombre', '').strip()
    apellido = request.POST.get('apellido', '').strip()
    correo = request.POST.get('correo', '').strip().lower()
    password = request.POST.get('password', '')
    password2 = request.POST.get('password_confirm', '')
    telefono = request.POST.get('telefono', '').strip() or None
    rol_id = request.POST.get('rol_id')
    activo = request.POST.get('activo') == 'on'

    if not nombre or not apellido or not correo or not password:
        messages.error(request, 'Completa nombre, apellido, correo y contraseña.')
        return redirect(back)

    if not re.match(r'^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(\s[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*$', nombre):
        messages.error(request, 'El nombre debe empezar con mayúscula y no tener mayúsculas dobles.')
        return redirect(back)

    if not re.match(r'^[A-ZÁÉÍÓÚÑ][a-zA-ZáéíóúñÁÉÍÓÚÑ]*(\s[A-ZÁÉÍÓÚÑ][a-zA-ZáéíóúñÁÉÍÓÚÑ]*)*$', apellido):
        messages.error(request, 'El apellido debe tener la primera letra de cada palabra en mayúscula.')
        return redirect(back)

    if not re.match(r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,10}$', correo):
        messages.error(request, 'Correo electrónico no válido.')
        return redirect(back)

    if password != password2:
        messages.error(request, 'Las contraseñas no coinciden.')
        return redirect(back)

    if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&.-])[A-Za-z\d@$!%*?&.-]{8,}$', password):
        messages.error(request, 'La contraseña debe tener mín. 8 caracteres, mayúscula, minúscula, número y un especial (@$!%*?&.-).')
        return redirect(back)

    if telefono and not re.match(r'^[67]\d{7}$', telefono):
        messages.error(request, 'El celular en Bolivia debe empezar con 6 o 7 y tener 8 dígitos.')
        return redirect(back)

    if Usuario.objects.filter(correo=correo).exists():
        messages.error(request, 'Este correo ya está registrado.')
        return redirect(back)

    if telefono and Usuario.objects.filter(telefono=telefono).exists():
        messages.error(request, 'Este teléfono ya está en uso.')
        return redirect(back)

    try:
        rol_id_int = int(rol_id)
    except (TypeError, ValueError):
        messages.error(request, 'Selecciona un rol válido.')
        return redirect(back)

    rol = Rol.objects.filter(pk=rol_id_int).first()
    if not rol:
        messages.error(request, 'Rol no encontrado.')
        return redirect(back)

    rol_nombre = (rol.nombre or '').strip().lower()
    is_staff = rol_nombre == 'administrador'

    try:
        with transaction.atomic():
            usuario = Usuario(
                nombre=nombre,
                apellido=apellido,
                correo=correo,
                telefono=telefono,
                rol=rol,
                activo=activo,
                is_staff=is_staff,
            )
            usuario.set_password(password)
            usuario.full_clean()
            usuario.save()
        messages.success(request, f'Usuario «{nombre} {apellido}» creado correctamente.')
    except ValidationError as e:
        messages.error(request, e.messages[0] if e.messages else str(e))
    except Exception:
        messages.error(request, 'No se pudo crear el usuario.')

    return redirect(back)


def _parse_date_get(val, default):
    if not val:
        return default
    try:
        return date.fromisoformat(str(val).strip()[:10])
    except ValueError:
        return default

def _reserva_tiempo_clase_texto(reserva, now):
    nombre = (reserva.estado_reserva.nombre or '').lower()
    if 'cancel' in nombre:
        return 'cell-muted', 'Cancelada'
    if 'confirm' in nombre:
        return 'cell-muted', 'Confirmada'
    if 'expir' in nombre:
        return 'admin-text-amber', 'Expirada'
    if reserva.fecha_expiracion:
        exp = reserva.fecha_expiracion
        if timezone.is_naive(exp):
            exp = timezone.make_aware(exp, timezone.get_current_timezone())
        if exp < now:
            return 'admin-text-amber', 'Expiró'
        diff = exp - now
        total_s = max(0, int(diff.total_seconds()))
        m, _s = divmod(total_s, 60)
        h, m = divmod(m, 60)
        if h >= 48:
            return 'cell-muted', f'{h // 24} días'
        if h > 0:
            return 'cell-muted', f'{h}h {m}m'
        return 'cell-muted', f'{m} min'
    return 'cell-muted', '—'


@never_cache
@require_POST
def admin_reserva_action(request):
    gate = _admin_gate(request)
    if gate:
        return gate

    rid = request.POST.get('reserva_id')
    action = (request.POST.get('action') or '').strip().lower()
    reserva = get_object_or_404(Reserva.objects.select_related('estado_reserva'), pk=rid)
    nuevo_estado = None

    if action == 'confirmar':
        nuevo_estado = EstadoReserva.objects.filter(nombre__icontains='confirm').order_by('id').first()
        if not nuevo_estado:
            messages.error(request, 'No existe un estado de reserva tipo «confirmada» en la base.')
    elif action == 'cancelar':
        nuevo_estado = (
            EstadoReserva.objects.filter(nombre__icontains='cancel').order_by('id').first()
            or EstadoReserva.objects.filter(nombre__icontains='anul').order_by('id').first()
        )
        if not nuevo_estado:
            messages.error(request, 'No existe un estado de reserva tipo «cancelada» en la base.')
    else:
        messages.error(request, 'Acción no válida.')
        return redirect(reverse('admin_panel') + '?tab=reservas')

    if nuevo_estado:
        actual = (reserva.estado_reserva.nombre or '').lower()
        if action == 'confirmar' and ('cancel' in actual or 'expir' in actual):
            messages.warning(request, 'No se puede confirmar esta reserva en su estado actual.')
        elif action == 'cancelar' and ('cancel' in actual or 'expir' in actual):
            messages.warning(request, 'La reserva ya está cancelada o expirada.')
        else:
            reserva.estado_reserva = nuevo_estado
            reserva.save(update_fields=['estado_reserva', 'actualizado_en'])
            messages.success(request, 'Reserva actualizada.')

    return redirect(reverse('admin_panel') + '?tab=reservas')


@never_cache
@require_GET
def admin_report_export(request):
    gate = _admin_gate(request)
    if gate:
        return gate

    tz = timezone.get_current_timezone()
    hoy = timezone.localdate()
    desde = _parse_date_get(request.GET.get('rep_desde'), hoy.replace(day=1))
    hasta = _parse_date_get(request.GET.get('rep_hasta'), hoy)
    if hasta < desde:
        desde, hasta = hasta, desde
    tipo = (request.GET.get('rep_tipo') or 'ventas').strip().lower()
    fmt = (request.GET.get('fmt') or 'csv').strip().lower()

    desde_dt = timezone.make_aware(datetime.combine(desde, datetime.min.time()), tz)
    hasta_dt = timezone.make_aware(datetime.combine(hasta + timedelta(days=1), datetime.min.time()), tz)

    if fmt == 'pdf':
        ventas_emit = (
            Venta.objects.filter(
                estado_venta__nombre__icontains='emitida',
                fecha_venta__gte=desde_dt,
                fecha_venta__lt=hasta_dt,
            )
            .select_related('reserva__evento', 'usuario', 'estado_venta')
            .order_by('-fecha_venta')[:500]
        )
        reservas = (
            Reserva.objects.filter(fecha_creacion__gte=desde_dt, fecha_creacion__lt=hasta_dt)
            .select_related('evento', 'estado_reserva', 'usuario', 'creada_por_usuario')
            .order_by('-fecha_creacion')[:500]
        )
        response = render(
            request,
            'pages/admin/reporte_print.html',
            {'desde': desde, 'hasta': hasta, 'tipo': tipo, 'ventas': ventas_emit, 'reservas': reservas},
        )
        response['Content-Disposition'] = 'attachment; filename="reporte_teatro.html"'
        return response

    buffer = io.StringIO()
    w = csv.writer(buffer)

    if tipo == 'reservas':
        w.writerow(['codigo_reserva', 'fecha_creacion', 'estado', 'evento', 'total', 'usuario_correo'])
        for r in (
            Reserva.objects.filter(fecha_creacion__gte=desde_dt, fecha_creacion__lt=hasta_dt)
            .select_related('evento', 'estado_reserva', 'usuario', 'creada_por_usuario')
            .order_by('-fecha_creacion')
        ):
            u = r.usuario or r.creada_por_usuario
            w.writerow(
                [
                    r.codigo_reserva,
                    r.fecha_creacion.isoformat(),
                    r.estado_reserva.nombre,
                    r.evento.nombre,
                    str(r.total_reserva),
                    u.correo if u else '',
                ]
            )
    elif tipo == 'ocupacion':
        w.writerow(['evento_id', 'evento', 'fecha_evento', 'zona', 'asientos_total', 'ocupados', 'pct_ocupacion'])
        agg = (
            EventoAsiento.objects.filter(
                evento_zona__evento__fecha_evento__gte=desde,
                evento_zona__evento__fecha_evento__lte=hasta,
            )
            .values(
                'evento_zona__evento_id',
                'evento_zona__evento__nombre',
                'evento_zona__evento__fecha_evento',
                'evento_zona__zona__nombre',
            )
            .annotate(tot=Count('id'), no_lib=Count('id', filter=~Q(estado='DISPONIBLE')))
            .order_by('evento_zona__evento__fecha_evento', 'evento_zona__zona__nombre')
        )
        for row in agg:
            t = row['tot'] or 0
            ou = row['no_lib'] or 0
            pct = round(100 * ou / t) if t else 0
            w.writerow(
                [
                    row['evento_zona__evento_id'],
                    row['evento_zona__evento__nombre'],
                    row['evento_zona__evento__fecha_evento'].isoformat(),
                    row['evento_zona__zona__nombre'] or '—',
                    t,
                    ou,
                    pct,
                ]
            )
    else:
        w.writerow(['venta_id', 'fecha_venta', 'estado', 'total', 'evento', 'cliente_correo', 'codigo_reserva'])
        for v in (
            Venta.objects.filter(fecha_venta__gte=desde_dt, fecha_venta__lt=hasta_dt)
            .select_related('reserva__evento', 'usuario', 'estado_venta')
            .order_by('-fecha_venta')
        ):
            u = v.usuario
            w.writerow(
                [
                    v.id,
                    v.fecha_venta.isoformat(),
                    v.estado_venta.nombre,
                    str(v.total),
                    v.reserva.evento.nombre,
                    u.correo if u else '',
                    v.reserva.codigo_reserva,
                ]
            )

    response = HttpResponse('\ufeff' + buffer.getvalue(), content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="reporte_{tipo}_{desde}_{hasta}.csv"'
    return response


@never_cache
def admin_venta_detalle(request, venta_id):
    gate = _admin_gate(request)
    if gate:
        return gate

    venta = get_object_or_404(
        Venta.objects.select_related(
            'reserva__evento', 'usuario', 'empleado', 'estado_venta', 'canal_venta'
        ).prefetch_related(
            Prefetch(
                'reserva__detalles',
                queryset=DetalleReserva.objects.select_related('evento_zona__zona', 'evento_asiento__asiento'),
            ),
            Prefetch(
                'reserva__pagos',
                queryset=Pago.objects.select_related('metodo_pago', 'estado_pago').order_by('-fecha_creacion'),
            ),
            Prefetch('entradas', queryset=Entrada.objects.select_related('estado_entrada')),
        ),
        pk=venta_id,
    )
    return render(request, 'pages/admin/venta_detalle.html', {'venta': venta})


@never_cache
@require_POST
def admin_soporte_reply(request):
    gate = _admin_gate(request)
    if gate:
        return gate

    ticket_id = request.POST.get('ticket_id')
    texto = (request.POST.get('mensaje') or '').strip()
    if not ticket_id or not texto:
        messages.error(request, 'Debes seleccionar ticket y escribir un mensaje.')
        return redirect(reverse('admin_panel') + '?tab=soporte')

    ticket = get_object_or_404(Soporte, pk=ticket_id)
    usuario = Usuario.objects.filter(pk=request.session.get('usuario_id')).first()
    if not usuario:
        messages.error(request, 'Sesión inválida.')
        return redirect('login')

    if ticket.fecha_cierre:
        messages.error(request, 'El ticket está cerrado.')
        return redirect(reverse('admin_panel') + f'?tab=soporte&sup_id={ticket.id}')

    SoporteMensaje.objects.create(soporte=ticket, remitente=usuario, mensaje=texto)
    messages.success(request, 'Mensaje enviado.')
    return redirect(reverse('admin_panel') + f'?tab=soporte&sup_id={ticket.id}')


@never_cache
@require_POST
def admin_soporte_close(request):
    gate = _admin_gate(request)
    if gate:
        return gate

    ticket_id = request.POST.get('ticket_id')
    if not ticket_id:
        messages.error(request, 'Ticket inválido.')
        return redirect(reverse('admin_panel') + '?tab=soporte')

    ticket = get_object_or_404(Soporte, pk=ticket_id)
    estado_cerrado = EstadoSoporte.objects.filter(nombre__icontains='cerr').order_by('id').first()
    if not estado_cerrado:
        messages.error(request, 'No existe estado de soporte cerrado.')
        return redirect(reverse('admin_panel') + f'?tab=soporte&sup_id={ticket.id}')

    ticket.estado_soporte = estado_cerrado
    ticket.fecha_cierre = timezone.now()
    ticket.save(update_fields=['estado_soporte', 'fecha_cierre', 'actualizado_en'])
    messages.success(request, 'Ticket cerrado.')
    return redirect(reverse('admin_panel') + '?tab=soporte')


@never_cache
@require_POST
def admin_config_general_save(request):
    gate = _admin_gate(request)
    if gate:
        return gate

    usuario = Usuario.objects.filter(pk=request.session.get('usuario_id')).first()
    if not usuario:
        return redirect('login')

    usuario.nombre = (request.POST.get('nombre') or usuario.nombre).strip()[:100]
    usuario.apellido = (request.POST.get('apellido') or usuario.apellido).strip()[:100]
    nuevo_correo = (request.POST.get('correo') or usuario.correo).strip().lower()
    telefono = (request.POST.get('telefono') or '').strip() or None

    if Usuario.objects.exclude(pk=usuario.pk).filter(correo=nuevo_correo).exists():
        messages.error(request, 'Ese correo ya está en uso.')
        return redirect(reverse('admin_panel') + '?tab=configuracion&cfg_tab=general')

    usuario.correo = nuevo_correo
    usuario.telefono = telefono
    usuario.save(update_fields=['nombre', 'apellido', 'correo', 'telefono', 'actualizado_en'])
    request.session['usuario_nombre'] = usuario.nombre
    request.session['usuario_correo'] = usuario.correo
    messages.success(request, 'Datos generales actualizados.')
    return redirect(reverse('admin_panel') + '?tab=configuracion&cfg_tab=general')


@never_cache
@require_POST
def admin_config_security_save(request):
    gate = _admin_gate(request)
    if gate:
        return gate

    usuario = Usuario.objects.filter(pk=request.session.get('usuario_id')).first()
    if not usuario:
        return redirect('login')

    current = request.POST.get('current_password') or ''
    new_password = request.POST.get('new_password') or ''
    repeat_password = request.POST.get('repeat_password') or ''

    if not usuario.check_password(current):
        messages.error(request, 'Contraseña actual incorrecta.')
        return redirect(reverse('admin_panel') + '?tab=configuracion&cfg_tab=seguridad')
    if len(new_password) < 8:
        messages.error(request, 'La nueva contraseña debe tener al menos 8 caracteres.')
        return redirect(reverse('admin_panel') + '?tab=configuracion&cfg_tab=seguridad')
    if new_password != repeat_password:
        messages.error(request, 'La confirmación de contraseña no coincide.')
        return redirect(reverse('admin_panel') + '?tab=configuracion&cfg_tab=seguridad')

    usuario.set_password(new_password)
    usuario.save(update_fields=['password'])
    messages.success(request, 'Contraseña actualizada.')
    return redirect(reverse('admin_panel') + '?tab=configuracion&cfg_tab=seguridad')


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
        precio_vip = None
        precio_grad = None
        precio_gen = None
        cap_total = 0
        for ez in ev.eventozona_set.all():
            nombre_z = (ez.zona.nombre or '').lower()
            cap_total += int(ez.capacidad_evento or 0)
            if ('vip' in nombre_z or 'prefer' in nombre_z) and precio_vip is None:
                precio_vip = ez.precio_base
            elif ('grader' in nombre_z) and precio_grad is None:
                precio_grad = ez.precio_base
            elif ('general' in nombre_z or 'fosa' in nombre_z or 'popular' in nombre_z) and precio_gen is None:
                precio_gen = ez.precio_base
        eventos_filas.append(
            {
                'evento': ev,
                'ocup': st['ocup'],
                'capacidad': cap_d,
                'pct': st['pct'],
                'precio_vip': precio_vip,
                'precio_grad': precio_grad,
                'precio_gen': precio_gen,
                'cap_total': cap_total if cap_total > 0 else (cap_d or 0),
                'es_activo': 'activ' in (ev.estado_evento.nombre or '').lower(),
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

    # ——— Reservas / Ventas / Reportes (BD) ———
    res_q = (request.GET.get('res_q') or '').strip()
    res_estado = (request.GET.get('res_estado') or '').strip()
    vta_q = (request.GET.get('vta_q') or '').strip()
    vta_estado = (request.GET.get('vta_estado') or '').strip()

    rep_desde = _parse_date_get(request.GET.get('rep_desde'), hoy.replace(day=1))
    rep_hasta = _parse_date_get(request.GET.get('rep_hasta'), hoy)
    if rep_hasta < rep_desde:
        rep_desde, rep_hasta = rep_hasta, rep_desde
    rep_tipo = (request.GET.get('rep_tipo') or 'ventas').strip()

    reservas_qs = (
        Reserva.objects.select_related(
            'usuario', 'creada_por_usuario', 'evento', 'estado_reserva', 'canal_venta'
        )
        .prefetch_related(
            Prefetch(
                'detalles',
                queryset=DetalleReserva.objects.select_related(
                    'evento_zona__zona', 'evento_asiento__asiento'
                ),
            )
        )
        .order_by('-fecha_creacion')
    )
    if res_q:
        rq = (
            Q(codigo_reserva__icontains=res_q)
            | Q(evento__nombre__icontains=res_q)
            | Q(usuario__nombre__icontains=res_q)
            | Q(usuario__apellido__icontains=res_q)
            | Q(usuario__correo__icontains=res_q)
            | Q(creada_por_usuario__nombre__icontains=res_q)
            | Q(creada_por_usuario__apellido__icontains=res_q)
            | Q(creada_por_usuario__correo__icontains=res_q)
        )
        if res_q.isdigit():
            rq |= Q(pk=int(res_q))
        reservas_qs = reservas_qs.filter(rq)
    if res_estado:
        reservas_qs = reservas_qs.filter(estado_reserva__nombre__iexact=res_estado)
    reservas_list = list(reservas_qs[:400])

    reservas_rows = []
    for r in reservas_list:
        as_parts = []
        for d in r.detalles.all():
            zn = d.evento_zona.zona.nombre if d.evento_zona_id else '—'
            if d.evento_asiento_id:
                a = d.evento_asiento.asiento
                as_parts.append(f'{zn} · {a.fila}-{a.numero}')
            else:
                as_parts.append(f'{zn} (×{d.cantidad})')
        as_txt = ', '.join(as_parts) if as_parts else '—'
        t_cls, t_txt = _reserva_tiempo_clase_texto(r, now)
        ne = (r.estado_reserva.nombre or '').lower()
        reservas_rows.append(
            {
                'reserva': r,
                'asiento_txt': as_txt,
                'tiempo_class': t_cls,
                'tiempo_txt': t_txt,
                'puede_confirmar': ne == 'activa',
                'puede_cancelar': ne in ('activa', 'confirmada'),
            }
        )

    kpi_res_panel_activa = (
        Reserva.objects.filter(estado_reserva__nombre__icontains='activa')
        .exclude(estado_reserva__nombre__icontains='inactiv')
        .count()
    )
    kpi_res_panel_confirm = Reserva.objects.filter(estado_reserva__nombre__icontains='confirm').count()
    kpi_res_panel_exp = Reserva.objects.filter(estado_reserva__nombre__icontains='expir').count()
    cat_estados_reserva = list(EstadoReserva.objects.all().order_by('nombre'))

    ventas_qs = (
        Venta.objects.select_related('reserva__evento', 'usuario', 'estado_venta', 'canal_venta')
        .prefetch_related(
            Prefetch(
                'reserva__detalles',
                queryset=DetalleReserva.objects.select_related(
                    'evento_zona__zona', 'evento_asiento__asiento'
                ),
            ),
            Prefetch(
                'reserva__pagos',
                queryset=Pago.objects.select_related('metodo_pago').order_by('-fecha_creacion'),
            ),
        )
        .order_by('-fecha_venta')
    )
    if vta_q:
        vq = (
            Q(reserva__evento__nombre__icontains=vta_q)
            | Q(usuario__nombre__icontains=vta_q)
            | Q(usuario__apellido__icontains=vta_q)
            | Q(usuario__correo__icontains=vta_q)
            | Q(reserva__codigo_reserva__icontains=vta_q)
        )
        if vta_q.isdigit():
            vq |= Q(pk=int(vta_q))
        ventas_qs = ventas_qs.filter(vq)
    if vta_estado:
        ventas_qs = ventas_qs.filter(estado_venta__nombre__iexact=vta_estado)
    ventas_list = list(ventas_qs[:400])

    ventas_rows = []
    for v in ventas_list:
        pagos_l = list(v.reserva.pagos.all()[:1])
        metodo = pagos_l[0].metodo_pago.nombre if pagos_l else '—'
        ap = []
        for d in v.reserva.detalles.all():
            zn = d.evento_zona.zona.nombre if d.evento_zona_id else '—'
            if d.evento_asiento_id:
                a = d.evento_asiento.asiento
                ap.append(f'{zn} ({a.fila}-{a.numero})')
            else:
                ap.append(f'{zn} ({d.cantidad})')
        ventas_rows.append(
            {
                'venta': v,
                'metodo': metodo,
                'asientos_txt': ', '.join(ap) if ap else '—',
            }
        )

    emitidas_panel = Venta.objects.filter(estado_venta__nombre__icontains='emitida')
    kpi_vta_ingresos = emitidas_panel.aggregate(s=Sum('total'))['s'] or Decimal('0')
    kpi_vta_emitidas = emitidas_panel.count()
    kpi_vta_otras = Venta.objects.exclude(estado_venta__nombre__icontains='emitida').count()
    cat_estados_venta = list(EstadoVenta.objects.all().order_by('nombre'))

    rep_desde_dt = timezone.make_aware(datetime.combine(rep_desde, datetime.min.time()), tz)
    rep_hasta_dt = timezone.make_aware(datetime.combine(rep_hasta + timedelta(days=1), datetime.min.time()), tz)

    ventas_rango_emit = Venta.objects.filter(
        estado_venta__nombre__icontains='emitida',
        fecha_venta__gte=rep_desde_dt,
        fecha_venta__lt=rep_hasta_dt,
    )
    rep_kpi_ingresos = ventas_rango_emit.aggregate(s=Sum('total'))['s'] or Decimal('0')
    rep_kpi_tickets = Entrada.objects.filter(
        venta__estado_venta__nombre__icontains='emitida',
        venta__fecha_venta__gte=rep_desde_dt,
        venta__fecha_venta__lt=rep_hasta_dt,
    ).count()

    as_rep = EventoAsiento.objects.filter(
        evento_zona__evento__fecha_evento__gte=rep_desde,
        evento_zona__evento__fecha_evento__lte=rep_hasta,
    )
    trp = as_rep.count()
    orp = as_rep.exclude(estado='DISPONIBLE').count()
    rep_kpi_ocup = round(100 * orp / trp) if trp else 0
    rep_kpi_eventos = Evento.objects.filter(
        fecha_evento__gte=rep_desde, fecha_evento__lte=rep_hasta
    ).count()

    end_d = min(rep_hasta, hoy)
    start_win = max(rep_desde, end_d - timedelta(days=6))
    dias_rep = []
    dcur = start_win
    while dcur <= end_d:
        dias_rep.append(dcur)
        dcur += timedelta(days=1)

    rep_win_desde_dt = timezone.make_aware(datetime.combine(start_win, datetime.min.time()), tz)
    rep_win_hasta_dt = timezone.make_aware(datetime.combine(end_d + timedelta(days=1), datetime.min.time()), tz)

    day_sum_rep = defaultdict(lambda: Decimal('0'))
    for fv, total in Venta.objects.filter(
        estado_venta__nombre__icontains='emitida',
        fecha_venta__gte=rep_win_desde_dt,
        fecha_venta__lt=rep_win_hasta_dt,
    ).values_list('fecha_venta', 'total'):
        ld = timezone.localtime(fv, tz).date()
        if start_win <= ld <= end_d:
            day_sum_rep[ld] += total

    dow_es = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
    rep_sem_labels = []
    rep_sem_vals = []
    for di in dias_rep:
        rep_sem_labels.append(f'{dow_es[di.weekday()]} {di.day:02d}')
        rep_sem_vals.append(float(day_sum_rep.get(di, Decimal('0'))))
    rep_sem_ymax = max(rep_sem_vals + [1.0]) * 1.1

    zr = (
        EventoAsiento.objects.filter(
            evento_zona__evento__fecha_evento__gte=rep_desde,
            evento_zona__evento__fecha_evento__lte=rep_hasta,
        )
        .values('evento_zona__zona__nombre')
        .annotate(tot=Count('id'), no_lib=Count('id', filter=~Q(estado='DISPONIBLE')))
        .order_by('-tot')[:12]
    )
    rep_zonas_labels = []
    rep_zonas_data = []
    for z in zr:
        nombre_z = z['evento_zona__zona__nombre'] or '—'
        t = z['tot'] or 1
        oc = z['no_lib'] or 0
        rep_zonas_labels.append(nombre_z)
        rep_zonas_data.append(round(100 * oc / t) if t else 0)
    if not rep_zonas_labels:
        rep_zonas_labels = ['Sin datos']
        rep_zonas_data = [0]

    reportes_chart_payload = {
        'sem_labels': rep_sem_labels,
        'sem_vals': rep_sem_vals,
        'sem_ymax': max(round(rep_sem_ymax, 2), 500.0),
        'zonas_labels': rep_zonas_labels,
        'zonas_data': rep_zonas_data,
    }

    # ——— Soporte / Transacciones / Configuración (BD) ———
    sup_q = (request.GET.get('sup_q') or '').strip()
    sup_estado = (request.GET.get('sup_estado') or '').strip()
    sup_id = request.GET.get('sup_id')

    soporte_qs = (
        Soporte.objects.select_related('usuario', 'estado_soporte', 'categoria_soporte', 'pago', 'entrada')
        .prefetch_related(Prefetch('mensajes', queryset=SoporteMensaje.objects.select_related('remitente')))
        .order_by('-fecha_creacion')
    )
    if sup_q:
        soporte_qs = soporte_qs.filter(
            Q(numero_reclamo__icontains=sup_q)
            | Q(asunto__icontains=sup_q)
            | Q(usuario__correo__icontains=sup_q)
            | Q(usuario__nombre__icontains=sup_q)
            | Q(usuario__apellido__icontains=sup_q)
        )
    if sup_estado:
        soporte_qs = soporte_qs.filter(estado_soporte__nombre__iexact=sup_estado)
    soporte_list = list(soporte_qs[:250])
    estados_soporte = list(EstadoSoporte.objects.all().order_by('id'))
    soporte_total = Soporte.objects.count()
    soporte_pendientes = Soporte.objects.exclude(estado_soporte__nombre__icontains='cerr').count()
    soporte_cerrados = Soporte.objects.filter(estado_soporte__nombre__icontains='cerr').count()

    soporte_activo = None
    if sup_id:
        try:
            sid = int(sup_id)
            soporte_activo = next((s for s in soporte_list if s.id == sid), None)
            if not soporte_activo:
                soporte_activo = Soporte.objects.select_related(
                    'usuario', 'estado_soporte', 'categoria_soporte'
                ).prefetch_related(
                    Prefetch('mensajes', queryset=SoporteMensaje.objects.select_related('remitente'))
                ).filter(pk=sid).first()
        except ValueError:
            pass
    if not soporte_activo and soporte_list:
        soporte_activo = soporte_list[0]

    trans_q = (request.GET.get('trans_q') or '').strip()
    trans_estado = (request.GET.get('trans_estado') or '').strip()
    trans_metodo = (request.GET.get('trans_metodo') or '').strip()
    trans_qs = (
        Pago.objects.select_related('reserva__evento', 'metodo_pago', 'estado_pago', 'confirmado_por_usuario')
        .order_by('-fecha_creacion')
    )
    if trans_q:
        tq = Q(referencia_externa__icontains=trans_q) | Q(reserva__codigo_reserva__icontains=trans_q)
        if trans_q.isdigit():
            tq |= Q(pk=int(trans_q))
        trans_qs = trans_qs.filter(tq)
    if trans_estado:
        trans_qs = trans_qs.filter(estado_pago__nombre__iexact=trans_estado)
    if trans_metodo:
        trans_qs = trans_qs.filter(metodo_pago__nombre__iexact=trans_metodo)
    transacciones_rows = list(trans_qs[:300])
    estados_pago = list(EstadoPago.objects.all().order_by('nombre'))
    metodos_pago = list(MetodoPago.objects.all().order_by('nombre'))

    # ——— Cuentas (BD) ———
    usr_q = (request.GET.get('usr_q') or '').strip()
    usr_estado = (request.GET.get('usr_estado') or '').strip().lower()  # activo|inactivo|''
    usr_rol = (request.GET.get('usr_rol') or '').strip().lower()

    usuarios_qs = Usuario.objects.select_related('rol').order_by('-fecha_creacion')
    if usr_q:
        uq = (
            Q(nombre__icontains=usr_q)
            | Q(apellido__icontains=usr_q)
            | Q(correo__icontains=usr_q)
            | Q(telefono__icontains=usr_q)
            | Q(dni__icontains=usr_q)
        )
        if usr_q.isdigit():
            uq |= Q(pk=int(usr_q))
        usuarios_qs = usuarios_qs.filter(uq)
    if usr_estado == 'activo':
        usuarios_qs = usuarios_qs.filter(activo=True)
    elif usr_estado == 'inactivo':
        usuarios_qs = usuarios_qs.filter(activo=False)
    if usr_rol:
        usuarios_qs = usuarios_qs.filter(rol__nombre__iexact=usr_rol)

    usuarios_list = list(usuarios_qs[:400])
    roles_list = list(Rol.objects.all().order_by('nombre'))

    current_admin = Usuario.objects.select_related('rol').filter(pk=request.session.get('usuario_id')).first()
    cfg_tab = (request.GET.get('cfg_tab') or 'general').strip().lower()
    noti_unread = SoporteMensaje.objects.count()
    canales_count = CanalVenta.objects.count()

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
            'res_q': res_q,
            'res_estado': res_estado,
            'reservas_rows': reservas_rows,
            'kpi_res_panel_activa': kpi_res_panel_activa,
            'kpi_res_panel_confirm': kpi_res_panel_confirm,
            'kpi_res_panel_exp': kpi_res_panel_exp,
            'cat_estados_reserva': cat_estados_reserva,
            'vta_q': vta_q,
            'vta_estado': vta_estado,
            'ventas_rows': ventas_rows,
            'kpi_vta_ingresos': kpi_vta_ingresos,
            'kpi_vta_emitidas': kpi_vta_emitidas,
            'kpi_vta_otras': kpi_vta_otras,
            'cat_estados_venta': cat_estados_venta,
            'rep_desde': rep_desde,
            'rep_hasta': rep_hasta,
            'rep_tipo': rep_tipo,
            'rep_kpi_ingresos': rep_kpi_ingresos,
            'rep_kpi_tickets': rep_kpi_tickets,
            'rep_kpi_ocup': rep_kpi_ocup,
            'rep_kpi_eventos': rep_kpi_eventos,
            'reportes_chart_payload': reportes_chart_payload,
            'sup_q': sup_q,
            'sup_estado': sup_estado,
            'sup_id': sup_id,
            'soporte_list': soporte_list,
            'soporte_activo': soporte_activo,
            'estados_soporte': estados_soporte,
            'soporte_total': soporte_total,
            'soporte_pendientes': soporte_pendientes,
            'soporte_cerrados': soporte_cerrados,
            'trans_q': trans_q,
            'trans_estado': trans_estado,
            'trans_metodo': trans_metodo,
            'transacciones_rows': transacciones_rows,
            'estados_pago': estados_pago,
            'metodos_pago': metodos_pago,
            'current_admin': current_admin,
            'cfg_tab': cfg_tab,
            'noti_unread': noti_unread,
            'canales_count': canales_count,
            'usr_q': usr_q,
            'usr_estado': usr_estado,
            'usr_rol': usr_rol,
            'usuarios_list': usuarios_list,
            'roles_list': roles_list,
        },
    )