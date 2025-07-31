#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_inventario_ti.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from inventario.models import Sede, Area, Personal, Categoria

def debug_template():
    print("=== DEBUG DEL TEMPLATE CREAR PRODUCTO ===")
    
    # Verificar datos en la base de datos
    print("\n1. VERIFICANDO DATOS EN LA BASE DE DATOS:")
    
    # Contar sedes
    sedes_count = Sede.objects.filter(activo=True).count()
    print(f"   - Sedes activas: {sedes_count}")
    
    # Contar áreas
    areas_count = Area.objects.filter(activo=True).count()
    print(f"   - Áreas activas: {areas_count}")
    
    # Contar personal
    personal_count = Personal.objects.filter(activo=True).count()
    print(f"   - Personal activo: {personal_count}")
    
    # Contar categorías
    categorias_count = Categoria.objects.count()
    print(f"   - Categorías: {categorias_count}")
    
    # Detalles de PRADERAS
    sede_praderas = Sede.objects.filter(nombre='PRADERAS').first()
    if sede_praderas:
        print(f"\n   - Sede PRADERAS (ID: {sede_praderas.id}):")
        areas_praderas = Area.objects.filter(sede=sede_praderas, activo=True)
        print(f"     * Áreas: {areas_praderas.count()}")
        for area in areas_praderas:
            personal_area = Personal.objects.filter(area=area, activo=True)
            print(f"       - {area.nombre}: {personal_area.count()} personas")
    
    # Crear cliente de prueba
    client = Client()
    
    # Obtener usuario admin
    User = get_user_model()
    try:
        admin_user = User.objects.get(username='admin')
        client.force_login(admin_user)
        print("\n✅ Usuario admin autenticado")
    except User.DoesNotExist:
        print("\n❌ Usuario admin no encontrado")
        return
    
    # Probar acceso a la página
    print("\n2. PROBANDO ACCESO A LA PÁGINA:")
    response = client.get('/productos/crear/')
    
    print(f"   - Status code: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✅ Página accesible")
        
        # Verificar contenido del template
        content = response.content.decode('utf-8')
        
        # Buscar elementos específicos en el HTML
        if 'PRADERAS' in content:
            print("   ✅ Sede PRADERAS encontrada en el HTML")
        else:
            print("   ❌ Sede PRADERAS NO encontrada en el HTML")
        
        if 'Seleccione una sede' in content:
            print("   ✅ Dropdown de sede encontrado")
        else:
            print("   ❌ Dropdown de sede NO encontrado")
        
        if 'Seleccione un área' in content:
            print("   ✅ Dropdown de área encontrado")
        else:
            print("   ❌ Dropdown de área NO encontrado")
        
        if 'Personal Asignado' in content:
            print("   ✅ Campo Personal Asignado encontrado")
        else:
            print("   ❌ Campo Personal Asignado NO encontrado")
        
        # Verificar si hay JavaScript
        if 'api/areas-por-sede' in content:
            print("   ✅ JavaScript para cargar áreas encontrado")
        else:
            print("   ❌ JavaScript para cargar áreas NO encontrado")
        
        if 'api/personal-por-area' in content:
            print("   ✅ JavaScript para cargar personal encontrado")
        else:
            print("   ❌ JavaScript para cargar personal NO encontrado")
        
        # Verificar jQuery
        if 'jquery' in content.lower():
            print("   ✅ jQuery encontrado")
        else:
            print("   ❌ jQuery NO encontrado")
        
    else:
        print(f"   ❌ Error al acceder a la página: {response.status_code}")
    
    # Probar APIs directamente
    print("\n3. PROBANDO APIs:")
    
    if sede_praderas:
        # API de áreas por sede
        print("   - Probando API áreas por sede...")
        import json
        response = client.post('/api/areas-por-sede/', 
                              data=json.dumps({'sede_id': sede_praderas.id}),
                              content_type='application/json')
        
        if response.status_code == 200:
            data = json.loads(response.content)
            areas_count = len(data.get('areas', []))
            print(f"     ✅ API áreas por sede exitosa ({areas_count} áreas)")
            for area in data.get('areas', []):
                print(f"       - {area['nombre']} (ID: {area['id']})")
        else:
            print(f"     ❌ Error en API áreas por sede: {response.status_code}")
            print(f"       Respuesta: {response.content}")
    
    print("\n✅ Debug completado.")

if __name__ == "__main__":
    debug_template() 