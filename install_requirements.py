#!/usr/bin/env python
"""
Script para instalar todas las dependencias necesarias del proyecto
"""

import subprocess
import sys
import os

def install_package(package):
    """Instalar un paquete usando pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    """Instalar todas las dependencias"""
    print("📦 Instalando dependencias del Sistema de Inventario TI...")
    print("=" * 60)
    
    # Lista de dependencias
    packages = [
        "django>=4.2.0",
        "mysql-connector-python>=8.0.0",
        "Pillow>=9.0.0",  # Para manejo de imágenes
        "reportlab>=3.6.0",  # Para generar reportes PDF
        "openpyxl>=3.0.0",  # Para exportar a Excel
    ]
    
    print("🔍 Verificando Python...")
    print(f"   Versión de Python: {sys.version}")
    
    print("\n📥 Instalando paquetes...")
    failed_packages = []
    
    for package in packages:
        print(f"   Instalando {package}...")
        if install_package(package):
            print(f"   ✅ {package} instalado correctamente")
        else:
            print(f"   ❌ Error al instalar {package}")
            failed_packages.append(package)
    
    if failed_packages:
        print(f"\n❌ Error al instalar los siguientes paquetes:")
        for package in failed_packages:
            print(f"   - {package}")
        print("\n💡 Intenta instalar manualmente con:")
        print("   pip install -r requirements.txt")
        return False
    else:
        print("\n✅ Todas las dependencias instaladas correctamente!")
        print("\n📋 Próximos pasos:")
        print("1. Ejecuta: python setup_database.py")
        print("2. Ejecuta: python manage.py migrate")
        print("3. Ejecuta: python manage.py runserver")
        return True

if __name__ == "__main__":
    main() 