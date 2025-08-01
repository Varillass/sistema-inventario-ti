#!/usr/bin/env bash
# exit on error
set -o errexit

# Actualizar pip
pip install --upgrade pip

# Instalar todas las dependencias
pip install -r requirements.txt

# Recolectar archivos estáticos
python manage.py collectstatic --no-input --settings=sistema_inventario_ti.settings_production

# Ejecutar migraciones con configuración de producción
python manage.py migrate --settings=sistema_inventario_ti.settings_production 