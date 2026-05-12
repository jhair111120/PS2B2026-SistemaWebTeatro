"""
Script para poblar todos los datos de catálogo necesarios en la BD.
Ejecutar con: python manage.py shell < setup_datos_iniciales.py
O directamente: python setup_datos_iniciales.py (con DJANGO_SETTINGS_MODULE configurado)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.tickets.models import CanalVenta, EstadoVenta, EstadoEntrada
from apps.payments.models import EstadoPago, MetodoPago
from apps.reservations.models import EstadoReserva
from apps.events.models import Zona, EstadoEvento
from apps.users.models import Rol

print("=" * 50)
print("CONFIGURANDO DATOS INICIALES")
print("=" * 50)

# ── ROLES ────────────────────────────────────────
roles = ['administrador', 'cliente', 'empleado', 'soporte']
for nombre in roles:
    obj, created = Rol.objects.get_or_create(nombre=nombre)
    print(f"{'[CREADO]' if created else '[OK]'} Rol: {nombre}")

# ── ESTADOS DE EVENTO ────────────────────────────
estados_evento = ['activo', 'finalizado', 'cancelado', 'borrador']
for nombre in estados_evento:
    from apps.events.models import EstadoEvento
    obj, created = EstadoEvento.objects.get_or_create(nombre=nombre)
    print(f"{'[CREADO]' if created else '[OK]'} EstadoEvento: {nombre}")

# ── ZONAS (4 zonas estándar del teatro) ──────────
zonas_data = [
    {
        'nombre': 'SUPER VIP',
        'descripcion': 'Mejor vista al escenario',
        'tipo_zona': 'zona',
        'tipo_asignacion': 'zona',
        'codigo_color': '#A855F7',
        'capacidad_base': 100,
        'orden_visual': 1,
    },
    {
        'nombre': 'VIP',
        'descripcion': 'Excelente vista',
        'tipo_zona': 'zona',
        'tipo_asignacion': 'zona',
        'codigo_color': '#00AEEF',
        'capacidad_base': 200,
        'orden_visual': 2,
    },
    {
        'nombre': 'PLATEA',
        'descripcion': 'Buena vista',
        'tipo_zona': 'zona',
        'tipo_asignacion': 'zona',
        'codigo_color': '#8B5CF6',
        'capacidad_base': 400,
        'orden_visual': 3,
    },
    {
        'nombre': 'GENERAL',
        'descripcion': 'Entrada estándar',
        'tipo_zona': 'zona',
        'tipo_asignacion': 'zona',
        'codigo_color': '#1E293B',
        'capacidad_base': 800,
        'orden_visual': 4,
    },
]

for z_data in zonas_data:
    nombre = z_data.pop('nombre')
    obj, created = Zona.objects.get_or_create(nombre=nombre, defaults=z_data)
    if not created:
        # Actualizar color y orden si ya existe
        Zona.objects.filter(nombre=nombre).update(
            codigo_color=z_data.get('codigo_color', obj.codigo_color),
            orden_visual=z_data.get('orden_visual', obj.orden_visual),
            descripcion=z_data.get('descripcion', obj.descripcion),
        )
    print(f"{'[CREADO]' if created else '[ACTUALIZADO]'} Zona: {nombre}")

# ── CANAL DE VENTA ───────────────────────────────
canales = ['web', 'ventanilla']
for nombre in canales:
    obj, created = CanalVenta.objects.get_or_create(nombre=nombre)
    print(f"{'[CREADO]' if created else '[OK]'} CanalVenta: {nombre}")

# ── ESTADO RESERVA ───────────────────────────────
estados_reserva = ['activa', 'confirmada', 'expirada', 'cancelada']
for nombre in estados_reserva:
    obj, created = EstadoReserva.objects.get_or_create(nombre=nombre)
    print(f"{'[CREADO]' if created else '[OK]'} EstadoReserva: {nombre}")

# ── ESTADO VENTA ─────────────────────────────────
estados_venta = ['emitida', 'anulada', 'reembolsada']
for nombre in estados_venta:
    obj, created = EstadoVenta.objects.get_or_create(nombre=nombre)
    print(f"{'[CREADO]' if created else '[OK]'} EstadoVenta: {nombre}")

# ── ESTADO ENTRADA ───────────────────────────────
estados_entrada = ['emitida', 'usada', 'cancelada']
for nombre in estados_entrada:
    obj, created = EstadoEntrada.objects.get_or_create(nombre=nombre)
    print(f"{'[CREADO]' if created else '[OK]'} EstadoEntrada: {nombre}")

# ── ESTADO PAGO ──────────────────────────────────
estados_pago = ['pendiente', 'pagado', 'rechazado', 'reembolsado']
for nombre in estados_pago:
    obj, created = EstadoPago.objects.get_or_create(nombre=nombre)
    print(f"{'[CREADO]' if created else '[OK]'} EstadoPago: {nombre}")

# ── MÉTODO DE PAGO ───────────────────────────────
metodos_pago = ['Tarjeta de Crédito', 'QR Bancario', 'Transferencia Bancaria']
for nombre in metodos_pago:
    obj, created = MetodoPago.objects.get_or_create(nombre=nombre)
    print(f"{'[CREADO]' if created else '[OK]'} MetodoPago: {nombre}")

# ── EVENTO DE PRUEBA ─────────────────────────────
from apps.events.models import Evento, EventoZona
import datetime

estado_activo = EstadoEvento.objects.get(nombre='activo')

evento, created = Evento.objects.get_or_create(
    nombre='Concierto Folklórico Nacional',
    defaults={
        'descripcion': 'Una noche mágica con lo mejor de la música folklórica boliviana bajo las estrellas del Teatro al Aire Libre.',
        'fecha_evento': datetime.date(2026, 8, 15),
        'hora_evento': datetime.time(19, 30),
        'lugar': 'Teatro al Aire Libre - La Paz',
        'imagen_url': None,
        'estado_evento': estado_activo,
    }
)
print(f"\n{'[CREADO]' if created else '[OK]'} Evento: {evento.nombre} (id={evento.id})")

# Asignar las 4 zonas al evento con precios
precios_zonas = {
    'SUPER VIP': 600,
    'VIP': 400,
    'PLATEA': 200,
    'GENERAL': 150,
}

for nombre_zona, precio in precios_zonas.items():
    zona = Zona.objects.get(nombre=nombre_zona)
    ez, created = EventoZona.objects.get_or_create(
        evento=evento,
        zona=zona,
        defaults={
            'precio_base': precio,
            'capacidad_evento': zona.capacidad_base,
            'nombre_display': nombre_zona,
            'limite_por_usuario': 4,
            'habilitada': True,
        }
    )
    if not created:
        ez.precio_base = precio
        ez.habilitada = True
        ez.nombre_display = nombre_zona
        ez.save()
    print(f"  {'[CREADO]' if created else '[ACTUALIZADO]'} EventoZona: {nombre_zona} → Bs. {precio}")

print("\n" + "=" * 50)
print("DATOS INICIALES CONFIGURADOS CORRECTAMENTE")
print("=" * 50)
print(f"\nEvento disponible en: /comprar-entrada/{evento.id}/")
print("Zonas del teatro: SUPER VIP, VIP, PLATEA, GENERAL")
