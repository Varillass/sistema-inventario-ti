#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_inventario_ti.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

def debug_javascript():
    print("=== DEBUG DEL JAVASCRIPT ===")
    
    # Crear cliente de prueba
    client = Client()
    
    # Obtener usuario admin
    User = get_user_model()
    try:
        admin_user = User.objects.get(username='admin')
        client.force_login(admin_user)
        print("✅ Usuario admin autenticado")
    except User.DoesNotExist:
        print("❌ Usuario admin no encontrado")
        return
    
    # Obtener la página
    response = client.get('/productos/crear/')
    
    if response.status_code == 200:
        print("✅ Página accesible")
        content = response.content.decode('utf-8')
        
        # Verificar elementos clave del JavaScript
        print("\n🔍 VERIFICANDO ELEMENTOS DEL JAVASCRIPT:")
        
        # Verificar jQuery
        if 'jquery' in content.lower():
            print("✅ jQuery encontrado en el HTML")
        else:
            print("❌ jQuery NO encontrado en el HTML")
        
        # Verificar función waitForJQuery
        if 'waitForJQuery' in content:
            print("✅ Función waitForJQuery encontrada")
        else:
            print("❌ Función waitForJQuery NO encontrada")
        
        # Verificar función initializeApp
        if 'initializeApp' in content:
            print("✅ Función initializeApp encontrada")
        else:
            print("❌ Función initializeApp NO encontrada")
        
        # Verificar evento change de sede
        if "$('#sede').change" in content:
            print("✅ Evento change de sede encontrado")
        else:
            print("❌ Evento change de sede NO encontrado")
        
        # Verificar URL de la API
        if "/api/areas-por-sede/" in content:
            print("✅ URL de API áreas encontrada")
        else:
            print("❌ URL de API áreas NO encontrada")
        
        # Verificar headers CSRF
        if "X-CSRFToken" in content:
            print("✅ Headers CSRF encontrados")
        else:
            print("❌ Headers CSRF NO encontrados")
        
        # Verificar console.log
        if "console.log" in content:
            print("✅ Console.log encontrado (debugging activo)")
        else:
            print("❌ Console.log NO encontrado")
        
        # Verificar botón de prueba
        if "btnTestAPI" in content:
            print("✅ Botón de prueba encontrado")
        else:
            print("❌ Botón de prueba NO encontrado")
        
        print("\n📋 INSTRUCCIONES PARA DEBUGGING:")
        print("1. Abre tu navegador y ve a: http://127.0.0.1:8000/productos/crear/")
        print("2. Abre las herramientas de desarrollador (F12)")
        print("3. Ve a la pestaña 'Console'")
        print("4. Recarga la página (F5)")
        print("5. Verifica que aparezcan estos mensajes:")
        print("   - 'Script cargado'")
        print("   - '⏳ Esperando a que jQuery se cargue...'")
        print("   - '✅ jQuery está disponible'")
        print("   - '🚀 Inicializando aplicación...'")
        print("   - 'Document ready ejecutado'")
        print("6. Selecciona 'PRADERAS' en el dropdown de Sede")
        print("7. Verifica que aparezcan estos mensajes:")
        print("   - '🔄 Sede seleccionada: 2'")
        print("   - 'CSRF Token: ✅ Presente'")
        print("   - '🚀 Enviando petición para cargar áreas...'")
        print("   - '✅ Respuesta API áreas exitosa:'")
        print("   - '✅ Cargadas 4 áreas'")
        
        print("\n🔧 SI NO FUNCIONA:")
        print("- Verifica que no haya errores en la consola (en rojo)")
        print("- Asegúrate de estar autenticado")
        print("- Intenta limpiar la caché del navegador (Ctrl+F5)")
        print("- Verifica que el servidor esté ejecutándose")
        
    else:
        print(f"❌ Error al acceder a la página: {response.status_code}")
    
    print("\n✅ Debug completado.")

if __name__ == "__main__":
    debug_javascript() 