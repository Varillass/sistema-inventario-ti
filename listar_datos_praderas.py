#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_inventario_ti.settings')
django.setup()

from inventario.models import Sede, Area, Personal

def listar_datos_praderas():
    print("=== DATOS DE LA SEDE PRADERAS ===")
    
    # Buscar la sede PRADERAS
    sede_praderas = Sede.objects.filter(nombre='PRADERAS').first()
    
    if not sede_praderas:
        print("❌ No se encontró la sede PRADERAS")
        return
    
    print(f"✅ Sede encontrada: {sede_praderas.nombre} (ID: {sede_praderas.id})")
    print(f"   Estado: {'Activa' if sede_praderas.activo else 'Inactiva'}")
    print(f"   Dirección: {sede_praderas.direccion or 'No especificada'}")
    print(f"   Teléfono: {sede_praderas.telefono or 'No especificado'}")
    
    # Listar todas las áreas de PRADERAS
    print("\n📋 ÁREAS EN PRADERAS:")
    areas_praderas = Area.objects.filter(sede=sede_praderas, activo=True)
    
    if areas_praderas.exists():
        print(f"✅ Se encontraron {areas_praderas.count()} áreas activas:")
        for i, area in enumerate(areas_praderas, 1):
            print(f"   {i}. {area.nombre} (ID: {area.id})")
            print(f"      Descripción: {area.descripcion}")
            print(f"      Estado: {'Activa' if area.activo else 'Inactiva'}")
            
            # Contar personal en esta área
            personal_area = Personal.objects.filter(area=area, activo=True)
            print(f"      Personal asignado: {personal_area.count()} personas")
            print()
    else:
        print("❌ No se encontraron áreas activas en PRADERAS")
    
    # Listar todo el personal de PRADERAS (sin importar el área)
    print("👥 TODO EL PERSONAL EN PRADERAS:")
    personal_praderas = Personal.objects.filter(area__sede=sede_praderas, activo=True)
    
    if personal_praderas.exists():
        print(f"✅ Se encontraron {personal_praderas.count()} personas activas:")
        for i, persona in enumerate(personal_praderas, 1):
            print(f"   {i}. {persona.nombre} {persona.apellido} (ID: {persona.id})")
            print(f"      Área: {persona.area.nombre}")
            print(f"      Cargo: {persona.cargo}")
            print(f"      Email: {persona.email}")
            print(f"      Teléfono: {persona.telefono}")
            print(f"      Estado: {'Activo' if persona.activo else 'Inactivo'}")
            print()
    else:
        print("❌ No se encontró personal activo en PRADERAS")
    
    # Resumen final
    print("📊 RESUMEN:")
    print(f"   - Sede: {sede_praderas.nombre}")
    print(f"   - Áreas activas: {areas_praderas.count()}")
    print(f"   - Personal activo: {personal_praderas.count()}")
    
    # Verificar si hay datos para las APIs
    if areas_praderas.exists():
        print("\n✅ Las APIs deberían funcionar correctamente")
        print("   - API /api/areas-por-sede/ debería devolver áreas")
        if personal_praderas.exists():
            print("   - API /api/personal-por-area/ debería devolver personal")
        else:
            print("   - API /api/personal-por-area/ no devolverá personal (no hay personal activo)")
    else:
        print("\n❌ Las APIs no devolverán datos (no hay áreas activas)")
    
    print("\n✅ Listado completado.")

if __name__ == "__main__":
    listar_datos_praderas() 