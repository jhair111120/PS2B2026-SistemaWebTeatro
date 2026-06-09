"""
Script para configurar las 4 zonas con asientos numerados.
Capacidades:
  SUPER VIP : 200 personas  → 5 filas  × 40 asientos
  VIP       : 300 personas  → 6 filas  × 50 asientos
  PLATEA    : 500 personas  → 10 filas × 50 asientos
  GENERAL   : 1000 personas → 10 filas × 100 asientos

Ejecutar: .\\venv\\Scripts\\python.exe setup_asientos.py
"""
import os
import django
import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import transaction
from apps.events.models import Zona, Asiento, Evento, EventoZona, EventoAsiento, EstadoEvento
from apps.tickets.models import CanalVenta, EstadoVenta, EstadoEntrada
from apps.payments.models import EstadoPago, MetodoPago
from apps.reservations.models import EstadoReserva
from apps.support.models import Soporte
from apps.tickets.models import Venta, Entrada
from apps.payments.models import Pago
from apps.reservations.models import Reserva, DetalleReserva

with transaction.atomic():
    # ── Limpiar en orden correcto ────────────────────────────────
    print("Limpiando datos anteriores...")
    try:
        Soporte.objects.all().delete()
    except Exception:
        pass
    Entrada.objects.all().delete()
    Venta.objects.all().delete()
    Pago.objects.all().delete()
    DetalleReserva.objects.all().delete()
    Reserva.objects.all().delete()
    EventoAsiento.objects.all().delete()
    EventoZona.objects.all().delete()
    Asiento.objects.all().delete()
    Evento.objects.all().delete()
    Zona.objects.all().delete()
    print("Limpieza completa.\n")

    # ── Definición de zonas ──────────────────────────────────────
    # filas: lista de letras de fila
    # cols:  asientos por fila (numerados del 1 al N)
    ZONAS = [
        dict(
            nombre='SUPER VIP',
            descripcion='Mejor vista al escenario',
            tipo_zona='svip',
            tipo_asignacion='asiento',
            codigo_color='#A855F7',
            capacidad_base=200,
            orden_visual=1,
            filas=['A', 'B', 'C', 'D', 'E'],
            cols=40,
            precio=600,
        ),
        dict(
            nombre='VIP',
            descripcion='Excelente vista',
            tipo_zona='vip',
            tipo_asignacion='asiento',
            codigo_color='#00AEEF',
            capacidad_base=300,
            orden_visual=2,
            filas=['A', 'B', 'C', 'D', 'E', 'F'],
            cols=50,
            precio=400,
        ),
        dict(
            nombre='PLATEA',
            descripcion='Buena vista',
            tipo_zona='platea',
            tipo_asignacion='asiento',
            codigo_color='#8B5CF6',
            capacidad_base=500,
            orden_visual=3,
            filas=['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'],
            cols=50,
            precio=200,
        ),
        dict(
            nombre='GENERAL',
            descripcion='Entrada estandar',
            tipo_zona='general',
            tipo_asignacion='asiento',
            codigo_color='#64748B',
            capacidad_base=1000,
            orden_visual=4,
            filas=['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'],
            cols=100,
            precio=150,
        ),
    ]

    zonas_map = {}
    for zd in ZONAS:
        filas  = zd.pop('filas')
        cols   = zd.pop('cols')
        precio = zd.pop('precio')

        zona = Zona.objects.create(**zd)
        zonas_map[zona.nombre] = (zona, filas, cols, precio)
        print(f"[ZONA] {zona.nombre} (id={zona.id})")

        # Asientos numerados del 1 al cols
        bulk = [
            Asiento(zona=zona, fila=f, numero=n)
            for f in filas
            for n in range(1, cols + 1)
        ]
        Asiento.objects.bulk_create(bulk)
        print(f"  -> {len(bulk)} asientos ({len(filas)} filas × {cols} cols)")

    # ── Crear eventos de ejemplo ─────────────────────────────────
    estado_activo, _ = EstadoEvento.objects.get_or_create(nombre='activo')

    eventos_data = [
        dict(
            nombre='Concierto Folklorico Nacional',
            descripcion='Una noche magica con lo mejor de la musica folklorica boliviana.',
            fecha_evento=datetime.date(2026, 8, 15),
            hora_evento=datetime.time(19, 30),
            lugar='Teatro al Aire Libre - La Paz',
            imagen_url='https://images.unsplash.com/photo-1501386761578-eaa54b4e9f5e?w=800',
        ),
        dict(
            nombre='Festival de Danza Contemporanea',
            descripcion='Los mejores grupos de danza del pais en un espectaculo unico.',
            fecha_evento=datetime.date(2026, 9, 20),
            hora_evento=datetime.time(20, 0),
            lugar='Teatro al Aire Libre - La Paz',
            imagen_url='https://images.unsplash.com/photo-1547153760-18fc86324498?w=800',
        ),
        dict(
            nombre='Noche de Opera Boliviana',
            descripcion='Una velada de opera con las mejores voces del pais.',
            fecha_evento=datetime.date(2026, 10, 10),
            hora_evento=datetime.time(19, 0),
            lugar='Teatro al Aire Libre - La Paz',
            imagen_url='https://images.unsplash.com/photo-1507676184212-d03ab07a01bf?w=800',
        ),
    ]

    for ev_data in eventos_data:
        evento = Evento.objects.create(estado_evento=estado_activo, **ev_data)
        print(f"\n[EVENTO] '{evento.nombre}' (id={evento.id})")

        for nombre, (zona, filas, cols, precio) in zonas_map.items():
            ez = EventoZona.objects.create(
                evento=evento,
                zona=zona,
                precio_base=precio,
                capacidad_evento=zona.capacidad_base,
                nombre_display=nombre,
                limite_por_usuario=10,   # ← máximo 10 asientos por compra
                habilitada=True,
            )
            asientos = list(Asiento.objects.filter(zona=zona))
            ea_bulk = [
                EventoAsiento(
                    evento_zona=ez,
                    asiento=a,
                    estado=EventoAsiento.Estado.DISPONIBLE,
                )
                for a in asientos
            ]
            EventoAsiento.objects.bulk_create(ea_bulk)
            print(f"  [EZ] {nombre} Bs.{precio} cap={zona.capacidad_base} "
                  f"limite=10 -> {len(ea_bulk)} EventoAsiento")

    # ── Catálogos ────────────────────────────────────────────────
    for n in ['web', 'ventanilla']:
        CanalVenta.objects.get_or_create(nombre=n)
    for n in ['activa', 'confirmada', 'expirada', 'cancelada']:
        EstadoReserva.objects.get_or_create(nombre=n)
    for n in ['emitida', 'anulada', 'reembolsada']:
        EstadoVenta.objects.get_or_create(nombre=n)
    for n in ['emitida', 'usada', 'cancelada']:
        EstadoEntrada.objects.get_or_create(nombre=n)
    for n in ['pendiente', 'pagado', 'rechazado']:
        EstadoPago.objects.get_or_create(nombre=n)
    for n in ['Tarjeta de Credito', 'QR Bancario', 'Transferencia']:
        MetodoPago.objects.get_or_create(nombre=n)
    print("\nCatalogos OK")

print("\n=== RESUMEN FINAL ===")
print(f"Zonas:          {Zona.objects.count()}")
print(f"Asientos:       {Asiento.objects.count()}")
print(f"Eventos:        {Evento.objects.count()}")
print(f"EventoZona:     {EventoZona.objects.count()}")
print(f"EventoAsiento:  {EventoAsiento.objects.count()}")
print(f"\nCapacidades:")
for ez in EventoZona.objects.select_related('zona', 'evento').filter(evento__nombre__icontains='Folklorico'):
    print(f"  {ez.zona.nombre}: {ez.capacidad_evento} asientos, limite={ez.limite_por_usuario}")
