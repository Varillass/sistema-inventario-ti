#!/usr/bin/env bash
# exit on error
set -o errexit

# Actualizar pip
pip install --upgrade pip

# Instalar dependencias con manejo de errores
pip install -r requirements.txt || {
    echo "Error instalando dependencias. Intentando instalar una por una..."
    pip install Django==5.2.4
    pip install mysqlclient==2.2.0
    pip install cryptography==41.0.7
    pip install dj-database-url==2.1.0
    pip install whitenoise==6.6.0
    pip install gunicorn==21.2.0
    pip install psycopg2-binary==2.9.9
    pip install python-barcode==0.15.1
    pip install Pillow==10.0.1
    pip install reportlab==3.6.13
}

# Recolectar archivos estáticos
python manage.py collectstatic --no-input --settings=sistema_inventario_ti.settings_production

# Ejecutar migraciones con configuración de producción
python manage.py migrate --settings=sistema_inventario_ti.settings_production 