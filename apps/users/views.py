import re
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.views.decorators.cache import never_cache
from django.db import transaction
from django.core.exceptions import ValidationError

from .models import Usuario, Rol


# =========================
# 🔐 REGISTRO
# =========================
@never_cache
def signup_view(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        apellido = request.POST.get('apellido', '').strip()
        correo = request.POST.get('correo', '').strip().lower()
        password = request.POST.get('password', '')
        telefono = request.POST.get('telefono', '').strip() or None

        # Validaciones básicas (las críticas ya están en el modelo)
        if len(nombre) < 2 or len(apellido) < 2:
            messages.error(request, "Nombre y apellido deben tener al menos 2 caracteres.")
            return redirect('/?action=signup')

        if Usuario.objects.filter(correo=correo).exists():
            messages.error(request, "Este correo ya está registrado.")
            return redirect('/?action=signup')

        if telefono and Usuario.objects.filter(telefono=telefono).exists():
            messages.error(request, "Este teléfono ya está en uso.")
            return redirect('/?action=signup')

        rol_cliente, _ = Rol.objects.get_or_create(
            nombre='cliente'
        )   

        try:
            with transaction.atomic():
                usuario = Usuario(
                    nombre=nombre,
                    apellido=apellido,
                    correo=correo,
                    telefono=telefono or None,
                    rol=rol_cliente,
                    activo=True
                )
                usuario.set_password(password)  # 🔥 usa hashing seguro
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
    if request.method == 'POST':
        correo = request.POST.get('correo', '').strip().lower()
        password = request.POST.get('password', '')

        try:
            usuario = Usuario.objects.select_related('rol').get(correo=correo)

            if not usuario.is_active:
                messages.error(request, "Tu cuenta está desactivada.")
                return redirect('/?action=login')

            if usuario.check_password(password):  # 🔥 usar método del modelo
                request.session.flush()  # limpia sesiones previas

                request.session['usuario_id'] = usuario.id
                request.session['usuario_nombre'] = usuario.nombre
                request.session['usuario_nombre_completo'] = str(usuario)
                request.session['usuario_correo'] = usuario.correo
                request.session['usuario_rol'] = usuario.rol.nombre

                request.session.set_expiry(60 * 60 * 4)  # 4 horas

                messages.success(request, f"Bienvenido {usuario.nombre}")
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
            usuario.nombre = request.POST.get('nombre', '').strip()
            usuario.apellido = request.POST.get('apellido', '').strip()
            nuevo_correo = request.POST.get('correo', '').strip().lower()
            usuario.telefono = request.POST.get('telefono', '').strip() or None
            usuario.dni = request.POST.get('dni', '').strip() or None

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

            elif len(new_password) < 8:
                messages.error(request, "La contraseña debe tener al menos 8 caracteres.")

            else:
                usuario.set_password(new_password)
                usuario.save()
                messages.success(request, "Contraseña actualizada.")

            return redirect('perfil')

    return render(request, 'pages/usuarios/perfil.html', {'usuario': usuario})