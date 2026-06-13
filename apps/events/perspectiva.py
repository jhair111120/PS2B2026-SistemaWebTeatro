"""URLs de imágenes de perspectiva desde el asiento, por zona del teatro."""
from django.templatetags.static import static


def perspectiva_imagenes_para_zona(zona):
    """
    Devuelve dict {izquierda, medio, derecha} con rutas estáticas,
    o None si la zona no tiene vista previa (VIP, PLATEA, etc.).
    """
    if not zona:
        return None

    nombre = (zona.nombre or '').strip().upper()
    tipo = (zona.tipo_zona or '').strip().lower()

    # SUPER VIP (cuidado: no confundir con VIP solo)
    es_super_vip = tipo == 'svip' or ('SUPER' in nombre and 'VIP' in nombre)
    es_general = tipo == 'general' or nombre == 'GENERAL'

    if es_super_vip:
        prefix = 'svip'
    elif es_general:
        prefix = 'gen'
    else:
        return None

    return {
        'izquierda': static(f'img/{prefix}_izquierda.png'),
        'medio': static(f'img/{prefix}_medio.png'),
        'derecha': static(f'img/{prefix}_derecha.png'),
    }
