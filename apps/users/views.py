import re
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.db import transaction
from django.core.exceptions import ValidationError
from django.urls import reverse

from .models import Usuario, Rol
from apps.events.models import Evento


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
                if usuario.rol.nombre.lower() == 'administrador':
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
def admin_panel(request):
    rol = (request.session.get('usuario_rol') or '').strip().lower()

    if rol != 'administrador':
        return redirect('inicio')

    eventos = Evento.objects.all()

    return render(request, 'pages/admin/dashboard.html', {
        'eventos': eventos
    })