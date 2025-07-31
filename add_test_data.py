#!/usr/bin/env python
"""
Script para agregar datos de prueba
"""

import os
import sys
import django

def main():
    """Agregar datos de prueba"""
    try:
        # Configurar Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_inventario_ti.settings')
        django.setup()
        
        from inventario.models import Categoria, Producto
        
        print("🔧 Agregando datos de prueba...")
        print("=" * 50)
        
        # Obtener categorías existentes
        categorias = list(Categoria.objects.all())
        
        if not categorias:
            print("❌ No hay categorías disponibles. Ejecuta primero create_initial_data.py")
            return False
        
        # Productos de prueba por categoría
        productos_prueba = {
            'Computadoras': [
                {'nombre': 'Laptop HP Pavilion', 'codigo': 'LAP001', 'marca': 'HP', 'modelo': 'Pavilion', 'cantidad': 5, 'precio_unitario': 1200.00},
                {'nombre': 'Desktop Dell OptiPlex', 'codigo': 'DESK001', 'marca': 'Dell', 'modelo': 'OptiPlex', 'cantidad': 3, 'precio_unitario': 800.00},
                {'nombre': 'Laptop Lenovo ThinkPad', 'codigo': 'LAP002', 'marca': 'Lenovo', 'modelo': 'ThinkPad', 'cantidad': 4, 'precio_unitario': 1500.00},
            ],
            'Periféricos': [
                {'nombre': 'Teclado Mecánico', 'codigo': 'TEC001', 'marca': 'Logitech', 'modelo': 'G Pro', 'cantidad': 10, 'precio_unitario': 120.00},
                {'nombre': 'Mouse Inalámbrico', 'codigo': 'MOUSE001', 'marca': 'Microsoft', 'modelo': 'Wireless', 'cantidad': 15, 'precio_unitario': 45.00},
                {'nombre': 'Monitor 24"', 'codigo': 'MON001', 'marca': 'Samsung', 'modelo': '24" LED', 'cantidad': 8, 'precio_unitario': 200.00},
            ],
            'Redes': [
                {'nombre': 'Switch 24 Puertos', 'codigo': 'SW001', 'marca': 'Cisco', 'modelo': 'Catalyst', 'cantidad': 2, 'precio_unitario': 500.00},
                {'nombre': 'Router WiFi', 'codigo': 'ROUTER001', 'marca': 'TP-Link', 'modelo': 'Archer', 'cantidad': 3, 'precio_unitario': 80.00},
            ],
            'Software': [
                {'nombre': 'Office 365', 'codigo': 'SOFT001', 'marca': 'Microsoft', 'modelo': 'Office 365', 'cantidad': 20, 'precio_unitario': 150.00},
                {'nombre': 'Adobe Creative Suite', 'codigo': 'SOFT002', 'marca': 'Adobe', 'modelo': 'Creative Suite', 'cantidad': 5, 'precio_unitario': 500.00},
            ],
            'Almacenamiento': [
                {'nombre': 'SSD 500GB', 'codigo': 'SSD001', 'marca': 'Samsung', 'modelo': '870 EVO', 'cantidad': 12, 'precio_unitario': 80.00},
                {'nombre': 'HDD 1TB', 'codigo': 'HDD001', 'marca': 'Western Digital', 'modelo': 'Blue', 'cantidad': 8, 'precio_unitario': 50.00},
            ],
            'Impresoras': [
                {'nombre': 'Impresora Láser', 'codigo': 'IMP001', 'marca': 'HP', 'modelo': 'LaserJet', 'cantidad': 4, 'precio_unitario': 300.00},
            ],
            'Servidores': [
                {'nombre': 'Servidor Dell PowerEdge', 'codigo': 'SERV001', 'marca': 'Dell', 'modelo': 'PowerEdge', 'cantidad': 1, 'precio_unitario': 2500.00},
            ],
            'Otros': [
                {'nombre': 'Cable HDMI', 'codigo': 'CABLE001', 'marca': 'Amazon Basics', 'modelo': 'HDMI 2m', 'cantidad': 25, 'precio_unitario': 15.00},
                {'nombre': 'Webcam HD', 'codigo': 'CAM001', 'marca': 'Logitech', 'modelo': 'C920', 'cantidad': 6, 'precio_unitario': 90.00},
            ]
        }
        
        productos_creados = 0
        
        for categoria_nombre, productos in productos_prueba.items():
            try:
                categoria = Categoria.objects.get(nombre=categoria_nombre)
                print(f"\n📦 Agregando productos a '{categoria_nombre}':")
                
                for prod_data in productos:
                    # Verificar si el producto ya existe
                    if not Producto.objects.filter(codigo=prod_data['codigo']).exists():
                        producto = Producto.objects.create(
                            categoria=categoria,
                            **prod_data,
                            descripcion=f"Producto de prueba - {prod_data['nombre']}",
                            estado='activo'
                        )
                        print(f"  ✅ {producto.nombre} creado")
                        productos_creados += 1
                    else:
                        print(f"  ⚠️ {prod_data['nombre']} ya existe")
                        
            except Categoria.DoesNotExist:
                print(f"  ❌ Categoría '{categoria_nombre}' no encontrada")
        
        print(f"\n🎉 Total de productos creados: {productos_creados}")
        print("\n📊 Verificando datos para el gráfico:")
        
        for cat in Categoria.objects.all():
            count = cat.productos.count()
            print(f"  • {cat.nombre}: {count} productos")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al agregar datos de prueba: {e}")
        return False

if __name__ == "__main__":
    main() 