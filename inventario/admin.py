from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import (
    Usuario, Categoria, Producto, TipoMovimiento, 
    Movimiento, Reporte, ConfiguracionSistema
)


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Configuración del admin para el modelo Usuario personalizado"""
    list_display = ('username', 'email', 'first_name', 'last_name', 'rol', 'is_active', 'date_joined')
    list_filter = ('rol', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Información Adicional', {
            'fields': ('rol', 'telefono', 'departamento')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información Adicional', {
            'fields': ('rol', 'telefono', 'departamento')
        }),
    )


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    """Configuración del admin para el modelo Categoria"""
    list_display = ('nombre', 'descripcion', 'activo', 'fecha_creacion', 'total_productos')
    list_filter = ('activo', 'fecha_creacion')
    search_fields = ('nombre', 'descripcion')
    ordering = ('nombre',)
    
    def total_productos(self, obj):
        """Muestra el total de productos en la categoría"""
        return obj.productos.count()
    total_productos.short_description = 'Total Productos'


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    """Configuración del admin para el modelo Producto"""
    list_display = ('codigo', 'nombre', 'categoria', 'cantidad', 'estado', 'ubicacion', 'valor_total_formatted')
    list_filter = ('categoria', 'estado', 'fecha_creacion', 'fecha_adquisicion')
    search_fields = ('codigo', 'nombre', 'marca', 'modelo', 'serie')
    ordering = ('categoria', 'nombre')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'nombre', 'categoria', 'descripcion')
        }),
        ('Especificaciones', {
            'fields': ('marca', 'modelo', 'serie')
        }),
        ('Estado y Ubicación', {
            'fields': ('estado', 'cantidad', 'ubicacion')
        }),
        ('Información Financiera', {
            'fields': ('precio_unitario', 'valor_total')
        }),
        ('Información Adicional', {
            'fields': ('fecha_adquisicion', 'proveedor', 'garantia_hasta', 'observaciones')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def valor_total_formatted(self, obj):
        """Formatea el valor total del producto"""
        if obj.valor_total > 0:
            return format_html('<span style="color: green; font-weight: bold;">${:,.2f}</span>', obj.valor_total)
        return format_html('<span style="color: gray;">Sin valor</span>')
    valor_total_formatted.short_description = 'Valor Total'


@admin.register(TipoMovimiento)
class TipoMovimientoAdmin(admin.ModelAdmin):
    """Configuración del admin para el modelo TipoMovimiento"""
    list_display = ('nombre', 'descripcion', 'afecta_stock', 'es_entrada', 'activo')
    list_filter = ('afecta_stock', 'es_entrada', 'activo')
    search_fields = ('nombre', 'descripcion')
    ordering = ('nombre',)


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    """Configuración del admin para el modelo Movimiento"""
    list_display = ('id', 'producto', 'tipo_movimiento', 'cantidad', 'usuario', 'fecha_movimiento', 'motivo_short')
    list_filter = ('tipo_movimiento', 'fecha_movimiento', 'producto__categoria')
    search_fields = ('producto__nombre', 'producto__codigo', 'usuario__username', 'motivo')
    ordering = ('-fecha_movimiento',)
    readonly_fields = ('id', 'cantidad_anterior', 'cantidad_nueva', 'fecha_movimiento')
    
    fieldsets = (
        ('Información del Movimiento', {
            'fields': ('id', 'producto', 'tipo_movimiento', 'cantidad')
        }),
        ('Detalles', {
            'fields': ('motivo', 'referencia', 'responsable')
        }),
        ('Ubicaciones', {
            'fields': ('ubicacion_origen', 'ubicacion_destino')
        }),
        ('Información del Sistema', {
            'fields': ('usuario', 'cantidad_anterior', 'cantidad_nueva', 'fecha_movimiento'),
            'classes': ('collapse',)
        }),
        ('Observaciones', {
            'fields': ('observaciones',)
        }),
    )
    
    def motivo_short(self, obj):
        """Muestra el motivo truncado"""
        return obj.motivo[:50] + '...' if len(obj.motivo) > 50 else obj.motivo
    motivo_short.short_description = 'Motivo'


@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    """Configuración del admin para el modelo Reporte"""
    list_display = ('nombre', 'tipo', 'usuario', 'fecha_generacion', 'archivo_link')
    list_filter = ('tipo', 'fecha_generacion')
    search_fields = ('nombre', 'usuario__username')
    ordering = ('-fecha_generacion',)
    readonly_fields = ('fecha_generacion',)
    
    def archivo_link(self, obj):
        """Muestra un enlace al archivo si existe"""
        if obj.archivo:
            return format_html('<a href="{}" target="_blank">Descargar</a>', obj.archivo.url)
        return format_html('<span style="color: gray;">Sin archivo</span>')
    archivo_link.short_description = 'Archivo'


@admin.register(ConfiguracionSistema)
class ConfiguracionSistemaAdmin(admin.ModelAdmin):
    """Configuración del admin para el modelo ConfiguracionSistema"""
    list_display = ('nombre', 'valor', 'descripcion', 'fecha_actualizacion')
    search_fields = ('nombre', 'descripcion')
    ordering = ('nombre',)
    readonly_fields = ('fecha_actualizacion',)


# Configuración del sitio admin
admin.site.site_header = "Sistema de Inventario TI - Administración"
admin.site.site_title = "Inventario TI Admin"
admin.site.index_title = "Panel de Administración"
