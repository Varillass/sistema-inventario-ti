#!/usr/bin/env python
"""
Script para configurar la base de datos MySQL y crear datos iniciales
"""

import mysql.connector
from mysql.connector import Error
import os
import sys
import django
from django.conf import settings

def create_database():
    """Crear la base de datos si no existe"""
    try:
        print("🔌 Conectando a MySQL...")
        # Conectar a MySQL sin especificar base de datos
        connection = mysql.connector.connect(
            host='181.224.226.142',
            user='afrodita',
            password='Zxasqw12@@@',
            port=3306
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Verificar si la base de datos ya existe
            cursor.execute("SHOW DATABASES LIKE 'inventario_ti'")
            db_exists = cursor.fetchone()
            
            if db_exists:
                print("✅ Base de datos 'inventario_ti' ya existe")
            else:
                # Crear la base de datos
                cursor.execute("CREATE DATABASE inventario_ti CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                print("✅ Base de datos 'inventario_ti' creada exitosamente")
            
            cursor.close()
            connection.close()
            
    except Error as e:
        print(f"❌ Error al conectar a MySQL: {e}")
        print("\n📋 Posibles soluciones:")
        print("1. Verifica que MySQL esté ejecutándose en el servidor")
        print("2. Verifica las credenciales en settings.py")
        print("3. Asegúrate de que el usuario tenga permisos para crear bases de datos")
        print("4. Si usas un servidor local, cambia la configuración en settings.py")
        print("\n🔧 Para usar SQLite (más simple para desarrollo):")
        print("   Modifica DATABASES en settings.py para usar 'django.db.backends.sqlite3'")
        return False
    
    return True

def test_database_connection():
    """Probar la conexión a la base de datos configurada"""
    try:
        print("🔍 Probando conexión a la base de datos...")
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_inventario_ti.settings')
        django.setup()
        
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result:
                print("✅ Conexión a la base de datos exitosa")
                return True
    except Exception as e:
        print(f"❌ Error al conectar a la base de datos: {e}")
        return False

def check_dependencies():
    """Verificar que las dependencias estén instaladas"""
    try:
        import mysql.connector
        print("✅ mysql-connector-python está instalado")
    except ImportError:
        print("❌ Error: mysql-connector-python no está instalado")
        print("   Instala con: pip install mysql-connector-python")
        return False
    
    try:
        import django
        print("✅ Django está instalado")
    except ImportError:
        print("❌ Error: Django no está instalado")
        print("   Instala con: pip install django")
        return False
    
    return True

def create_initial_data():
    """Crear datos iniciales usando Django"""
    try:
        # Configurar Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_inventario_ti.settings')
        
        # Configurar zona horaria
        os.environ.setdefault('TZ', 'America/Bogota')
        
        django.setup()
        
        from inventario.models import Usuario, Categoria, TipoMovimiento, Sede, Area
        
        # Crear superusuario si no existe
        if not Usuario.objects.filter(username='admin').exists():
            admin_user = Usuario.objects.create_user(
                username='admin',
                email='admin@sistema.com',
                password='admin123',
                first_name='Administrador',
                last_name='Sistema',
                rol='admin',
                is_staff=True,
                is_superuser=True
            )
            print("✅ Usuario administrador creado:")
            print("   Usuario: admin")
            print("   Contraseña: admin123")
        
        # Crear categorías iniciales
        categorias_data = [
            {'nombre': 'Computadoras', 'descripcion': 'Equipos de cómputo y laptops'},
            {'nombre': 'Periféricos', 'descripcion': 'Teclados, mouse, monitores, etc.'},
            {'nombre': 'Redes', 'descripcion': 'Switches, routers, cables de red'},
            {'nombre': 'Software', 'descripcion': 'Licencias y programas informáticos'},
            {'nombre': 'Almacenamiento', 'descripcion': 'Discos duros, SSDs, memorias USB'},
            {'nombre': 'Impresoras', 'descripcion': 'Impresoras y consumibles'},
            {'nombre': 'Servidores', 'descripcion': 'Servidores y equipos de respaldo'},
            {'nombre': 'Otros', 'descripcion': 'Otros equipos y accesorios'},
        ]
        
        for cat_data in categorias_data:
            categoria, created = Categoria.objects.get_or_create(
                nombre=cat_data['nombre'],
                defaults=cat_data
            )
            if created:
                print(f"✅ Categoría '{categoria.nombre}' creada")
        
        # Crear tipos de movimiento iniciales
        tipos_movimiento_data = [
            {'nombre': 'Entrada por Compra', 'descripcion': 'Entrada de productos por compra', 'es_entrada': True},
            {'nombre': 'Entrada por Donación', 'descripcion': 'Entrada de productos por donación', 'es_entrada': True},
            {'nombre': 'Entrada por Devolución', 'descripcion': 'Entrada de productos por devolución', 'es_entrada': True},
            {'nombre': 'Salida por Uso', 'descripcion': 'Salida de productos por uso interno', 'es_entrada': False},
            {'nombre': 'Salida por Venta', 'descripcion': 'Salida de productos por venta', 'es_entrada': False},
            {'nombre': 'Salida por Daño', 'descripcion': 'Salida de productos por daño', 'es_entrada': False},
            {'nombre': 'Ajuste de Inventario', 'descripcion': 'Ajuste manual de inventario', 'es_entrada': True},
        ]
        
        for tm_data in tipos_movimiento_data:
            tipo_mov, created = TipoMovimiento.objects.get_or_create(
                nombre=tm_data['nombre'],
                defaults=tm_data
            )
            if created:
                print(f"✅ Tipo de movimiento '{tipo_mov.nombre}' creado")
        
        # Crear sede por defecto
        sede_default, created = Sede.objects.get_or_create(
            nombre='Sede Principal',
            defaults={
                'direccion': 'Dirección principal de la empresa',
                'telefono': 'N/A'
            }
        )
        if created:
            print(f"✅ Sede '{sede_default.nombre}' creada")
        
        # Crear área por defecto
        area_default, created = Area.objects.get_or_create(
            nombre='Área General',
            sede=sede_default,
            defaults={
                'descripcion': 'Área general de la empresa'
            }
        )
        if created:
            print(f"✅ Área '{area_default.nombre}' creada")
        
        print("\n🎉 Datos iniciales creados exitosamente!")
        return True
        
    except Exception as e:
        print(f"❌ Error al crear datos iniciales: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Configurando Sistema de Inventario TI...")
    print("=" * 50)
    
    # Verificar dependencias
    if not check_dependencies():
        print("\n❌ Faltan dependencias necesarias")
        return
    
    # Crear base de datos
    if create_database():
        print("\n📊 Base de datos configurada correctamente")
        
        # Probar conexión
        if test_database_connection():
            # Crear datos iniciales
            if create_initial_data():
                print("\n✅ Configuración completada exitosamente!")
                print("\n📋 Próximos pasos:")
                print("1. Ejecuta: python manage.py migrate")
                print("2. Ejecuta: python manage.py runserver")
                print("3. Accede a: http://localhost:8000")
                print("4. Inicia sesión con: admin / admin123")
                print("\n⚠️  Nota: Si tienes problemas con las migraciones,")
                print("   ejecuta: python manage.py makemigrations")
            else:
                print("\n❌ Error al crear datos iniciales")
        else:
            print("\n❌ Error al conectar a la base de datos configurada")
    else:
        print("\n❌ Error al configurar la base de datos")

if __name__ == "__main__":
    main() 