"""
Vistas para páginas estáticas: Sobre Nosotros, Contacto, Términos y Condiciones.
"""
from django.shortcuts import render


def handler404(request, exception):
    return render(request, '404.html', status=404)


def sobre_nosotros_view(request):
    stats = [
        {'valor': '20+', 'label': 'Años de historia'},
        {'valor': '500+', 'label': 'Eventos realizados'},
        {'valor': '2000', 'label': 'Capacidad de aforo'},
        {'valor': '50K+', 'label': 'Espectadores al año'},
    ]
    return render(request, 'pages/static/sobre_nosotros.html', {'stats': stats})


def contacto_view(request):
    """Redirige directamente a la vista de soporte del cliente."""
    from django.shortcuts import redirect
    return redirect('cliente_soporte')


def terminos_view(request):
    secciones = [
        {
            'titulo': 'Aceptación de los Términos',
            'contenido': (
                'Al acceder y utilizar el sistema de venta de entradas del Teatro al Aire Libre "Jaime Laredo", '
                'usted acepta estar sujeto a estos Términos y Condiciones. Si no está de acuerdo con alguna parte '
                'de estos términos, no podrá acceder al servicio.'
            ),
        },
        {
            'titulo': 'Compra de Entradas',
            'contenido': (
                'Las entradas adquiridas a través de nuestra plataforma son válidas únicamente para el evento, '
                'fecha y zona especificados. Cada entrada tiene un código QR único e intransferible. '
                'El Teatro se reserva el derecho de verificar la identidad del portador de la entrada. '
                'Las entradas no son reembolsables salvo en caso de cancelación del evento por parte del Teatro.'
            ),
        },
        {
            'titulo': 'Política de Cancelación y Reembolsos',
            'contenido': (
                'En caso de cancelación del evento por causas imputables al Teatro, se procederá al reembolso '
                'total del valor de las entradas en un plazo máximo de 15 días hábiles. '
                'No se realizarán reembolsos por inasistencia del comprador, llegada tardía o '
                'circunstancias ajenas al Teatro. Los cargos por servicio no son reembolsables.'
            ),
        },
        {
            'titulo': 'Uso del Sistema',
            'contenido': (
                'El usuario se compromete a utilizar el sistema de manera responsable y legal. '
                'Está prohibida la reventa de entradas a precios superiores al valor nominal. '
                'El Teatro se reserva el derecho de cancelar compras que considere fraudulentas '
                'o que violen estos términos, sin previo aviso y sin derecho a reembolso.'
            ),
        },
        {
            'titulo': 'Protección de Datos Personales',
            'contenido': (
                'Los datos personales proporcionados durante el registro y la compra serán tratados '
                'conforme a la legislación boliviana vigente en materia de protección de datos. '
                'La información será utilizada exclusivamente para la gestión de entradas y comunicaciones '
                'relacionadas con los eventos del Teatro. No compartiremos sus datos con terceros '
                'sin su consentimiento expreso.'
            ),
        },
        {
            'titulo': 'Responsabilidad',
            'contenido': (
                'El Teatro al Aire Libre "Jaime Laredo" no se hace responsable por pérdidas, robos o '
                'daños a personas o bienes dentro del recinto, salvo negligencia comprobada de nuestra parte. '
                'El Teatro se reserva el derecho de modificar la programación, artistas o condiciones '
                'del evento por causas de fuerza mayor, notificando a los compradores con la mayor '
                'anticipación posible.'
            ),
        },
        {
            'titulo': 'Modificaciones',
            'contenido': (
                'El Teatro se reserva el derecho de modificar estos Términos y Condiciones en cualquier momento. '
                'Los cambios entrarán en vigor inmediatamente después de su publicación en el sitio web. '
                'El uso continuado del servicio después de dichos cambios constituye la aceptación de los nuevos términos.'
            ),
        },
        {
            'titulo': 'Contacto',
            'contenido': (
                'Para cualquier consulta relacionada con estos Términos y Condiciones, puede contactarnos a través '
                'de nuestro formulario de contacto, por correo electrónico a info@teatrolapaz.bo, '
                'o llamando al +591 2 123-4567 en horario de atención.'
            ),
        },
    ]
    return render(request, 'pages/static/terminos.html', {'secciones': secciones})


def privacidad_view(request):
    secciones = [
        {
            'titulo': 'Información que Recopilamos',
            'contenido': (
                'Recopilamos información que usted nos proporciona directamente al registrarse, '
                'como nombre, apellido, correo electrónico, número de teléfono y documento de identidad. '
                'También recopilamos información de uso del sistema, como páginas visitadas, eventos consultados '
                'y transacciones realizadas, con el fin de mejorar nuestros servicios.'
            ),
        },
        {
            'titulo': 'Uso de la Información',
            'contenido': (
                'Utilizamos su información personal exclusivamente para: gestionar su cuenta y compras de entradas, '
                'enviar confirmaciones y notificaciones relacionadas con sus tickets, '
                'mejorar la experiencia de usuario en nuestra plataforma, '
                'y cumplir con obligaciones legales y fiscales. '
                'No utilizamos su información para fines publicitarios de terceros sin su consentimiento.'
            ),
        },
        {
            'titulo': 'Compartición de Datos',
            'contenido': (
                'No vendemos, alquilamos ni compartimos su información personal con terceros, '
                'salvo en los siguientes casos: cuando sea requerido por ley o autoridad competente, '
                'con proveedores de servicios que nos asisten en la operación del sistema '
                '(bajo estrictos acuerdos de confidencialidad), '
                'o con su consentimiento expreso previo.'
            ),
        },
        {
            'titulo': 'Seguridad de los Datos',
            'contenido': (
                'Implementamos medidas técnicas y organizativas para proteger su información personal '
                'contra acceso no autorizado, pérdida o alteración. '
                'Las contraseñas se almacenan de forma cifrada y nunca en texto plano. '
                'Sin embargo, ningún sistema es completamente infalible, por lo que le recomendamos '
                'usar contraseñas seguras y no compartirlas con terceros.'
            ),
        },
        {
            'titulo': 'Cookies y Sesiones',
            'contenido': (
                'Utilizamos cookies de sesión para mantener su estado de autenticación mientras navega '
                'por nuestra plataforma. Estas cookies son estrictamente necesarias para el funcionamiento '
                'del sistema y no se utilizan para rastreo publicitario. '
                'Al cerrar sesión, las cookies de sesión son eliminadas automáticamente.'
            ),
        },
        {
            'titulo': 'Derechos del Usuario',
            'contenido': (
                'Usted tiene derecho a: acceder a su información personal almacenada en nuestro sistema, '
                'solicitar la corrección de datos incorrectos o desactualizados, '
                'solicitar la eliminación de su cuenta y datos asociados, '
                'y oponerse al tratamiento de sus datos en determinadas circunstancias. '
                'Para ejercer estos derechos, contáctenos a través de nuestro sistema de soporte.'
            ),
        },
        {
            'titulo': 'Retención de Datos',
            'contenido': (
                'Conservamos su información personal mientras su cuenta esté activa o sea necesaria '
                'para prestarle nuestros servicios. Los registros de transacciones se conservan '
                'por el período mínimo requerido por la legislación boliviana vigente. '
                'Tras la eliminación de su cuenta, sus datos personales serán anonimizados o eliminados '
                'en un plazo máximo de 30 días hábiles.'
            ),
        },
        {
            'titulo': 'Cambios en esta Política',
            'contenido': (
                'Nos reservamos el derecho de actualizar esta Política de Privacidad en cualquier momento. '
                'Le notificaremos sobre cambios significativos mediante un aviso visible en nuestra plataforma. '
                'El uso continuado del servicio tras la publicación de cambios implica su aceptación. '
                'Le recomendamos revisar esta política periódicamente.'
            ),
        },
        {
            'titulo': 'Contacto',
            'contenido': (
                'Si tiene preguntas, inquietudes o solicitudes relacionadas con esta Política de Privacidad '
                'o el tratamiento de sus datos personales, puede contactarnos a través de nuestro sistema '
                'de soporte en línea, por correo electrónico a privacidad@teatrolapaz.bo, '
                'o llamando al +591 2 123-4567 en horario de atención.'
            ),
        },
    ]
    return render(request, 'pages/static/privacidad.html', {'secciones': secciones})
