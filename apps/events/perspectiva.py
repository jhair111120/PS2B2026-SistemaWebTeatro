"""URLs de imágenes de perspectiva desde el asiento, por zona del teatro."""
from django.templatetags.static import static

# Prefijo de archivos en static/img/ ({prefix}_izquierda|medio|derecha.png)
_PREFIX_POR_TIPO = {
    'svip': 'svip',
    'vip': 'svip',
    'platea': 'gen',
    'general': 'gen',
}

_PREFIX_POR_NOMBRE = {
    'SUPER VIP': 'svip',
    'VIP': 'svip',
    'PLATEA': 'gen',
    'GENERAL': 'gen',
}


def _prefix_para_zona(zona):
    tipo = (zona.tipo_zona or '').strip().lower()
    if tipo in _PREFIX_POR_TIPO:
        return _PREFIX_POR_TIPO[tipo]
    nombre = (zona.nombre or '').strip().upper()
    if 'SUPER' in nombre and 'VIP' in nombre:
        return 'svip'
    return _PREFIX_POR_NOMBRE.get(nombre, 'gen')


def perspectiva_imagenes_para_zona(zona):
    """
    Devuelve dict {izquierda, medio, derecha} con rutas estáticas
    para todas las zonas del teatro.
    """
    if not zona:
        return None

    prefix = _prefix_para_zona(zona)
    return {
        'izquierda': static(f'img/{prefix}_izquierda.png'),
        'medio': static(f'img/{prefix}_medio.png'),
        'derecha': static(f'img/{prefix}_derecha.png'),
    }
