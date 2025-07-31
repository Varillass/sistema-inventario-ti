# Sistema de Inventario TI - Guía de Instalación

## 📋 Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- MySQL Server (opcional, se puede usar SQLite)

## 🚀 Instalación Rápida

### Opción 1: Instalación Automática
```bash
# 1. Instalar dependencias
python install_requirements.py

# 2. Configurar base de datos
python setup_database.py

# 3. Ejecutar migraciones
python manage.py migrate

# 4. Iniciar servidor
python manage.py runserver
```

### Opción 2: Instalación Manual
```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar base de datos
python setup_database.py

# 3. Ejecutar migraciones
python manage.py migrate

# 4. Iniciar servidor
python manage.py runserver
```

## 🔧 Configuración de Base de Datos

### MySQL (Recomendado para producción)
El sistema está configurado para usar MySQL por defecto. Las credenciales están en `sistema_inventario_ti/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'inventario_ti',
        'USER': 'afrodita',
        'PASSWORD': 'Zxasqw12@@@',
        'HOST': '181.224.226.142',
        'PORT': '3306',
    }
}
```

### SQLite (Recomendado para desarrollo)
Si tienes problemas con MySQL, puedes usar SQLite:

1. Copia el contenido de `settings_sqlite.py` a `sistema_inventario_ti/settings.py`
2. Ejecuta las migraciones: `python manage.py migrate`

## 👤 Acceso al Sistema

Una vez configurado, accede a:
- **URL**: http://localhost:8000
- **Usuario**: admin
- **Contraseña**: admin123

## 🛠️ Solución de Problemas

### Error de conexión a MySQL
1. Verifica que MySQL esté ejecutándose
2. Verifica las credenciales en `settings.py`
3. Usa SQLite como alternativa

### Error de migraciones
```bash
python manage.py makemigrations
python manage.py migrate
```

### Error de dependencias
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Error de permisos
En Windows, ejecuta PowerShell como administrador.

## 📁 Estructura del Proyecto

```
Sistema Inventario Ti/
├── inventario/           # Aplicación principal
├── sistema_inventario_ti/ # Configuración del proyecto
├── templates/            # Plantillas HTML
├── static/              # Archivos estáticos
├── setup_database.py    # Script de configuración
├── install_requirements.py # Script de instalación
├── requirements.txt     # Dependencias
└── README_INSTALACION.md # Esta guía
```

## 🔒 Seguridad

⚠️ **Importante**: 
- Cambia las credenciales por defecto en producción
- No uses las credenciales de ejemplo en un entorno de producción
- Configura HTTPS en producción

## 📞 Soporte

Si tienes problemas:
1. Revisa los logs de error
2. Verifica la configuración de la base de datos
3. Asegúrate de que todas las dependencias estén instaladas

## 🎯 Características del Sistema

- ✅ Gestión de inventario
- ✅ Control de movimientos
- ✅ Reportes y estadísticas
- ✅ Gestión de usuarios
- ✅ Interfaz web moderna
- ✅ Soporte para múltiples sedes
- ✅ Control de licencias de software 