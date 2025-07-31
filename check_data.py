#!/usr/bin/env python
"""
Script para verificar datos en la base de datos
"""

import os
import sys
import django

def main():
    """Verificar datos en la base de datos"""
    try:
        # Configurar Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_inventario_ti.settings')
        django.setup()
        
        from inventario.models import Categoria, Producto
        
        print("🔍 Verificando datos en la base de datos...")
        print("=" * 50)
        
        # Verificar categorías
        categorias_count = Categoria.objects.count()
        print(f"📊 Total de categorías: {categorias_count}")
        
        if categorias_count > 0:
            print("\n📋 Categorías disponibles:")
            for cat in Categoria.objects.all():
                productos_count = cat.productos.count()
                print(f"  • {cat.nombre}: {productos_count} productos")
        
        # Verificar productos
        productos_count = Producto.objects.count()
        print(f"\n📦 Total de productos: {productos_count}")
        
        if productos_count > 0:
            print("\n📋 Productos disponibles:")
            for prod in Producto.objects.all()[:10]:  # Solo mostrar los primeros 10
                print(f"  • {prod.nombre} ({prod.categoria.nombre})")
        
        # Verificar datos para el gráfico
        print("\n📈 Datos para el gráfico de productos por categoría:")
        productos_por_categoria = Categoria.objects.annotate(
            total_productos=django.db.models.Count('productos')
        ).values('nombre', 'total_productos')
        
        for item in productos_por_categoria:
            print(f"  • {item['nombre']}: {item['total_productos']} productos")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al verificar datos: {e}")
        return False

if __name__ == "__main__":
    main() 