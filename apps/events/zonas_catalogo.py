"""Catálogo oficial de zonas del Teatro al Aire Libre."""
from decimal import Decimal

from .models import Zona

ZONAS_TEATRO = (
    {
        'nombre': 'SUPER VIP',
        'tipo_zona': 'svip',
        'tipo_asignacion': 'asiento',
        'capacidad_base': 200,
        'codigo_color': '#A855F7',
        'orden_visual': 1,
        'precio_default': Decimal('200'),
        'field_precio': 'precio_super_vip',
        'field_capacidad': 'capacidad_super_vip',
    },
    {
        'nombre': 'VIP',
        'tipo_zona': 'vip',
        'tipo_asignacion': 'asiento',
        'capacidad_base': 300,
        'codigo_color': '#00AEEF',
        'orden_visual': 2,
        'precio_default': Decimal('300'),
        'field_precio': 'precio_vip',
        'field_capacidad': 'capacidad_vip',
    },
    {
        'nombre': 'PLATEA',
        'tipo_zona': 'platea',
        'tipo_asignacion': 'asiento',
        'capacidad_base': 500,
        'codigo_color': '#8B5CF6',
        'orden_visual': 3,
        'precio_default': Decimal('500'),
        'field_precio': 'precio_platea',
        'field_capacidad': 'capacidad_platea',
    },
    {
        'nombre': 'GENERAL',
        'tipo_zona': 'general',
        'tipo_asignacion': 'asiento',
        'capacidad_base': 1000,
        'codigo_color': '#64748B',
        'orden_visual': 4,
        'precio_default': Decimal('1000'),
        'field_precio': 'precio_general',
        'field_capacidad': 'capacidad_general',
    },
)


def sync_zonas_teatro():
    """Asegura que las 4 zonas del teatro existan con los datos correctos."""
    for spec in ZONAS_TEATRO:
        Zona.objects.update_or_create(
            nombre=spec['nombre'],
            defaults={
                'descripcion': f"Zona {spec['nombre']}",
                'tipo_zona': spec['tipo_zona'],
                'tipo_asignacion': spec['tipo_asignacion'],
                'codigo_color': spec['codigo_color'],
                'capacidad_base': spec['capacidad_base'],
                'orden_visual': spec['orden_visual'],
            },
        )


def zona_por_spec(spec):
    z = Zona.objects.filter(tipo_zona__iexact=spec['tipo_zona']).first()
    if z:
        return z
    return Zona.objects.filter(nombre__iexact=spec['nombre']).first()
