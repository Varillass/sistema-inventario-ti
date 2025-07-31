from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.utils import timezone
from cryptography.fernet import Fernet
from django.conf import settings
import uuid
import base64


class Usuario(AbstractUser):
    """Modelo de usuario personalizado con roles"""
    ROLES = (
        ('admin', 'Administrador'),
        ('user', 'Usuario'),
    )
    
    rol = models.CharField(max_length=10, choices=ROLES, default='user')
    telefono = models.CharField(max_length=15, blank=True, null=True)
    departamento = models.CharField(max_length=100, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.rol})"


class Categoria(models.Model):
    """Modelo para categorías de productos"""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class Sede(models.Model):
    """Modelo para sedes de la empresa"""
    nombre = models.CharField(max_length=100, unique=True)
    direccion = models.TextField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Sede'
        verbose_name_plural = 'Sedes'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class Area(models.Model):
    """Modelo para áreas de la empresa"""
    nombre = models.CharField(max_length=100)
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE, related_name='areas')
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Área'
        verbose_name_plural = 'Áreas'
        ordering = ['sede', 'nombre']
        unique_together = ['nombre', 'sede']
    
    def __str__(self):
        return f"{self.nombre} - {self.sede.nombre}"


class Personal(models.Model):
    """Modelo para personal de la empresa"""
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    area = models.ForeignKey(Area, on_delete=models.CASCADE, related_name='personal')
    cargo = models.CharField(max_length=100, blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Personal'
        verbose_name_plural = 'Personal'
        ordering = ['apellido', 'nombre']
    
    def __str__(self):
        return f"{self.apellido}, {self.nombre}"
    
    def get_full_name(self):
        return f"{self.nombre} {self.apellido}"


class Licencia(models.Model):
    """Modelo para licencias de software"""
    TIPOS_LICENCIA = (
        ('perpetua', 'Perpetua'),
        ('anual', 'Anual'),
        ('mensual', 'Mensual'),
        ('otro', 'Otro'),
    )
    
    TIPOS_DISTRIBUCION = (
        ('oem', 'OEM'),
        ('retail', 'Retail'),
        ('volume', 'Volume License'),
        ('otro', 'Otro'),
    )
    
    nombre = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPOS_LICENCIA, default='perpetua')
    tipo_distribucion = models.CharField(max_length=20, choices=TIPOS_DISTRIBUCION, default='retail', verbose_name='Tipo de Distribución')
    proveedor = models.CharField(max_length=200, blank=True, null=True)
    fecha_adquisicion = models.DateField(blank=True, null=True)
    fecha_vencimiento = models.DateField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    cantidad_licencias = models.IntegerField(default=1)
    licencias_disponibles = models.IntegerField(default=1, help_text="Cantidad de licencias disponibles para asignar")
    clave_licencia = models.TextField(blank=True, null=True, help_text="Clave de licencia encriptada")
    activo = models.BooleanField(default=True)
    observaciones = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Licencia'
        verbose_name_plural = 'Licencias'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre
    
    def _get_encryption_key(self):
        """Obtiene la clave de encriptación desde settings o genera una nueva"""
        if hasattr(settings, 'LICENSE_ENCRYPTION_KEY'):
            # La clave ya está en bytes, no necesita encode()
            return settings.LICENSE_ENCRYPTION_KEY
        else:
            # Generar una clave si no existe en settings
            key = Fernet.generate_key()
            return key
    
    def encrypt_license_key(self, license_key):
        """Encripta la clave de licencia"""
        if not license_key:
            return None
        
        try:
            fernet = Fernet(self._get_encryption_key())
            encrypted_data = fernet.encrypt(license_key.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            # En caso de error, devolver None
            return None
    
    def decrypt_license_key(self):
        """Desencripta la clave de licencia"""
        if not self.clave_licencia:
            return None
        
        try:
            fernet = Fernet(self._get_encryption_key())
            encrypted_data = base64.b64decode(self.clave_licencia.encode())
            decrypted_data = fernet.decrypt(encrypted_data)
            return decrypted_data.decode()
        except Exception as e:
            # En caso de error, devolver None
            return None
    
    def set_license_key(self, license_key):
        """Establece la clave de licencia encriptada"""
        self.clave_licencia = self.encrypt_license_key(license_key)
    
    def get_license_key(self):
        """Obtiene la clave de licencia desencriptada"""
        return self.decrypt_license_key()


class Producto(models.Model):
    """Modelo para productos del inventario"""
    ESTADOS = (
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('mantenimiento', 'En Mantenimiento'),
        ('retirado', 'Retirado'),
    )
    
    TIPOS_PROPIEDAD = (
        ('propio', 'Propio'),
        ('alquilado', 'Alquilado'),
    )
    
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='productos')
    marca = models.CharField(max_length=100, blank=True, null=True)
    modelo = models.CharField(max_length=100, blank=True, null=True)
    serie = models.CharField(max_length=100, blank=True, null=True)
    
    # Ubicación y asignación
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE, related_name='productos', blank=True, null=True)
    area = models.ForeignKey(Area, on_delete=models.CASCADE, related_name='productos', blank=True, null=True)
    personal_asignado = models.ForeignKey(Personal, on_delete=models.SET_NULL, blank=True, null=True, related_name='productos_asignados')
    
    # Propiedad del equipo
    tipo_propiedad = models.CharField(max_length=20, choices=TIPOS_PROPIEDAD, default='propio')
    codigo_alquiler = models.CharField(max_length=50, blank=True, null=True, help_text="Código de alquiler si es alquilado")
    fecha_alquiler = models.DateField(blank=True, null=True, help_text="Fecha de inicio del alquiler")
    fecha_vencimiento_alquiler = models.DateField(blank=True, null=True, help_text="Fecha de vencimiento del alquiler")
    
    # Software y sistema
    sistema_operativo = models.CharField(max_length=100, blank=True, null=True)
    antivirus = models.BooleanField(default=False)
    antivirus_nombre = models.CharField(max_length=100, blank=True, null=True)
    
    # Licencias asociadas
    licencias = models.ManyToManyField(Licencia, blank=True, through='ProductoLicencia')
    
    # Campos existentes
    ubicacion = models.CharField(max_length=200, blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='activo')
    cantidad = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fecha_adquisicion = models.DateField(blank=True, null=True)
    proveedor = models.CharField(max_length=200, blank=True, null=True)
    garantia_hasta = models.DateField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['categoria', 'nombre']
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    @property
    def valor_total(self):
        """Calcula el valor total del producto"""
        if self.precio_unitario and self.cantidad:
            return self.precio_unitario * self.cantidad
        return 0


class ProductoLicencia(models.Model):
    """Modelo intermedio para relacionar productos con licencias"""
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    licencia = models.ForeignKey(Licencia, on_delete=models.CASCADE)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    observaciones = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Licencia de Producto'
        verbose_name_plural = 'Licencias de Productos'
        unique_together = ['producto', 'licencia']
    
    def __str__(self):
        return f"{self.producto.codigo} - {self.licencia.nombre}"


class TipoMovimiento(models.Model):
    """Modelo para tipos de movimientos"""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    afecta_stock = models.BooleanField(default=True)
    es_entrada = models.BooleanField(default=True)  # True para entradas, False para salidas
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Tipo de Movimiento'
        verbose_name_plural = 'Tipos de Movimientos'
    
    def __str__(self):
        return self.nombre


class Movimiento(models.Model):
    """Modelo para movimientos de inventario"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='movimientos')
    tipo_movimiento = models.ForeignKey(TipoMovimiento, on_delete=models.CASCADE)
    cantidad = models.IntegerField(validators=[MinValueValidator(1)])
    cantidad_anterior = models.IntegerField()
    cantidad_nueva = models.IntegerField()
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    fecha_movimiento = models.DateTimeField(auto_now_add=True)
    motivo = models.TextField()
    referencia = models.CharField(max_length=100, blank=True, null=True)
    
    # Ubicaciones origen y destino
    sede_origen = models.ForeignKey(Sede, on_delete=models.CASCADE, related_name='movimientos_origen', blank=True, null=True)
    area_origen = models.ForeignKey(Area, on_delete=models.CASCADE, related_name='movimientos_origen', blank=True, null=True)
    sede_destino = models.ForeignKey(Sede, on_delete=models.CASCADE, related_name='movimientos_destino', blank=True, null=True)
    area_destino = models.ForeignKey(Area, on_delete=models.CASCADE, related_name='movimientos_destino', blank=True, null=True)
    
    # Personal responsable
    personal_origen = models.ForeignKey(Personal, on_delete=models.SET_NULL, related_name='movimientos_origen', blank=True, null=True)
    personal_destino = models.ForeignKey(Personal, on_delete=models.SET_NULL, related_name='movimientos_destino', blank=True, null=True)
    
    # Campos legacy para compatibilidad
    ubicacion_origen = models.CharField(max_length=200, blank=True, null=True)
    ubicacion_destino = models.CharField(max_length=200, blank=True, null=True)
    responsable = models.CharField(max_length=200, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Movimiento'
        verbose_name_plural = 'Movimientos'
        ordering = ['-fecha_movimiento']
    
    def __str__(self):
        return f"{self.producto.codigo} - {self.tipo_movimiento.nombre} - {self.cantidad}"
    
    def save(self, *args, **kwargs):
        if not self.pk:  # Solo para nuevos movimientos
            self.cantidad_anterior = self.producto.cantidad
            if self.tipo_movimiento.es_entrada:
                self.cantidad_nueva = self.cantidad_anterior + self.cantidad
            else:
                self.cantidad_nueva = self.cantidad_anterior - self.cantidad
            
            # Actualizar stock del producto
            self.producto.cantidad = self.cantidad_nueva
            self.producto.save()
        
        super().save(*args, **kwargs)


class Reporte(models.Model):
    """Modelo para reportes generados"""
    TIPOS_REPORTE = (
        ('inventario', 'Reporte de Inventario'),
        ('movimientos', 'Reporte de Movimientos'),
        ('valor', 'Reporte de Valor'),
        ('categoria', 'Reporte por Categoría'),
        ('estado', 'Reporte por Estado'),
    )
    
    nombre = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPOS_REPORTE)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    parametros = models.JSONField(blank=True, null=True)  # Para almacenar filtros aplicados
    archivo = models.FileField(upload_to='reportes/', blank=True, null=True)
    
    class Meta:
        verbose_name = 'Reporte'
        verbose_name_plural = 'Reportes'
        ordering = ['-fecha_generacion']
    
    def __str__(self):
        return f"{self.nombre} - {self.get_tipo_display()}"


class ConfiguracionSistema(models.Model):
    """Modelo para configuraciones del sistema"""
    nombre = models.CharField(max_length=100, unique=True)
    valor = models.TextField()
    descripcion = models.TextField(blank=True, null=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Configuración del Sistema'
        verbose_name_plural = 'Configuraciones del Sistema'
    
    def __str__(self):
        return self.nombre


class Cuenta(models.Model):
    """Modelo para gestionar cuentas de Office 365 o cualquier tipo de cuenta"""
    TIPOS_CUENTA = (
        ('office365', 'Office 365'),
        ('google', 'Google Workspace'),
        ('aws', 'Amazon Web Services'),
        ('azure', 'Microsoft Azure'),
        ('dropbox', 'Dropbox'),
        ('slack', 'Slack'),
        ('zoom', 'Zoom'),
        ('adobe', 'Adobe Creative Cloud'),
        ('otro', 'Otro'),
    )
    
    ESTADOS_CUENTA = (
        ('activa', 'Activa'),
        ('inactiva', 'Inactiva'),
        ('suspendida', 'Suspendida'),
        ('vencida', 'Vencida'),
    )
    
    nombre = models.CharField(max_length=200, help_text="Nombre descriptivo de la cuenta")
    tipo_cuenta = models.CharField(max_length=20, choices=TIPOS_CUENTA, default='office365', verbose_name='Tipo de Cuenta')
    email = models.EmailField(help_text="Correo electrónico de la cuenta")
    usuario = models.CharField(max_length=100, help_text="Nombre de usuario")
    password = models.TextField(blank=True, null=True, help_text="Contraseña encriptada")
    url_acceso = models.URLField(blank=True, null=True, help_text="URL de acceso a la plataforma")
    
    # Información de la cuenta
    fecha_creacion_cuenta = models.DateField(blank=True, null=True, help_text="Fecha de creación de la cuenta")
    fecha_vencimiento = models.DateField(blank=True, null=True, help_text="Fecha de vencimiento de la suscripción")
    estado = models.CharField(max_length=20, choices=ESTADOS_CUENTA, default='activa')
    
    # Asignación
    personal_asignado = models.ForeignKey(Personal, on_delete=models.SET_NULL, blank=True, null=True, related_name='cuentas_asignadas', help_text="Personal asignado a esta cuenta")
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE, related_name='cuentas', blank=True, null=True)
    area = models.ForeignKey(Area, on_delete=models.CASCADE, related_name='cuentas', blank=True, null=True)
    
    # Información adicional
    plan_suscripcion = models.CharField(max_length=100, blank=True, null=True, help_text="Plan o tipo de suscripción")
    costo_mensual = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Costo mensual de la suscripción")
    proveedor = models.CharField(max_length=200, blank=True, null=True, help_text="Proveedor del servicio")
    
    # Campos de control
    activo = models.BooleanField(default=True)
    observaciones = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Cuenta'
        verbose_name_plural = 'Cuentas'
        ordering = ['tipo_cuenta', 'nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_cuenta_display()})"
    
    def _get_encryption_key(self):
        """Obtiene la clave de encriptación desde settings o genera una nueva"""
        if hasattr(settings, 'ACCOUNT_ENCRYPTION_KEY'):
            return settings.ACCOUNT_ENCRYPTION_KEY.encode()
        else:
            # Usar la misma clave que las licencias si no existe una específica
            if hasattr(settings, 'LICENSE_ENCRYPTION_KEY'):
                return settings.LICENSE_ENCRYPTION_KEY.encode()
            else:
                # Generar una clave si no existe en settings
                key = Fernet.generate_key()
                return key
    
    def encrypt_password(self, password):
        """Encripta la contraseña"""
        if not password:
            return None
        
        try:
            fernet = Fernet(self._get_encryption_key())
            encrypted_data = fernet.encrypt(password.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            # En caso de error, devolver None
            return None
    
    def decrypt_password(self):
        """Desencripta la contraseña"""
        if not self.password:
            return None
        
        try:
            fernet = Fernet(self._get_encryption_key())
            encrypted_data = base64.b64decode(self.password.encode())
            decrypted_data = fernet.decrypt(encrypted_data)
            return decrypted_data.decode()
        except Exception as e:
            # En caso de error, devolver None
            return None
    
    def set_password(self, password):
        """Establece la contraseña encriptada"""
        self.password = self.encrypt_password(password)
    
    def get_password(self):
        """Obtiene la contraseña desencriptada"""
        return self.decrypt_password()
    
    @property
    def dias_vencimiento(self):
        """Calcula los días hasta el vencimiento"""
        if self.fecha_vencimiento:
            from datetime import date
            hoy = date.today()
            return (self.fecha_vencimiento - hoy).days
        return None
    
    @property
    def estado_vencimiento(self):
        """Determina el estado de vencimiento"""
        if not self.fecha_vencimiento:
            return 'sin_fecha'
        
        dias = self.dias_vencimiento
        if dias < 0:
            return 'vencida'
        elif dias <= 30:
            return 'proximo_vencimiento'
        else:
            return 'vigente'
