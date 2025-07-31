# Sistema de Inventario TI

Un sistema completo de gestión de inventario para empresas de tecnología, desarrollado con Django.

## 🚀 Características

### Gestión de Inventario
- **Productos**: Registro completo de equipos con códigos únicos
- **Categorías**: Organización por tipos de productos
- **Movimientos**: Control de entradas y salidas de inventario
- **Ubicaciones**: Gestión por sedes y áreas

### Gestión de Licencias
- **Licencias de Software**: Control de licencias con encriptación de claves
- **Tipos de Distribución**: OEM, Retail, Volume License
- **Asignación**: Vinculación de licencias a productos
- **Vencimientos**: Control de fechas de expiración

### Gestión de Cuentas
- **Cuentas de Servicios**: Office 365, Google Workspace, AWS, etc.
- **Contraseñas Encriptadas**: Seguridad en el almacenamiento
- **Suscripciones**: Control de planes y costos mensuales

### Reportes
- **Reportes PDF**: Generación automática de reportes en PDF
- **Filtros Avanzados**: Múltiples criterios de búsqueda
- **Estadísticas**: Dashboard con métricas importantes

### Seguridad
- **Encriptación**: Claves de licencia y contraseñas encriptadas
- **Roles de Usuario**: Administrador y Usuario
- **Autenticación**: Sistema de login seguro

## 🛠️ Tecnologías

- **Backend**: Django 5.2.4
- **Base de Datos**: MySQL
- **Frontend**: Bootstrap 5, jQuery
- **Encriptación**: Cryptography (Fernet)
- **Reportes**: ReportLab
- **Despliegue**: Render

## 📋 Requisitos

- Python 3.8+
- MySQL 5.7+
- pip

## 🔧 Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/sistema-inventario-ti.git
cd sistema-inventario-ti
```

### 2. Crear entorno virtual
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar base de datos
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Crear superusuario
```bash
python manage.py createsuperuser
```

### 6. Ejecutar servidor
```bash
python manage.py runserver
```

## 🔐 Configuración de Encriptación

El sistema utiliza encriptación para las claves de licencia y contraseñas. Las claves se configuran en `settings.py`:

```python
LICENSE_ENCRYPTION_KEY = b'tu-clave-aqui'
ACCOUNT_ENCRYPTION_KEY = b'tu-clave-aqui'
```

## 📊 Estructura del Proyecto

```
sistema_inventario_ti/
├── inventario/                 # App principal
│   ├── models.py              # Modelos de datos
│   ├── views.py               # Vistas y lógica
│   ├── forms.py               # Formularios
│   └── urls.py                # URLs de la app
├── templates/                 # Plantillas HTML
│   ├── base.html             # Template base
│   └── inventario/           # Templates específicos
├── static/                   # Archivos estáticos
├── media/                    # Archivos subidos
└── manage.py                 # Script de Django
```

## 🚀 Despliegue en Render

### 1. Preparar para producción

Crear archivo `render.yaml`:
```yaml
services:
  - type: web
    name: sistema-inventario-ti
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn sistema_inventario_ti.wsgi:application
    envVars:
      - key: PYTHON_VERSION
        value: 3.9.16
```

### 2. Configurar variables de entorno en Render
- `SECRET_KEY`
- `DATABASE_URL`
- `LICENSE_ENCRYPTION_KEY`
- `ACCOUNT_ENCRYPTION_KEY`

### 3. Conectar con GitHub
- Conectar el repositorio de GitHub
- Configurar build automático

## 📝 Uso

### Gestión de Productos
1. Ir a **Productos** → **Lista de Productos**
2. Crear categorías y sedes primero
3. Agregar productos con códigos únicos
4. Asignar ubicaciones y personal

### Gestión de Licencias
1. Ir a **Licencias** → **Lista de Licencias**
2. Crear licencias con claves encriptadas
3. Asignar licencias a productos
4. Controlar vencimientos

### Gestión de Cuentas
1. Ir a **Cuentas** → **Lista de Cuentas**
2. Registrar cuentas de servicios
3. Configurar contraseñas encriptadas
4. Monitorear vencimientos

### Reportes
1. Ir a **Reportes**
2. Seleccionar tipo de reporte
3. Aplicar filtros
4. Generar y descargar PDF

## 🔧 Configuración de Base de Datos

### Desarrollo (SQLite)
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### Producción (MySQL)
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'nombre_db',
        'USER': 'usuario',
        'PASSWORD': 'contraseña',
        'HOST': 'host',
        'PORT': '3306',
    }
}
```

## 🤝 Contribuir

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 📞 Soporte

Para soporte técnico, contactar a:
- Email: soporte@empresa.com
- Teléfono: +1 234 567 890

## 🗺️ Roadmap

- [ ] API REST completa
- [ ] Aplicación móvil
- [ ] Integración con proveedores
- [ ] Dashboard avanzado
- [ ] Notificaciones automáticas
- [ ] Backup automático
- [ ] Auditoría de cambios

---

**Desarrollado con ❤️ para la gestión eficiente de inventarios TI** 