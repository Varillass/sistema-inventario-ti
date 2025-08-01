# Sistema de Inventario TI

Sistema completo de gestión de inventario para el área de TI, desarrollado con Django y MySQL.

## Características

- ✅ Sistema de autenticación con roles (admin/user)
- ✅ Gestión de productos y categorías
- ✅ Movimientos de inventario con trazabilidad
- ✅ Gestión de sedes, áreas y personal
- ✅ Sistema de licencias y cuentas
- ✅ Conexiones Winbox para MikroTik
- ✅ Planificación semanal
- ✅ Generación de reportes (Excel/PDF)
- ✅ Encriptación de datos sensibles

## Despliegue en Render

### 1. Preparación del Repositorio

Asegúrate de que tu repositorio contenga los siguientes archivos:
- `requirements.txt`
- `build.sh`
- `runtime.txt`
- `manage.py`
- `sistema_inventario_ti/settings.py`

### 2. Configuración en Render

1. **Crear una nueva aplicación web** en Render
2. **Conectar tu repositorio** de GitHub/GitLab
3. **Configurar las variables de entorno**:

```
SECRET_KEY=tu_clave_secreta_generada
DEBUG=False
DATABASE_URL=postgresql://usuario:password@host:puerto/nombre_db
LICENSE_ENCRYPTION_KEY=b'2vDGw7FRIz6ENdyS0cdydLEyo3NqOCJ2816NeClTcgY='
ACCOUNT_ENCRYPTION_KEY=b'2vDGw7FRIz6ENdyS0cdydLEyo3NqOCJ2816NeClTcgY='
WINBOX_ENCRYPTION_KEY=b'2vDGw7FRIz6ENdyS0cdydLEyo3NqOCJ2816NeClTcgY='
```

### 3. Configuración de la Aplicación

- **Build Command**: `./build.sh`
- **Start Command**: `gunicorn sistema_inventario_ti.wsgi:application`

### 4. Base de Datos

Render proporcionará automáticamente una base de datos PostgreSQL. El archivo `build.sh` ejecutará las migraciones automáticamente.

### 5. Usuario Inicial

Después del primer despliegue, necesitarás crear un usuario administrador. Puedes hacerlo ejecutando:

```bash
python manage.py createsuperuser
```

O crear un script de inicialización en `build.sh`:

```bash
echo "from inventario.models import Usuario; Usuario.objects.create_superuser('admin', 'admin@example.com', 'password123') if not Usuario.objects.filter(username='admin').exists() else None" | python manage.py shell
```

## Desarrollo Local

1. **Clonar el repositorio**
2. **Instalar dependencias**: `pip install -r requirements.txt`
3. **Configurar base de datos MySQL**
4. **Ejecutar migraciones**: `python manage.py migrate`
5. **Crear superusuario**: `python manage.py createsuperuser`
6. **Ejecutar servidor**: `python manage.py runserver`

## Estructura del Proyecto

```
sistema_inventario_ti/
├── inventario/           # Aplicación principal
├── templates/           # Plantillas HTML
├── static/             # Archivos estáticos
├── sistema_inventario_ti/  # Configuración del proyecto
├── requirements.txt     # Dependencias
├── build.sh           # Script de construcción para Render
├── runtime.txt        # Versión de Python
└── manage.py         # Script de gestión de Django
```

## Tecnologías Utilizadas

- **Backend**: Django 5.2.4
- **Base de Datos**: MySQL (desarrollo) / PostgreSQL (producción)
- **Frontend**: Bootstrap 5, jQuery, DataTables
- **Encriptación**: cryptography (Fernet)
- **Despliegue**: Render, Gunicorn, WhiteNoise 