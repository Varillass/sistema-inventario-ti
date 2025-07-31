#!/usr/bin/env python
"""
Script para generar todas las claves necesarias para producción
"""
import secrets
import string
from cryptography.fernet import Fernet
import base64

def generate_production_keys():
    """Genera todas las claves necesarias para producción"""
    print("=== GENERADOR DE CLAVES PARA PRODUCCIÓN ===")
    print()
    
    # 1. Generar SECRET_KEY para Django
    secret_key = ''.join(secrets.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(50))
    
    # 2. Generar claves de encriptación
    license_key = Fernet.generate_key()
    account_key = Fernet.generate_key()
    
    # 3. Convertir a base64 para Render
    license_key_b64 = base64.b64encode(license_key).decode()
    account_key_b64 = base64.b64encode(account_key).decode()
    
    print("🔐 CLAVES GENERADAS PARA RENDER:")
    print()
    print("📋 Variables de entorno para Render:")
    print("=" * 50)
    print(f"SECRET_KEY={secret_key}")
    print(f"DEBUG=false")
    print(f"ALLOWED_HOSTS=.onrender.com")
    print(f"LICENSE_ENCRYPTION_KEY={license_key_b64}")
    print(f"ACCOUNT_ENCRYPTION_KEY={account_key_b64}")
    print("=" * 50)
    print()
    print("📋 Para settings.py (desarrollo):")
    print("=" * 50)
    print(f"SECRET_KEY = '{secret_key}'")
    print(f"LICENSE_ENCRYPTION_KEY = b'{license_key_b64}'")
    print(f"ACCOUNT_ENCRYPTION_KEY = b'{account_key_b64}'")
    print("=" * 50)
    print()
    print("⚠️  INSTRUCCIONES:")
    print("1. Copia las variables de entorno para Render")
    print("2. En Render, ve a tu servicio → Environment")
    print("3. Agrega cada variable una por una")
    print("4. Guarda los cambios")
    print()
    print("✅ ¡Las claves están listas para usar!")

if __name__ == "__main__":
    generate_production_keys() 