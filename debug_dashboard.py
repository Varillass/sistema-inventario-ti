#!/usr/bin/env python
"""
Script para debuggear el problema del dashboard
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_inventario_ti.settings')
django.setup()

from inventario.models import Producto
from django.db.models import Sum, Count
from decimal import Decimal

def test_dashboard_calculations():
    """Prueba los cálculos del dashboard"""
    print("=== PRUEBA DE CÁLCULOS DEL DASHBOARD ===")
    
    try:
        # 1. Contar productos
        total_productos = Producto.objects.count()
        print(f"Total productos: {total_productos}")
        
        # 2. Productos con stock bajo
        productos_stock_bajo = Producto.objects.filter(cantidad__lt=5).count()
        print(f"Productos con stock bajo: {productos_stock_bajo}")
        
        # 3. Probar el cálculo del valor total
        print("\n=== PRUEBA DEL CÁLCULO DE VALOR TOTAL ===")
        productos = Producto.objects.all()
        
        valor_total = 0
        for producto in productos:
            precio = producto.precio_unitario or 0
            cantidad = producto.cantidad or 0
            valor_producto = precio * cantidad
            
            print(f"Producto: {producto.nombre}")
            print(f"  - Precio unitario: {precio}")
            print(f"  - Cantidad: {cantidad}")
            print(f"  - Valor: {valor_producto}")
            
            valor_total += valor_producto
        
        print(f"\nValor total del inventario: {valor_total}")
        
        # 4. Probar con sum() directamente
        print("\n=== PRUEBA CON SUM() ===")
        valor_total_sum = sum(
            (producto.precio_unitario or 0) * (producto.cantidad or 0)
            for producto in Producto.objects.all()
        )
        print(f"Valor total con sum(): {valor_total_sum}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        print(f"Tipo de error: {type(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_producto_data():
    """Prueba los datos de productos"""
    print("\n=== PRUEBA DE DATOS DE PRODUCTOS ===")
    
    productos = Producto.objects.all()
    print(f"Total de productos en BD: {productos.count()}")
    
    for i, producto in enumerate(productos[:5]):  # Solo los primeros 5
        print(f"\nProducto {i+1}:")
        print(f"  - ID: {producto.id}")
        print(f"  - Nombre: {producto.nombre}")
        print(f"  - Precio unitario: {producto.precio_unitario} (tipo: {type(producto.precio_unitario)})")
        print(f"  - Cantidad: {producto.cantidad} (tipo: {type(producto.cantidad)})")
        print(f"  - Categoría: {producto.categoria.nombre if producto.categoria else 'Sin categoría'}")

if __name__ == "__main__":
    print("Iniciando pruebas de debug...")
    
    # Probar datos de productos
    test_producto_data()
    
    # Probar cálculos del dashboard
    success = test_dashboard_calculations()
    
    if success:
        print("\n✅ Todas las pruebas pasaron correctamente")
    else:
        print("\n❌ Se encontraron errores en las pruebas") 