from django.urls import path
from . import views

app_name = 'inventario'

urlpatterns = [
    # Autenticación
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Productos
    path('productos/', views.lista_productos, name='lista_productos'),
    path('productos/crear/', views.crear_producto, name='crear_producto'),
    path('productos/<int:producto_id>/', views.detalle_producto, name='detalle_producto'),
    path('productos/<int:producto_id>/editar/', views.editar_producto, name='editar_producto'),
    path('productos/<int:producto_id>/eliminar/', views.eliminar_producto, name='eliminar_producto'),
    path('productos/<int:producto_id>/imprimir-etiqueta/', views.imprimir_etiqueta, name='imprimir_etiqueta'),
    
    # Movimientos
    path('movimientos/', views.lista_movimientos, name='lista_movimientos'),
    path('movimientos/crear/', views.crear_movimiento, name='crear_movimiento'),
    path('movimientos/<uuid:movimiento_id>/', views.detalle_movimiento, name='detalle_movimiento'),
    path('movimientos/<uuid:movimiento_id>/editar/', views.editar_movimiento, name='editar_movimiento'),
    path('movimientos/<uuid:movimiento_id>/eliminar/', views.eliminar_movimiento, name='eliminar_movimiento'),
    
    # Reportes
    path('reportes/', views.reportes, name='reportes'),
    path('reportes/<int:reporte_id>/descargar/', views.descargar_reporte, name='descargar_reporte'),
    path('reportes/<int:reporte_id>/eliminar/', views.eliminar_reporte, name='eliminar_reporte'),
    
    # Gestión (solo admin)
    path('usuarios/', views.gestion_usuarios, name='gestion_usuarios'),
    path('usuarios/crear/', views.crear_usuario, name='crear_usuario'),
    path('usuarios/<int:usuario_id>/', views.detalle_usuario, name='detalle_usuario'),
    path('usuarios/<int:usuario_id>/editar/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/<int:usuario_id>/eliminar/', views.eliminar_usuario, name='eliminar_usuario'),
    path('configuracion/', views.configuracion_sistema, name='configuracion_sistema'),
    
    # URLs para gestión de categorías
    path('categorias/', views.lista_categorias, name='lista_categorias'),
    path('categorias/crear/', views.crear_categoria, name='crear_categoria'),
    path('categorias/<int:categoria_id>/editar/', views.editar_categoria, name='editar_categoria'),
    path('categorias/<int:categoria_id>/eliminar/', views.eliminar_categoria, name='eliminar_categoria'),
    
    # URLs para gestión de sedes
    path('sedes/', views.lista_sedes, name='lista_sedes'),
    path('sedes/crear/', views.crear_sede, name='crear_sede'),
    path('sedes/<int:sede_id>/editar/', views.editar_sede, name='editar_sede'),
    path('sedes/<int:sede_id>/eliminar/', views.eliminar_sede, name='eliminar_sede'),
    
    # URLs para gestión de áreas
    path('areas/', views.lista_areas, name='lista_areas'),
    path('areas/crear/', views.crear_area, name='crear_area'),
    path('areas/<int:area_id>/editar/', views.editar_area, name='editar_area'),
    path('areas/<int:area_id>/eliminar/', views.eliminar_area, name='eliminar_area'),
    
    # URLs para gestión de personal
    path('personal/', views.lista_personal, name='lista_personal'),
    path('personal/crear/', views.crear_personal, name='crear_personal'),
    path('personal/<int:personal_id>/editar/', views.editar_personal, name='editar_personal'),
    path('personal/<int:personal_id>/eliminar/', views.eliminar_personal, name='eliminar_personal'),
    
    # URLs para gestión de licencias
    path('licencias/', views.lista_licencias, name='lista_licencias'),
    path('licencias/crear/', views.crear_licencia, name='crear_licencia'),
    path('licencias/<int:licencia_id>/editar/', views.editar_licencia, name='editar_licencia'),
    path('licencias/<int:licencia_id>/eliminar/', views.eliminar_licencia, name='eliminar_licencia'),
    path('licencias/<int:licencia_id>/detalle/', views.detalle_licencia, name='detalle_licencia'),
    path('gestion-licencias/', views.gestion_licencias, name='gestion_licencias'),
    path('productos/<int:producto_id>/asignar-licencia/', views.asignar_licencia_producto, name='asignar_licencia_producto'),
    path('productos/<int:producto_id>/quitar-licencia/<int:licencia_id>/', views.quitar_licencia_producto, name='quitar_licencia_producto'),
    
    # APIs
    path('api/productos/', views.api_productos, name='api_productos'),
    path('api/movimientos/', views.api_movimientos, name='api_movimientos'),
    path('api/generar-codigo/', views.api_generar_codigo, name='api_generar_codigo'),
    path('api/areas-por-sede/', views.api_areas_por_sede, name='api_areas_por_sede'),
    path('api/personal-por-area/', views.api_personal_por_area, name='api_personal_por_area'),
    path('api/licencias/<int:licencia_id>/clave/', views.api_get_license_key, name='api_get_license_key'),
    
    # URLs para gestión de cuentas
    path('cuentas/', views.lista_cuentas, name='lista_cuentas'),
    path('cuentas/crear/', views.crear_cuenta, name='crear_cuenta'),
    path('cuentas/<int:cuenta_id>/', views.detalle_cuenta, name='detalle_cuenta'),
    path('cuentas/<int:cuenta_id>/editar/', views.editar_cuenta, name='editar_cuenta'),
    path('cuentas/<int:cuenta_id>/eliminar/', views.eliminar_cuenta, name='eliminar_cuenta'),
    path('gestion-cuentas/', views.gestion_cuentas, name='gestion_cuentas'),
] 