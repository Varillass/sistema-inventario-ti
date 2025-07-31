#!/usr/bin/env python
"""
Script para crear datos iniciales del sistema
"""

import os
import sys
import django

def main():
    """Crear datos iniciales usando Django"""
    try:
        # Configurar Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_inventario_ti.settings')
        django.setup()
        
        from inventario.models import Usuario, Categoria, TipoMovimiento, Sede, Area
        
        print("🚀 Creando datos iniciales del Sistema de Inventario TI...")
        print("=" * 50)
        
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
        else:
            print("✅ Usuario administrador ya existe")
        
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
        print("\n📋 Próximos pasos:")
        print("1. Ejecuta: python manage.py runserver")
        print("2. Accede a: http://localhost:8000")
        print("3. Inicia sesión con: admin / admin123")
        return True
        
    except Exception as e:
        print(f"❌ Error al crear datos iniciales: {e}")
        return False

if __name__ == "__main__":
    main() 