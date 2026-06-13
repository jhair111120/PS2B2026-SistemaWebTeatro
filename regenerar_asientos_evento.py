"""
Script para regenerar EventoAsiento para eventos existentes que no tengan asientos.
Ejecutar: python regenerar_asientos_evento.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.events.models import Evento, EventoZona, EventoAsiento, Asiento

print("Buscando eventos sin asientos...")
eventos = Evento.objects.all()

for evento in eventos:
    print(f"\nEvento: {evento.nombre} (ID: {evento.id})")
    
    # Verificar si tiene EventoZona
    evento_zonas = EventoZona.objects.filter(evento=evento)
    if not evento_zonas:
        print("  ❌ No tiene EventoZona configuradas")
        continue
    
    print(f"  ✓ Tiene {evento_zonas.count()} EventoZona configuradas")
    
    for ez in evento_zonas:
        # Verificar si tiene EventoAsiento
        ea_count = EventoAsiento.objects.filter(evento_zona=ez).count()
        
        if ea_count == 0:
            print(f"    ❌ Zona {ez.zona.nombre}: No tiene EventoAsiento - Generando...")
            
            # Obtener todos los asientos de la zona
            asientos = Asiento.objects.filter(zona=ez.zona)
            
            if not asientos:
                print(f"      ❌ La zona {ez.zona.nombre} no tiene asientos base")
                continue
            
            # Crear EventoAsiento en bulk
            ea_bulk = [
                EventoAsiento(
                    evento_zona=ez,
                    asiento=a,
                    estado=EventoAsiento.Estado.DISPONIBLE,
                )
                for a in asientos
            ]
            
            if ea_bulk:
                EventoAsiento.objects.bulk_create(ea_bulk)
                print(f"      ✓ Se generaron {len(ea_bulk)} EventoAsiento para {ez.zona.nombre}")
        else:
            print(f"    ✓ Zona {ez.zona.nombre}: Ya tiene {ea_count} EventoAsiento")

print("\n=== RESUMEN FINAL ===")
print(f"Total Eventos: {Evento.objects.count()}")
print(f"Total EventoZona: {EventoZona.objects.count()}")
print(f"Total EventoAsiento: {EventoAsiento.objects.count()}")

print("\n✓ Script completado. Los eventos ahora deberían tener asientos disponibles.")
