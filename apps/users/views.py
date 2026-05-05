import re
from django.shortcuts import render, redirect
from django.contrib import messages
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
    if request.method == 'POST':
        correo = request.POST.get('correo', '').strip().lower()
        password = request.POST.get('password', '')

        try:
            usuario = Usuario.objects.select_related('rol').get(correo=correo)

            if not usuario.is_active:
                messages.error(request, "Tu cuenta está desactivada.")
                return redirect('/?action=login')

            # 🔥 Aquí Django automáticamente verifica "password" contra la columna "contrasena_hash"
            if usuario.check_password(password):
                request.session.flush()

                request.session['usuario_id'] = usuario.id
                request.session['usuario_nombre'] = usuario.nombre
                request.session['usuario_nombre_completo'] = str(usuario)
                request.session['usuario_correo'] = usuario.correo
                request.session['usuario_rol'] = usuario.rol.nombre

                request.session.set_expiry(60 * 60 * 4)

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

    return render(request, 'pages/usuarios/perfil.html', {'usuario': usuario})