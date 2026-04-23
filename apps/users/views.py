import re
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from django.views.decorators.cache import never_cache # <--- ESTO EVITA EL CACHÉ AL CERRAR SESIÓN
from .models import Usuario, Rol

def signup_view(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        apellido = request.POST.get('apellido', '').strip()
        correo = request.POST.get('correo', '').strip()
        password = request.POST.get('password', '')
        telefono = request.POST.get('telefono', '').strip()

        if not re.match(r"^[A-ZÁÉÍÓÚÑ][a-zA-ZáéíóúñÁÉÍÓÚÑ\s]*$", nombre) or not re.match(r"^[A-ZÁÉÍÓÚÑ][a-zA-ZáéíóúñÁÉÍÓÚÑ\s]*$", apellido):
            messages.error(request, "El nombre y apellido deben comenzar con mayúscula y no contener números ni símbolos.")
            return redirect('/?action=signup')

        if not re.match(r"^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,10}$", correo):
            messages.error(request, "El formato del correo no es válido.")
            return redirect('/?action=signup')

        if telefono and not re.match(r"^[0-9]{8}$", telefono):
            messages.error(request, "El teléfono debe contener exactamente 8 números.")
            return redirect('/?action=signup')

        if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&.-])[A-Za-z\d@$!%*?&.-]{8,}$", password):
            messages.error(request, "La contraseña no cumple con los requisitos de seguridad.")
            return redirect('/?action=signup')

        if Usuario.objects.filter(correo=correo).exists():
            messages.error(request, "Este correo electrónico ya está registrado.")
            return redirect('/?action=signup')
            
        if telefono and Usuario.objects.filter(telefono=telefono).exists():
            messages.error(request, "Este número de teléfono ya está siendo utilizado.")
            return redirect('/?action=signup')

        hashed_password = make_password(password)

        try:
            rol_cliente = Rol.objects.get(nombre='cliente')
        except Rol.DoesNotExist:
            messages.error(request, "Error interno: El rol 'cliente' no está configurado.")
            return redirect('/?action=signup')

        try:
            Usuario.objects.create(
                nombre=nombre,
                apellido=apellido,
                correo=correo,
                telefono=telefono,
                contrasena_hash=hashed_password,
                rol=rol_cliente,
                activo=True,
                fecha_creacion=timezone.now()
            )
            messages.success(request, "¡Cuenta creada con éxito! Por favor, inicia sesión.")
            return redirect('/?action=login')
        except Exception as e:
            messages.error(request, "Ocurrió un error al registrarte.")
            return redirect('/?action=signup')

    return redirect('/')

def login_view(request):
    if request.method == 'POST':
        correo_form = request.POST.get('correo')
        password_form = request.POST.get('password')

        try:
            usuario = Usuario.objects.get(correo=correo_form)

            if check_password(password_form, usuario.contrasena_hash):
                request.session['usuario_id'] = usuario.id
                request.session['usuario_primer_nombre'] = usuario.nombre.split()[0]
                request.session['usuario_nombre_completo'] = f"{usuario.nombre} {usuario.apellido}"
                request.session['usuario_correo'] = usuario.correo
                request.session['usuario_rol'] = usuario.rol.nombre
                
                messages.success(request, f"¡Bienvenido de nuevo, {usuario.nombre.split()[0]}!")
                return redirect('/')
            else:
                messages.error(request, "Contraseña incorrecta.")
                return redirect('/?action=login')
        except Usuario.DoesNotExist:
            messages.error(request, "El correo ingresado no está registrado.")
            return redirect('/?action=login')

    return redirect('/')

def logout_view(request):
    request.session.flush()
    messages.success(request, "Has cerrado sesión correctamente.")
    return redirect('/')

# --- VISTA PERFIL ---
@never_cache # <--- BLOQUEA QUE EL NAVEGADOR GUARDE ESTA PÁGINA EN EL HISTORIAL "ATRÁS"
def perfil_view(request):
    if 'usuario_id' not in request.session:
        messages.error(request, "Debes iniciar sesión para acceder a tu perfil.")
        return redirect('/?action=login')

    try:
        usuario_actual = Usuario.objects.get(id=request.session['usuario_id'])
    except Usuario.DoesNotExist:
        request.session.flush()
        return redirect('/')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_profile':
            nombre = request.POST.get('nombre', '').strip()
            apellido = request.POST.get('apellido', '').strip()
            correo = request.POST.get('correo', '').strip()
            telefono = request.POST.get('telefono', '').strip()
            dni = request.POST.get('dni', '').strip()

            if correo != usuario_actual.correo and Usuario.objects.filter(correo=correo).exists():
                messages.error(request, "Ese correo ya está siendo utilizado por otra cuenta.")
                return redirect('perfil')

            usuario_actual.nombre = nombre
            usuario_actual.apellido = apellido
            usuario_actual.correo = correo
            usuario_actual.telefono = telefono
            usuario_actual.dni = dni
            usuario_actual.save()

            request.session['usuario_primer_nombre'] = nombre.split()[0]
            request.session['usuario_nombre_completo'] = f"{nombre} {apellido}"
            request.session['usuario_correo'] = correo

            messages.success(request, "Tus datos personales han sido actualizados con éxito.")
            return redirect('perfil')

        elif action == 'update_password':
            current_password = request.POST.get('current_password', '')
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')

            if not check_password(current_password, usuario_actual.contrasena_hash):
                messages.error(request, "La contraseña actual es incorrecta.")
            elif new_password != confirm_password:
                messages.error(request, "Las nuevas contraseñas no coinciden.")
            elif not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&.-])[A-Za-z\d@$!%*?&.-]{8,}$", new_password):
                messages.error(request, "La nueva contraseña debe tener 8 caracteres, 1 mayúscula, 1 número y 1 símbolo.")
            else:
                usuario_actual.contrasena_hash = make_password(new_password)
                usuario_actual.save()
                messages.success(request, "Tu contraseña ha sido actualizada correctamente.")
            
            return redirect('perfil')

    contexto = { 'usuario': usuario_actual }
    # Asegúrate de cambiar esta ruta abajo si mueves el perfil.html a pages/usuarios/perfil.html
    return render(request, 'pages/usuarios/perfil.html', contexto)