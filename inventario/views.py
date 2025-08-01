import os
import json
from datetime import datetime, timedelta
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Sum, Count, F
from django.utils import timezone
from django.core.paginator import Paginator
from django.db import models
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django import forms
import barcode
from barcode.writer import ImageWriter
import base64
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
import tempfile

from .models import (
    Usuario, Categoria, Sede, Area, Personal, Producto, 
    Movimiento, TipoMovimiento, Licencia, ProductoLicencia, Reporte, ConfiguracionSistema, Cuenta,
    PlanificacionSemanal, ConexionWinbox
)
from .forms import (
    CategoriaForm, SedeForm, AreaForm, PersonalForm, LicenciaForm, AsignarLicenciaForm, CuentaForm,
    PlanificacionSemanalForm, ConexionWinboxForm
)


def is_admin(user):
    """Verifica si el usuario es administrador"""
    return user.is_authenticated and user.rol == 'admin'


def is_user_or_admin(user):
    """Verifica si el usuario es usuario normal o administrador"""
    return user.is_authenticated


class LoginForm(forms.Form):
    """Formulario de login personalizado"""
    username = forms.CharField(
        label='Usuario',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su usuario'
        })
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su contraseña'
        })
    )


def login_view(request):
    """Vista de login"""
    if request.user.is_authenticated:
        return redirect('inventario:dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'¡Bienvenido {user.get_full_name()}!')
                return redirect('inventario:dashboard')
            else:
                messages.error(request, 'Usuario o contraseña incorrectos')
    else:
        form = LoginForm()
    
    return render(request, 'inventario/login.html', {'form': form})


def logout_view(request):
    """Vista de logout"""
    logout(request)
    messages.info(request, 'Has cerrado sesión exitosamente')
    return redirect('inventario:login')


@login_required
def dashboard(request):
    """Dashboard principal"""
    # Estadísticas generales
    total_productos = Producto.objects.count()
    total_categorias = Categoria.objects.count()
    total_movimientos = Movimiento.objects.count()
    total_usuarios = Usuario.objects.count()
    
    # Productos con stock bajo (menos de 5 unidades)
    productos_stock_bajo = Producto.objects.filter(cantidad__lt=5).count()
    
    # Movimientos recientes
    movimientos_recientes = Movimiento.objects.select_related(
        'producto', 'tipo_movimiento', 'usuario'
    ).order_by('-fecha_movimiento')[:10]
    
    # Valor total del inventario
    valor_total = float(sum(
        (producto.precio_unitario or 0) * (producto.cantidad or 0)
        for producto in Producto.objects.all()
    ))
    
    # Productos por categoría (para gráfico)
    productos_por_categoria = Categoria.objects.annotate(
        total_productos=Count('productos')
    ).values('nombre', 'total_productos').order_by('nombre')
    
    context = {
        'total_productos': total_productos,
        'total_categorias': total_categorias,
        'total_movimientos': total_movimientos,
        'total_usuarios': total_usuarios,
        'productos_stock_bajo': productos_stock_bajo,
        'movimientos_recientes': movimientos_recientes,
        'valor_total': valor_total,
        'productos_por_categoria': json.dumps(list(productos_por_categoria)),
    }
    
    return render(request, 'inventario/dashboard.html', context)


@login_required
def lista_productos(request):
    """Lista de productos con filtros y búsqueda"""
    productos = Producto.objects.select_related('categoria').all()
    
    # Filtros
    categoria_id = request.GET.get('categoria')
    estado = request.GET.get('estado')
    tipo_propiedad = request.GET.get('tipo_propiedad')
    search = request.GET.get('search')
    
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    
    if estado:
        productos = productos.filter(estado=estado)
    
    if tipo_propiedad:
        productos = productos.filter(tipo_propiedad=tipo_propiedad)
    
    if search:
        productos = productos.filter(
            Q(nombre__icontains=search) |
            Q(codigo__icontains=search) |
            Q(marca__icontains=search) |
            Q(modelo__icontains=search)
        )
    
    # Paginación
    paginator = Paginator(productos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categorias = Categoria.objects.all()
    
    context = {
        'page_obj': page_obj,
        'categorias': categorias,
        'filtros': {
            'categoria': categoria_id,
            'estado': estado,
            'tipo_propiedad': tipo_propiedad,
            'search': search,
        }
    }
    
    return render(request, 'inventario/lista_productos.html', context)


@login_required
def detalle_producto(request, producto_id):
    """Detalle de un producto específico"""
    producto = get_object_or_404(Producto, id=producto_id)
    movimientos = producto.movimientos.select_related(
        'tipo_movimiento', 'usuario'
    ).order_by('-fecha_movimiento')[:20]
    
    # Generar código de barras
    codigo_barras = generar_codigo_barras(producto.codigo)
    
    # Calcular estado del alquiler si es un producto alquilado
    estado_alquiler = None
    if producto.tipo_propiedad == 'alquilado' and producto.fecha_vencimiento_alquiler:
        today = timezone.now().date()
        vencimiento = producto.fecha_vencimiento_alquiler
        
        if vencimiento < today:
            estado_alquiler = {
                'texto': 'Ya venció',
                'clase': 'bg-danger',
                'icono': 'fas fa-times-circle'
            }
        elif vencimiento == today:
            estado_alquiler = {
                'texto': 'Vence hoy',
                'clase': 'bg-warning',
                'icono': 'fas fa-exclamation-triangle'
            }
        else:
            # Calcular días hasta el vencimiento
            dias_restantes = (vencimiento - today).days
            if dias_restantes <= 7:
                estado_alquiler = {
                    'texto': 'Por vencer',
                    'clase': 'bg-warning',
                    'icono': 'fas fa-clock'
                }
            else:
                estado_alquiler = {
                    'texto': 'En vigencia',
                    'clase': 'bg-success',
                    'icono': 'fas fa-check-circle'
                }
    
    context = {
        'producto': producto,
        'movimientos': movimientos,
        'codigo_barras': codigo_barras,
        'today': timezone.now().date(),
        'estado_alquiler': estado_alquiler,
    }
    
    return render(request, 'inventario/detalle_producto.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def eliminar_producto(request, producto_id):
    """Eliminar producto"""
    try:
        producto = get_object_or_404(Producto, id=producto_id)
        nombre = producto.nombre
        codigo = producto.codigo
        
        # Verificar si hay movimientos asociados
        movimientos_count = producto.movimientos.count()
        if movimientos_count > 0:
            messages.error(request, f'No se puede eliminar el producto "{nombre}" porque tiene {movimientos_count} movimiento(s) asociado(s).')
        else:
            producto.delete()
            messages.success(request, f'Producto "{nombre}" (código: {codigo}) eliminado exitosamente.')
            
    except Producto.DoesNotExist:
        messages.error(request, 'Producto no encontrado.')
    except Exception as e:
        messages.error(request, f'Error al eliminar el producto: {str(e)}')
    
    return redirect('inventario:lista_productos')


@login_required
def crear_producto(request):
    """Crear nuevo producto"""
    if request.method == 'POST':
        # Obtener datos del formulario
        codigo = request.POST.get('codigo', '').strip()
        nombre = request.POST.get('nombre')
        categoria_id = request.POST.get('categoria')
        cantidad = request.POST.get('cantidad', 0)
        precio_unitario = request.POST.get('precio_unitario', 0)
        marca = request.POST.get('marca', '')
        modelo = request.POST.get('modelo', '')
        serie = request.POST.get('numero_serie', '')
        proveedor = request.POST.get('proveedor', '')
        estado = request.POST.get('estado', 'activo')
        fecha_adquisicion = request.POST.get('fecha_adquisicion')
        garantia_hasta = request.POST.get('garantia_hasta')
        ubicacion = request.POST.get('ubicacion', '')
        descripcion = request.POST.get('descripcion', '')
        observaciones = request.POST.get('observaciones', '')
        
        # Nuevos campos
        sede_id = request.POST.get('sede')
        area_id = request.POST.get('area')
        personal_asignado_id = request.POST.get('personal_asignado')
        tipo_propiedad = request.POST.get('tipo_propiedad', 'propio')
        codigo_alquiler = request.POST.get('codigo_alquiler', '')
        fecha_alquiler = request.POST.get('fecha_alquiler')
        fecha_vencimiento_alquiler = request.POST.get('fecha_vencimiento_alquiler')
        sistema_operativo = request.POST.get('sistema_operativo', '')
        antivirus = request.POST.get('antivirus') == 'on'
        antivirus_nombre = request.POST.get('antivirus_nombre', '')
        
        try:
            categoria = Categoria.objects.get(id=categoria_id)
            
            # Si no se proporcionó código, generarlo automáticamente
            if not codigo:
                if tipo_propiedad == 'alquilado':
                    # Para productos alquilados, usar el código de alquiler
                    if codigo_alquiler:
                        codigo = codigo_alquiler
                    else:
                        messages.error(request, 'Para productos alquilados, debe proporcionar el código de alquiler')
                        raise ValueError('Código de alquiler requerido para productos alquilados')
                else:
                    # Para productos propios, generar código automáticamente
                    codigo = generar_codigo_producto(categoria)
            
            # Obtener objetos relacionados
            sede = None
            area = None
            personal_asignado = None
            
            if sede_id:
                sede = Sede.objects.get(id=sede_id)
            if area_id:
                area = Area.objects.get(id=area_id)
            if personal_asignado_id:
                personal_asignado = Personal.objects.get(id=personal_asignado_id)
            
            # Crear el producto
            producto = Producto.objects.create(
                codigo=codigo,
                nombre=nombre,
                categoria=categoria,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                marca=marca,
                modelo=modelo,
                serie=serie,
                proveedor=proveedor,
                estado=estado,
                fecha_adquisicion=fecha_adquisicion if fecha_adquisicion else None,
                garantia_hasta=garantia_hasta if garantia_hasta else None,
                ubicacion=ubicacion,
                descripcion=descripcion,
                observaciones=observaciones,
                # Nuevos campos
                sede=sede,
                area=area,
                personal_asignado=personal_asignado,
                tipo_propiedad=tipo_propiedad,
                codigo_alquiler=codigo_alquiler if tipo_propiedad == 'alquilado' else '',
                fecha_alquiler=fecha_alquiler if fecha_alquiler and tipo_propiedad == 'alquilado' else None,
                fecha_vencimiento_alquiler=fecha_vencimiento_alquiler if fecha_vencimiento_alquiler and tipo_propiedad == 'alquilado' else None,
                sistema_operativo=sistema_operativo,
                antivirus=antivirus,
                antivirus_nombre=antivirus_nombre if antivirus else ''
            )
            
            messages.success(request, f'Producto "{producto.nombre}" creado exitosamente con código {producto.codigo}')
            return redirect('inventario:lista_productos')
            
        except Categoria.DoesNotExist:
            messages.error(request, 'Categoría no encontrada')
        except Sede.DoesNotExist:
            messages.error(request, 'Sede no encontrada')
        except Area.DoesNotExist:
            messages.error(request, 'Área no encontrada')
        except Personal.DoesNotExist:
            messages.error(request, 'Personal no encontrado')
        except Exception as e:
            messages.error(request, f'Error al crear el producto: {str(e)}')
    
    categorias = Categoria.objects.all().order_by('nombre')
    sedes = Sede.objects.filter(activo=True).order_by('nombre')
    
    # Obtener datos iniciales para mostrar al usuario
    sedes_con_areas = []
    for sede in sedes:
        areas_count = Area.objects.filter(sede=sede, activo=True).count()
        sedes_con_areas.append({
            'sede': sede,
            'areas_count': areas_count
        })
    
    context = {
        'categorias': categorias,
        'sedes': sedes,
        'sedes_con_areas': sedes_con_areas,
    }
    
    return render(request, 'inventario/crear_producto.html', context)


@login_required
def editar_producto(request, producto_id):
    """Editar producto existente"""
    producto = get_object_or_404(Producto, id=producto_id)
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            codigo = request.POST.get('codigo', '').strip()
            nombre = request.POST.get('nombre', '').strip()
            categoria_id = request.POST.get('categoria')
            marca = request.POST.get('marca', '').strip()
            modelo = request.POST.get('modelo', '').strip()
            serie = request.POST.get('serie', '').strip()
            cantidad = int(request.POST.get('cantidad', 0))
            estado = request.POST.get('estado')
            precio_unitario = Decimal(request.POST.get('precio_unitario', 0))
            fecha_adquisicion = request.POST.get('fecha_adquisicion')
            proveedor = request.POST.get('proveedor', '').strip()
            garantia_hasta = request.POST.get('garantia_hasta')
            ubicacion = request.POST.get('ubicacion', '').strip()
            descripcion = request.POST.get('descripcion', '').strip()
            observaciones = request.POST.get('observaciones', '').strip()
            
            # Campos específicos de alquiler
            tipo_propiedad = request.POST.get('tipo_propiedad', 'propio')
            codigo_alquiler = request.POST.get('codigo_alquiler', '')
            fecha_alquiler = request.POST.get('fecha_alquiler')
            fecha_vencimiento_alquiler = request.POST.get('fecha_vencimiento_alquiler')
            
            # Software y sistema
            sistema_operativo = request.POST.get('sistema_operativo', '')
            antivirus = request.POST.get('antivirus') == 'on'
            
            # Validaciones básicas
            if not codigo or not nombre or not categoria_id or cantidad < 0 or not estado or precio_unitario < 0:
                messages.error(request, 'Por favor complete todos los campos obligatorios correctamente.')
                raise ValueError('Campos obligatorios incompletos')
            
            # Obtener objetos relacionados
            categoria = Categoria.objects.get(id=categoria_id)
            
            # Validar código único (excluyendo el producto actual)
            if Producto.objects.filter(codigo=codigo).exclude(id=producto.id).exists():
                messages.error(request, 'El código ya existe en otro producto.')
                raise ValueError('Código duplicado')
            
            # Si no se proporcionó código, generarlo automáticamente
            if not codigo:
                if tipo_propiedad == 'alquilado':
                    # Para productos alquilados, usar el código de alquiler
                    if codigo_alquiler:
                        codigo = codigo_alquiler
                    else:
                        messages.error(request, 'Para productos alquilados, debe proporcionar el código de alquiler')
                        raise ValueError('Código de alquiler requerido para productos alquilados')
                else:
                    # Para productos propios, generar código automáticamente
                    codigo = generar_codigo_producto(categoria)
            
            # Actualizar el producto
            producto.codigo = codigo
            producto.nombre = nombre
            producto.categoria = categoria
            producto.marca = marca
            producto.modelo = modelo
            producto.serie = serie
            producto.cantidad = cantidad
            producto.estado = estado
            producto.precio_unitario = precio_unitario
            producto.fecha_adquisicion = fecha_adquisicion if fecha_adquisicion else None
            producto.proveedor = proveedor
            producto.garantia_hasta = garantia_hasta if garantia_hasta else None
            producto.ubicacion = ubicacion
            producto.descripcion = descripcion
            producto.observaciones = observaciones
            producto.tipo_propiedad = tipo_propiedad
            producto.codigo_alquiler = codigo_alquiler if tipo_propiedad == 'alquilado' else ''
            producto.fecha_alquiler = fecha_alquiler if fecha_alquiler and tipo_propiedad == 'alquilado' else None
            producto.fecha_vencimiento_alquiler = fecha_vencimiento_alquiler if fecha_vencimiento_alquiler and tipo_propiedad == 'alquilado' else None
            producto.sistema_operativo = sistema_operativo
            producto.antivirus = antivirus
            
            producto.save()
            
            messages.success(request, 'Producto actualizado exitosamente')
            return redirect('inventario:detalle_producto', producto_id=producto.id)
            
        except (ValueError, Producto.DoesNotExist, Categoria.DoesNotExist) as e:
            messages.error(request, f'Error al actualizar el producto: {str(e)}')
        except Exception as e:
            messages.error(request, f'Error inesperado: {str(e)}')
    
    categorias = Categoria.objects.all()
    context = {
        'producto': producto,
        'categorias': categorias,
    }
    
    return render(request, 'inventario/editar_producto.html', context)


@login_required
def lista_movimientos(request):
    """Lista de movimientos con filtros"""
    movimientos = Movimiento.objects.select_related(
        'producto', 'tipo_movimiento', 'usuario'
    ).all()
    
    # Filtros
    producto_id = request.GET.get('producto')
    tipo_movimiento_id = request.GET.get('tipo_movimiento')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if producto_id:
        movimientos = movimientos.filter(producto_id=producto_id)
    
    if tipo_movimiento_id:
        movimientos = movimientos.filter(tipo_movimiento_id=tipo_movimiento_id)
    
    if fecha_desde:
        movimientos = movimientos.filter(fecha_movimiento__date__gte=fecha_desde)
    
    if fecha_hasta:
        movimientos = movimientos.filter(fecha_movimiento__date__lte=fecha_hasta)
    
    # Paginación
    paginator = Paginator(movimientos, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    productos = Producto.objects.all()
    tipos_movimiento = TipoMovimiento.objects.all()
    
    context = {
        'page_obj': page_obj,
        'productos': productos,
        'tipos_movimiento': tipos_movimiento,
        'filtros': {
            'producto': producto_id,
            'tipo_movimiento': tipo_movimiento_id,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
        }
    }
    
    return render(request, 'inventario/lista_movimientos.html', context)


@login_required
def crear_movimiento(request):
    """Crear nuevo movimiento"""
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            producto_id = request.POST.get('producto')
            tipo_movimiento_id = request.POST.get('tipo_movimiento')
            cantidad = int(request.POST.get('cantidad', 0))
            motivo = request.POST.get('motivo', '')
            referencia = request.POST.get('referencia', '')
            
            # Ubicaciones origen y destino
            sede_origen_id = request.POST.get('sede_origen')
            area_origen_id = request.POST.get('area_origen')
            sede_destino_id = request.POST.get('sede_destino')
            area_destino_id = request.POST.get('area_destino')
            
            # Personal responsable
            personal_origen_id = request.POST.get('personal_origen')
            personal_destino_id = request.POST.get('personal_destino')
            
            # Obtener objetos relacionados
            producto = Producto.objects.get(id=producto_id)
            tipo_movimiento = TipoMovimiento.objects.get(id=tipo_movimiento_id)
            
            sede_origen = None
            area_origen = None
            sede_destino = None
            area_destino = None
            personal_origen = None
            personal_destino = None
            
            if sede_origen_id:
                sede_origen = Sede.objects.get(id=sede_origen_id)
            if area_origen_id:
                area_origen = Area.objects.get(id=area_origen_id)
            if sede_destino_id:
                sede_destino = Sede.objects.get(id=sede_destino_id)
            if area_destino_id:
                area_destino = Area.objects.get(id=area_destino_id)
            if personal_origen_id:
                personal_origen = Personal.objects.get(id=personal_origen_id)
            if personal_destino_id:
                personal_destino = Personal.objects.get(id=personal_destino_id)
            
            # Calcular cantidades
            cantidad_anterior = producto.cantidad
            if tipo_movimiento.es_entrada:
                cantidad_nueva = cantidad_anterior + cantidad
            else:
                cantidad_nueva = cantidad_anterior - cantidad
            
            # Crear el movimiento
            movimiento = Movimiento.objects.create(
                producto=producto,
                tipo_movimiento=tipo_movimiento,
                cantidad=cantidad,
                cantidad_anterior=cantidad_anterior,
                cantidad_nueva=cantidad_nueva,
                usuario=request.user,
                motivo=motivo,
                referencia=referencia,
                sede_origen=sede_origen,
                area_origen=area_origen,
                sede_destino=sede_destino,
                area_destino=area_destino,
                personal_origen=personal_origen,
                personal_destino=personal_destino
            )
            
            # Actualizar cantidad del producto
            producto.cantidad = cantidad_nueva
            producto.save()
            
            messages.success(request, f'Movimiento registrado exitosamente. Stock actual: {producto.cantidad}')
            return redirect('inventario:lista_movimientos')
            
        except Producto.DoesNotExist:
            messages.error(request, 'Producto no encontrado')
        except TipoMovimiento.DoesNotExist:
            messages.error(request, 'Tipo de movimiento no encontrado')
        except Sede.DoesNotExist:
            messages.error(request, 'Sede no encontrada')
        except Area.DoesNotExist:
            messages.error(request, 'Área no encontrada')
        except Personal.DoesNotExist:
            messages.error(request, 'Personal no encontrado')
        except Exception as e:
            messages.error(request, f'Error al crear el movimiento: {str(e)}')
    
    productos = Producto.objects.all().order_by('nombre')
    tipos_movimiento = TipoMovimiento.objects.filter(activo=True).order_by('nombre')
    sedes = Sede.objects.filter(activo=True).order_by('nombre')
    areas = Area.objects.filter(activo=True).order_by('sede__nombre', 'nombre')
    personal = Personal.objects.filter(activo=True).order_by('apellido', 'nombre')
    
    context = {
        'productos': productos,
        'tipos_movimiento': tipos_movimiento,
        'sedes': sedes,
        'areas': areas,
        'personal': personal,
    }
    
    return render(request, 'inventario/crear_movimiento.html', context)


@login_required
def reportes(request):
    """Página de reportes"""
    # Obtener reportes recientes
    reportes_recientes = Reporte.objects.select_related('usuario').order_by('-fecha_generacion')[:10]
    
    # Obtener datos para los filtros
    categorias = Categoria.objects.all()
    tipos_movimiento = TipoMovimiento.objects.all()
    
    # Estadísticas para las tarjetas
    total_productos = Producto.objects.count()
    valor_total = sum(p.valor_total for p in Producto.objects.all())
    movimientos_hoy = Movimiento.objects.filter(
        fecha_movimiento__date=timezone.now().date()
    ).count()
    stock_bajo = Producto.objects.filter(cantidad__lt=5).count()
    
    if request.method == 'POST':
        tipo_reporte = request.POST.get('tipo_reporte')
        
        if tipo_reporte == 'inventario':
            return generar_reporte_inventario(request)
        elif tipo_reporte == 'movimientos':
            return generar_reporte_movimientos(request)
        elif tipo_reporte == 'categoria':
            return generar_reporte_categoria(request)
    
    context = {
        'reportes_recientes': reportes_recientes,
        'categorias': categorias,
        'tipos_movimiento': tipos_movimiento,
        'total_productos': total_productos,
        'valor_total': valor_total,
        'movimientos_hoy': movimientos_hoy,
        'stock_bajo': stock_bajo,
    }
    
    return render(request, 'inventario/reportes.html', context)


def crear_pdf_inventario(productos, filtros=None):
    """Crear PDF del reporte de inventario"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Título
    story.append(Paragraph("REPORTE DE INVENTARIO", title_style))
    story.append(Spacer(1, 20))
    
    # Información del reporte
    if filtros:
        info_text = f"<b>Fecha de generación:</b> {timezone.now().strftime('%d/%m/%Y %H:%M')}<br/>"
        if filtros.get('categoria'):
            categoria = Categoria.objects.get(id=filtros['categoria'])
            info_text += f"<b>Categoría:</b> {categoria.nombre}<br/>"
        if filtros.get('estado'):
            info_text += f"<b>Estado:</b> {filtros['estado']}<br/>"
        story.append(Paragraph(info_text, styles['Normal']))
        story.append(Spacer(1, 20))
    
    # Tabla de productos
    data = [['Código', 'Nombre', 'Categoría', 'Cantidad', 'Precio Unit.', 'Valor Total', 'Estado']]
    
    valor_total_inventario = 0
    for producto in productos:
        valor_producto = (producto.precio_unitario or 0) * (producto.cantidad or 0)
        valor_total_inventario += valor_producto
        
        data.append([
            producto.codigo,
            producto.nombre,
            producto.categoria.nombre,
            str(producto.cantidad),
            f"${producto.precio_unitario or 0:,.2f}",
            f"${valor_producto:,.2f}",
            producto.get_estado_display()
        ])
    
    # Agregar total
    data.append(['', '', '<b>TOTAL</b>', '', '', f'<b>${valor_total_inventario:,.2f}</b>', ''])
    
    table = Table(data, colWidths=[1*inch, 2*inch, 1.5*inch, 0.8*inch, 1*inch, 1.2*inch, 1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 20))
    
    # Resumen
    resumen_text = f"""
    <b>Resumen del Reporte:</b><br/>
    • Total de productos: {productos.count()}<br/>
    • Valor total del inventario: ${valor_total_inventario:,.2f}<br/>
    • Productos con stock bajo: {productos.filter(cantidad__lt=5).count()}<br/>
    """
    story.append(Paragraph(resumen_text, styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer


def crear_pdf_movimientos(movimientos, filtros=None):
    """Crear PDF del reporte de movimientos"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Título
    story.append(Paragraph("REPORTE DE MOVIMIENTOS", title_style))
    story.append(Spacer(1, 20))
    
    # Información del reporte
    if filtros:
        info_text = f"<b>Fecha de generación:</b> {timezone.now().strftime('%d/%m/%Y %H:%M')}<br/>"
        if filtros.get('fecha_desde'):
            info_text += f"<b>Desde:</b> {filtros['fecha_desde']}<br/>"
        if filtros.get('fecha_hasta'):
            info_text += f"<b>Hasta:</b> {filtros['fecha_hasta']}<br/>"
        if filtros.get('tipo_movimiento'):
            tipo = TipoMovimiento.objects.get(id=filtros['tipo_movimiento'])
            info_text += f"<b>Tipo de movimiento:</b> {tipo.nombre}<br/>"
        story.append(Paragraph(info_text, styles['Normal']))
        story.append(Spacer(1, 20))
    
    # Tabla de movimientos
    data = [['Fecha', 'Producto', 'Tipo', 'Cantidad', 'Usuario', 'Motivo']]
    
    for movimiento in movimientos:
        data.append([
            movimiento.fecha_movimiento.strftime('%d/%m/%Y %H:%M'),
            movimiento.producto.nombre,
            movimiento.tipo_movimiento.nombre,
            str(movimiento.cantidad),
            movimiento.usuario.get_full_name(),
            movimiento.motivo[:50] + '...' if len(movimiento.motivo) > 50 else movimiento.motivo
        ])
    
    table = Table(data, colWidths=[1.2*inch, 2*inch, 1*inch, 0.8*inch, 1.5*inch, 2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 20))
    
    # Resumen
    resumen_text = f"""
    <b>Resumen del Reporte:</b><br/>
    • Total de movimientos: {movimientos.count()}<br/>
    • Entradas: {movimientos.filter(tipo_movimiento__es_entrada=True).count()}<br/>
    • Salidas: {movimientos.filter(tipo_movimiento__es_entrada=False).count()}<br/>
    """
    story.append(Paragraph(resumen_text, styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer


def crear_pdf_categoria(productos, filtros=None):
    """Crear PDF del reporte por categoría"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Título
    story.append(Paragraph("REPORTE POR CATEGORÍA", title_style))
    story.append(Spacer(1, 20))
    
    # Información del reporte
    if filtros:
        info_text = f"<b>Fecha de generación:</b> {timezone.now().strftime('%d/%m/%Y %H:%M')}<br/>"
        if filtros.get('categoria'):
            categoria = Categoria.objects.get(id=filtros['categoria'])
            info_text += f"<b>Categoría:</b> {categoria.nombre}<br/>"
        if filtros.get('orden'):
            orden_text = {
                'mayor_menor': 'Cantidad (Mayor a Menor)',
                'menor_mayor': 'Cantidad (Menor a Mayor)',
                'valor': 'Valor (Mayor a Menor)'
            }.get(filtros['orden'], filtros['orden'])
            info_text += f"<b>Orden:</b> {orden_text}<br/>"
        story.append(Paragraph(info_text, styles['Normal']))
        story.append(Spacer(1, 20))
    
    # Tabla de productos
    data = [['Código', 'Nombre', 'Categoría', 'Cantidad', 'Precio Unit.', 'Valor Total']]
    
    valor_total = 0
    for producto in productos:
        valor_producto = (producto.precio_unitario or 0) * (producto.cantidad or 0)
        valor_total += valor_producto
        
        data.append([
            producto.codigo,
            producto.nombre,
            producto.categoria.nombre,
            str(producto.cantidad),
            f"${producto.precio_unitario or 0:,.2f}",
            f"${valor_producto:,.2f}"
        ])
    
    # Agregar total
    data.append(['', '', '<b>TOTAL</b>', '', '', f'<b>${valor_total:,.2f}</b>'])
    
    table = Table(data, colWidths=[1*inch, 2*inch, 1.5*inch, 0.8*inch, 1*inch, 1.2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 20))
    
    # Resumen
    resumen_text = f"""
    <b>Resumen del Reporte:</b><br/>
    • Total de productos: {productos.count()}<br/>
    • Valor total: ${valor_total:,.2f}<br/>
    """
    story.append(Paragraph(resumen_text, styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer


def generar_reporte_inventario(request):
    """Generar reporte de inventario"""
    try:
        # Obtener filtros
        categoria_id = request.POST.get('categoria')
        estado = request.POST.get('estado')
        
        # Filtrar productos
        productos = Producto.objects.select_related('categoria').all()
        
        if categoria_id:
            productos = productos.filter(categoria_id=categoria_id)
        
        if estado and estado != 'todos':
            productos = productos.filter(estado=estado)
        
        # Crear PDF
        filtros = {
            'categoria': categoria_id,
            'estado': estado
        }
        pdf_buffer = crear_pdf_inventario(productos, filtros)
        
        # Crear reporte en la base de datos
        nombre_reporte = f"Reporte_Inventario_{timezone.now().strftime('%Y-%m-%d_%H-%M')}"
        
        # Guardar archivo PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(pdf_buffer.getvalue())
            tmp_file_path = tmp_file.name
        
        # Crear objeto Reporte
        valor_total = float(sum((p.precio_unitario or 0) * (p.cantidad or 0) for p in productos))
        reporte = Reporte.objects.create(
            nombre=nombre_reporte,
            tipo='inventario',
            usuario=request.user,
            parametros={
                'categoria_id': categoria_id,
                'estado': estado,
                'total_productos': productos.count(),
                'valor_total': valor_total
            }
        )
        
        # Guardar archivo en el modelo
        with open(tmp_file_path, 'rb') as f:
            reporte.archivo.save(f'{nombre_reporte}.pdf', f, save=True)
        
        # Limpiar archivo temporal
        os.unlink(tmp_file_path)
        
        messages.success(request, f'Reporte "{nombre_reporte}" generado exitosamente')
        
    except Exception as e:
        messages.error(request, f'Error al generar el reporte: {str(e)}')
    
    return redirect('inventario:reportes')


def generar_reporte_movimientos(request):
    """Generar reporte de movimientos"""
    try:
        # Obtener filtros
        fecha_desde = request.POST.get('fecha_desde')
        fecha_hasta = request.POST.get('fecha_hasta')
        tipo_movimiento_id = request.POST.get('tipo_movimiento')
        
        # Filtrar movimientos
        movimientos = Movimiento.objects.select_related(
            'producto', 'tipo_movimiento', 'usuario'
        ).all()
        
        if fecha_desde:
            movimientos = movimientos.filter(fecha_movimiento__date__gte=fecha_desde)
        
        if fecha_hasta:
            movimientos = movimientos.filter(fecha_movimiento__date__lte=fecha_hasta)
        
        if tipo_movimiento_id and tipo_movimiento_id != 'todos':
            movimientos = movimientos.filter(tipo_movimiento_id=tipo_movimiento_id)
        
        # Crear PDF
        filtros = {
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'tipo_movimiento': tipo_movimiento_id
        }
        pdf_buffer = crear_pdf_movimientos(movimientos, filtros)
        
        # Crear reporte en la base de datos
        nombre_reporte = f"Reporte_Movimientos_{timezone.now().strftime('%Y-%m-%d_%H-%M')}"
        
        # Guardar archivo PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(pdf_buffer.getvalue())
            tmp_file_path = tmp_file.name
        
        # Crear objeto Reporte
        reporte = Reporte.objects.create(
            nombre=nombre_reporte,
            tipo='movimientos',
            usuario=request.user,
            parametros={
                'fecha_desde': fecha_desde,
                'fecha_hasta': fecha_hasta,
                'tipo_movimiento_id': tipo_movimiento_id,
                'total_movimientos': movimientos.count()
            }
        )
        
        # Guardar archivo en el modelo
        with open(tmp_file_path, 'rb') as f:
            reporte.archivo.save(f'{nombre_reporte}.pdf', f, save=True)
        
        # Limpiar archivo temporal
        os.unlink(tmp_file_path)
        
        messages.success(request, f'Reporte "{nombre_reporte}" generado exitosamente')
        
    except Exception as e:
        messages.error(request, f'Error al generar el reporte: {str(e)}')
    
    return redirect('inventario:reportes')


def generar_reporte_categoria(request):
    """Generar reporte por categoría"""
    try:
        # Obtener filtros
        categoria_id = request.POST.get('categoria')
        orden = request.POST.get('orden', 'mayor_menor')
        
        # Filtrar productos
        productos = Producto.objects.select_related('categoria').all()
        
        if categoria_id and categoria_id != 'todos':
            productos = productos.filter(categoria_id=categoria_id)
        
        # Ordenar productos
        if orden == 'mayor_menor':
            productos = productos.order_by('-cantidad')
        elif orden == 'menor_mayor':
            productos = productos.order_by('cantidad')
        elif orden == 'valor':
            productos = productos.order_by('-precio_unitario')
        
        # Crear PDF
        filtros = {
            'categoria': categoria_id,
            'orden': orden
        }
        pdf_buffer = crear_pdf_categoria(productos, filtros)
        
        # Crear reporte en la base de datos
        nombre_reporte = f"Reporte_Categoria_{timezone.now().strftime('%Y-%m-%d_%H-%M')}"
        
        # Guardar archivo PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(pdf_buffer.getvalue())
            tmp_file_path = tmp_file.name
        
        # Crear objeto Reporte
        valor_total = float(sum((p.precio_unitario or 0) * (p.cantidad or 0) for p in productos))
        reporte = Reporte.objects.create(
            nombre=nombre_reporte,
            tipo='categoria',
            usuario=request.user,
            parametros={
                'categoria_id': categoria_id,
                'orden': orden,
                'total_productos': productos.count(),
                'valor_total': valor_total
            }
        )
        
        # Guardar archivo en el modelo
        with open(tmp_file_path, 'rb') as f:
            reporte.archivo.save(f'{nombre_reporte}.pdf', f, save=True)
        
        # Limpiar archivo temporal
        os.unlink(tmp_file_path)
        
        messages.success(request, f'Reporte "{nombre_reporte}" generado exitosamente')
        
    except Exception as e:
        messages.error(request, f'Error al generar el reporte: {str(e)}')
    
    return redirect('inventario:reportes')


@login_required
def descargar_reporte(request, reporte_id):
    """Descargar reporte generado"""
    try:
        reporte = Reporte.objects.get(id=reporte_id)
        
        if reporte.archivo:
            # Si existe el archivo PDF, devolverlo
            response = HttpResponse(reporte.archivo.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{reporte.nombre}.pdf"'
            return response
        else:
            # Si no existe el archivo, generar uno básico
            messages.warning(request, 'Archivo PDF no encontrado, generando reporte básico...')
            
            # Generar PDF básico según el tipo
            if reporte.tipo == 'inventario':
                productos = Producto.objects.select_related('categoria').all()
                pdf_buffer = crear_pdf_inventario(productos, reporte.parametros)
            elif reporte.tipo == 'movimientos':
                movimientos = Movimiento.objects.select_related('producto', 'tipo_movimiento', 'usuario').all()
                pdf_buffer = crear_pdf_movimientos(movimientos, reporte.parametros)
            elif reporte.tipo == 'categoria':
                productos = Producto.objects.select_related('categoria').all()
                pdf_buffer = crear_pdf_categoria(productos, reporte.parametros)
            else:
                messages.error(request, 'Tipo de reporte no válido')
                return redirect('inventario:reportes')
            
            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{reporte.nombre}.pdf"'
            return response
        
    except Reporte.DoesNotExist:
        messages.error(request, 'Reporte no encontrado')
        return redirect('inventario:reportes')
    except Exception as e:
        messages.error(request, f'Error al descargar el reporte: {str(e)}')
        return redirect('inventario:reportes')


@login_required
def eliminar_reporte(request, reporte_id):
    """Eliminar reporte"""
    try:
        reporte = Reporte.objects.get(id=reporte_id)
        nombre = reporte.nombre
        reporte.delete()
        messages.success(request, f'Reporte "{nombre}" eliminado exitosamente')
        
    except Reporte.DoesNotExist:
        messages.error(request, 'Reporte no encontrado')
    except Exception as e:
        messages.error(request, f'Error al eliminar el reporte: {str(e)}')
    
    return redirect('inventario:reportes')


@user_passes_test(is_admin)
def gestion_usuarios(request):
    """Gestión de usuarios (solo admin)"""
    usuarios = Usuario.objects.all()
    
    context = {
        'usuarios': usuarios,
    }
    
    return render(request, 'inventario/gestion_usuarios.html', context)


@user_passes_test(is_admin)
def crear_usuario(request):
    """Crear nuevo usuario (solo admin)"""
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            rol = request.POST.get('rol')
            departamento = request.POST.get('departamento', '')
            telefono = request.POST.get('telefono', '')
            
            # Validar que el usuario no exista
            if Usuario.objects.filter(username=username).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'El nombre de usuario ya existe.'
                })
            
            # Validar que el email no exista
            if Usuario.objects.filter(email=email).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'El email ya está registrado.'
                })
            
            # Crear el usuario
            usuario = Usuario.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                rol=rol,
                departamento=departamento,
                telefono=telefono
            )
            
            # Asignar permisos según el rol
            if rol == 'admin':
                usuario.is_staff = True
                usuario.is_superuser = True
            else:
                usuario.is_staff = False
                usuario.is_superuser = False
            
            usuario.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Usuario "{username}" creado exitosamente.'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al crear el usuario: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido.'
    })


@user_passes_test(is_admin)
def detalle_usuario(request, usuario_id):
    """Ver detalles de un usuario (solo admin)"""
    try:
        usuario = get_object_or_404(Usuario, id=usuario_id)
        context = {
            'usuario': usuario,
        }
        return render(request, 'inventario/detalle_usuario.html', context)
    except Usuario.DoesNotExist:
        messages.error(request, 'Usuario no encontrado.')
        return redirect('inventario:gestion_usuarios')


@user_passes_test(is_admin)
def editar_usuario(request, usuario_id):
    """Editar usuario (solo admin)"""
    try:
        usuario = get_object_or_404(Usuario, id=usuario_id)
        
        if request.method == 'POST':
            try:
                # Obtener datos del formulario
                username = request.POST.get('username')
                email = request.POST.get('email')
                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')
                rol = request.POST.get('rol')
                departamento = request.POST.get('departamento', '')
                telefono = request.POST.get('telefono', '')
                is_active = request.POST.get('is_active') == 'on'
                
                # Validar que el usuario no exista (excluyendo el usuario actual)
                if Usuario.objects.filter(username=username).exclude(id=usuario_id).exists():
                    return JsonResponse({
                        'success': False,
                        'message': 'El nombre de usuario ya existe.'
                    })
                
                # Validar que el email no exista (excluyendo el usuario actual)
                if Usuario.objects.filter(email=email).exclude(id=usuario_id).exists():
                    return JsonResponse({
                        'success': False,
                        'message': 'El email ya está registrado.'
                    })
                
                # Actualizar el usuario
                usuario.username = username
                usuario.email = email
                usuario.first_name = first_name
                usuario.last_name = last_name
                usuario.rol = rol
                usuario.departamento = departamento
                usuario.telefono = telefono
                usuario.is_active = is_active
                
                # Asignar permisos según el rol
                if rol == 'admin':
                    usuario.is_staff = True
                    usuario.is_superuser = True
                else:
                    usuario.is_staff = False
                    usuario.is_superuser = False
                
                usuario.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Usuario "{username}" actualizado exitosamente.'
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Error al actualizar el usuario: {str(e)}'
                })
        
        context = {
            'usuario': usuario,
        }
        return render(request, 'inventario/editar_usuario.html', context)
        
    except Usuario.DoesNotExist:
        messages.error(request, 'Usuario no encontrado.')
        return redirect('inventario:gestion_usuarios')


@user_passes_test(is_admin)
def eliminar_usuario(request, usuario_id):
    """Eliminar usuario (solo admin)"""
    try:
        usuario = get_object_or_404(Usuario, id=usuario_id)
        
        # No permitir eliminar el usuario actual
        if usuario.id == request.user.id:
            return JsonResponse({
                'success': False,
                'message': 'No puedes eliminar tu propia cuenta.'
            })
        
        username = usuario.username
        usuario.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Usuario "{username}" eliminado exitosamente.'
        })
        
    except Usuario.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Usuario no encontrado.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al eliminar el usuario: {str(e)}'
        })


@user_passes_test(is_admin)
def configuracion_sistema(request):
    """Configuración del sistema (solo admin)"""
    if request.method == 'POST':
        # Aquí iría la lógica para guardar configuraciones
        messages.success(request, 'Configuración actualizada exitosamente')
        return redirect('inventario:configuracion_sistema')
    
    configuraciones = ConfiguracionSistema.objects.all()
    
    context = {
        'configuraciones': configuraciones,
    }
    
    return render(request, 'inventario/configuracion_sistema.html', context)


# APIs para AJAX
@login_required
@csrf_exempt
def api_productos(request):
    """API para obtener productos"""
    if request.method == 'GET':
        productos = Producto.objects.select_related('categoria').all()
        data = []
        
        for producto in productos:
            data.append({
                'id': producto.id,
                'codigo': producto.codigo,
                'nombre': producto.nombre,
                'categoria': producto.categoria.nombre,
                'cantidad': producto.cantidad,
                'estado': producto.estado,
                'valor_total': float(producto.valor_total),
            })
        
        return JsonResponse({'productos': data})
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required
@csrf_exempt
def api_movimientos(request):
    """API para obtener movimientos"""
    if request.method == 'GET':
        movimientos = Movimiento.objects.select_related(
            'producto', 'tipo_movimiento', 'usuario'
        ).order_by('-fecha_movimiento')[:50]
        
        data = []
        for movimiento in movimientos:
            data.append({
                'id': str(movimiento.id),
                'producto': movimiento.producto.nombre,
                'tipo': movimiento.tipo_movimiento.nombre,
                'cantidad': movimiento.cantidad,
                'usuario': movimiento.usuario.get_full_name(),
                'fecha': movimiento.fecha_movimiento.strftime('%d/%m/%Y %H:%M'),
                'motivo': movimiento.motivo,
            })
        
        return JsonResponse({'movimientos': data})
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required
@user_passes_test(lambda u: u.is_staff)
def lista_categorias(request):
    categorias = Categoria.objects.all().order_by('nombre')
    return render(request, 'inventario/lista_categorias.html', {
        'categorias': categorias
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def crear_categoria(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría creada exitosamente.')
            return redirect('inventario:lista_categorias')
    else:
        form = CategoriaForm()
    
    return render(request, 'inventario/crear_categoria.html', {
        'form': form
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def editar_categoria(request, categoria_id):
    try:
        categoria = Categoria.objects.get(id=categoria_id)
    except Categoria.DoesNotExist:
        messages.error(request, 'Categoría no encontrada.')
        return redirect('inventario:lista_categorias')
    
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría actualizada exitosamente.')
            return redirect('inventario:lista_categorias')
    else:
        form = CategoriaForm(instance=categoria)
    
    return render(request, 'inventario/editar_categoria.html', {
        'form': form,
        'categoria': categoria
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def eliminar_categoria(request, categoria_id):
    try:
        categoria = Categoria.objects.get(id=categoria_id)
        # Verificar si hay productos usando esta categoría
        productos_count = Producto.objects.filter(categoria=categoria).count()
        if productos_count > 0:
            messages.error(request, f'No se puede eliminar la categoría "{categoria.nombre}" porque tiene {productos_count} producto(s) asociado(s).')
        else:
            categoria.delete()
            messages.success(request, 'Categoría eliminada exitosamente.')
    except Categoria.DoesNotExist:
        messages.error(request, 'Categoría no encontrada.')
    
    return redirect('inventario:lista_categorias')


# Vistas para gestión de Sedes
@login_required
@user_passes_test(lambda u: u.is_staff)
def lista_sedes(request):
    sedes = Sede.objects.all().order_by('nombre')
    return render(request, 'inventario/lista_sedes.html', {
        'sedes': sedes
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def crear_sede(request):
    if request.method == 'POST':
        form = SedeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sede creada exitosamente.')
            return redirect('inventario:lista_sedes')
    else:
        form = SedeForm()
    
    return render(request, 'inventario/crear_sede.html', {
        'form': form
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def editar_sede(request, sede_id):
    try:
        sede = Sede.objects.get(id=sede_id)
    except Sede.DoesNotExist:
        messages.error(request, 'Sede no encontrada.')
        return redirect('inventario:lista_sedes')
    
    if request.method == 'POST':
        form = SedeForm(request.POST, instance=sede)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sede actualizada exitosamente.')
            return redirect('inventario:lista_sedes')
    else:
        form = SedeForm(instance=sede)
    
    return render(request, 'inventario/editar_sede.html', {
        'form': form,
        'sede': sede
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def eliminar_sede(request, sede_id):
    try:
        sede = Sede.objects.get(id=sede_id)
        # Verificar si hay áreas usando esta sede
        areas_count = Area.objects.filter(sede=sede).count()
        if areas_count > 0:
            messages.error(request, f'No se puede eliminar la sede "{sede.nombre}" porque tiene {areas_count} área(s) asociada(s).')
        else:
            sede.delete()
            messages.success(request, 'Sede eliminada exitosamente.')
    except Sede.DoesNotExist:
        messages.error(request, 'Sede no encontrada.')
    
    return redirect('inventario:lista_sedes')


# Vistas para gestión de Áreas
@login_required
@user_passes_test(lambda u: u.is_staff)
def lista_areas(request):
    areas = Area.objects.select_related('sede').all().order_by('sede', 'nombre')
    return render(request, 'inventario/lista_areas.html', {
        'areas': areas
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def crear_area(request):
    if request.method == 'POST':
        form = AreaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Área creada exitosamente.')
            return redirect('inventario:lista_areas')
    else:
        form = AreaForm()
    
    sedes = Sede.objects.filter(activo=True).order_by('nombre')
    return render(request, 'inventario/crear_area.html', {
        'form': form,
        'sedes': sedes
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def editar_area(request, area_id):
    try:
        area = Area.objects.get(id=area_id)
    except Area.DoesNotExist:
        messages.error(request, 'Área no encontrada.')
        return redirect('inventario:lista_areas')
    
    if request.method == 'POST':
        form = AreaForm(request.POST, instance=area)
        if form.is_valid():
            form.save()
            messages.success(request, 'Área actualizada exitosamente.')
            return redirect('inventario:lista_areas')
    else:
        form = AreaForm(instance=area)
    
    sedes = Sede.objects.filter(activo=True).order_by('nombre')
    return render(request, 'inventario/editar_area.html', {
        'form': form,
        'area': area,
        'sedes': sedes
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def eliminar_area(request, area_id):
    try:
        area = Area.objects.get(id=area_id)
        # Verificar si hay personal usando esta área
        personal_count = Personal.objects.filter(area=area).count()
        if personal_count > 0:
            messages.error(request, f'No se puede eliminar el área "{area.nombre}" porque tiene {personal_count} personal asociado.')
        else:
            area.delete()
            messages.success(request, 'Área eliminada exitosamente.')
    except Area.DoesNotExist:
        messages.error(request, 'Área no encontrada.')
    
    return redirect('inventario:lista_areas')


# Vistas para gestión de Personal
@login_required
@user_passes_test(lambda u: u.is_staff)
def lista_personal(request):
    personal = Personal.objects.select_related('area', 'area__sede').all().order_by('apellido', 'nombre')
    return render(request, 'inventario/lista_personal.html', {
        'personal': personal
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def crear_personal(request):
    if request.method == 'POST':
        form = PersonalForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Personal creado exitosamente.')
            return redirect('inventario:lista_personal')
    else:
        form = PersonalForm()
    
    areas = Area.objects.filter(activo=True).select_related('sede').order_by('sede__nombre', 'nombre')
    return render(request, 'inventario/crear_personal.html', {
        'form': form,
        'areas': areas
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def editar_personal(request, personal_id):
    try:
        personal = Personal.objects.get(id=personal_id)
    except Personal.DoesNotExist:
        messages.error(request, 'Personal no encontrado.')
        return redirect('inventario:lista_personal')
    
    if request.method == 'POST':
        form = PersonalForm(request.POST, instance=personal)
        if form.is_valid():
            form.save()
            messages.success(request, 'Personal actualizado exitosamente.')
            return redirect('inventario:lista_personal')
    else:
        form = PersonalForm(instance=personal)
    
    areas = Area.objects.filter(activo=True).select_related('sede').order_by('sede__nombre', 'nombre')
    return render(request, 'inventario/editar_personal.html', {
        'form': form,
        'personal': personal,
        'areas': areas
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def eliminar_personal(request, personal_id):
    try:
        personal = Personal.objects.get(id=personal_id)
        # Verificar si hay productos asignados a este personal
        productos_count = Producto.objects.filter(personal_asignado=personal).count()
        if productos_count > 0:
            messages.error(request, f'No se puede eliminar el personal "{personal.get_full_name()}" porque tiene {productos_count} producto(s) asignado(s).')
        else:
            personal.delete()
            messages.success(request, 'Personal eliminado exitosamente.')
    except Personal.DoesNotExist:
        messages.error(request, 'Personal no encontrado.')
    
    return redirect('inventario:lista_personal')


# Vistas para gestión de Licencias
@login_required
@user_passes_test(lambda u: u.is_staff)
def lista_licencias(request):
    from datetime import date
    licencias = Licencia.objects.all().order_by('nombre')
    return render(request, 'inventario/lista_licencias.html', {
        'licencias': licencias,
        'today': date.today()
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def crear_licencia(request):
    if request.method == 'POST':
        form = LicenciaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Licencia creada exitosamente.')
            return redirect('inventario:lista_licencias')
    else:
        form = LicenciaForm()
    
    return render(request, 'inventario/crear_licencia.html', {
        'form': form
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def editar_licencia(request, licencia_id):
    try:
        licencia = Licencia.objects.get(id=licencia_id)
    except Licencia.DoesNotExist:
        messages.error(request, 'Licencia no encontrada.')
        return redirect('inventario:lista_licencias')
    
    if request.method == 'POST':
        form = LicenciaForm(request.POST, instance=licencia)
        if form.is_valid():
            form.save()
            messages.success(request, 'Licencia actualizada exitosamente.')
            return redirect('inventario:lista_licencias')
    else:
        form = LicenciaForm(instance=licencia)
    
    return render(request, 'inventario/editar_licencia.html', {
        'form': form,
        'licencia': licencia
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def eliminar_licencia(request, licencia_id):
    try:
        licencia = Licencia.objects.get(id=licencia_id)
        licencia.delete()
        messages.success(request, 'Licencia eliminada exitosamente.')
    except Licencia.DoesNotExist:
        messages.error(request, 'Licencia no encontrada.')
    
    return redirect('inventario:lista_licencias')


def generar_codigo_producto(categoria):
    """Genera un código único para un producto basado en su categoría"""
    # Obtener el último producto de esta categoría
    ultimo_producto = Producto.objects.filter(
        categoria=categoria,
        codigo__startswith=categoria.nombre[:3].upper()
    ).order_by('-codigo').first()
    
    if ultimo_producto:
        # Extraer el número del último código
        try:
            ultimo_numero = int(ultimo_producto.codigo.split('-')[-1])
            nuevo_numero = ultimo_numero + 1
        except (ValueError, IndexError):
            nuevo_numero = 1
    else:
        nuevo_numero = 1
    
    # Generar el nuevo código
    codigo = f"{categoria.nombre[:3].upper()}-{nuevo_numero:05d}"
    return codigo


def generar_codigo_barras(codigo_producto):
    """Genera un código de barras en formato base64"""
    try:
        # Crear el código de barras con opciones personalizadas
        codigo_barras = barcode.Code128(codigo_producto, writer=ImageWriter())
        
        # Generar la imagen con opciones personalizadas
        buffer = BytesIO()
        codigo_barras.write(buffer, options={
            'module_height': 15.0,  # Altura de las barras (más alto)
            'module_width': 0.4,    # Ancho de las barras (más ancho)
            'quiet_zone': 6.0,      # Espacio en blanco a los lados
            'font_size': 0,         # Tamaño de fuente 0 = sin texto
            'text_distance': 0,     # Sin distancia de texto
            'write_text': False,    # No escribir texto debajo de las barras
        })
        buffer.seek(0)
        
        # Convertir a base64
        imagen_base64 = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{imagen_base64}"
    except Exception as e:
        print(f"Error generando código de barras: {e}")
        return None


@login_required
def imprimir_etiqueta(request, producto_id):
    """Vista para imprimir etiqueta de producto"""
    producto = get_object_or_404(Producto, id=producto_id)
    
    # Generar código de barras
    codigo_barras = generar_codigo_barras(producto.codigo)
    
    context = {
        'producto': producto,
        'codigo_barras': codigo_barras,
        'fecha_actual': timezone.now().strftime("%d/%m/%Y"),
        'anio_actual': timezone.now().year,
    }
    
    return render(request, 'inventario/imprimir_etiqueta.html', context)


@login_required
@csrf_exempt
def api_generar_codigo(request):
    """API para generar código automático basado en categoría"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            categoria_id = data.get('categoria_id')
            
            if categoria_id:
                categoria = Categoria.objects.get(id=categoria_id)
                codigo = generar_codigo_producto(categoria)
                print(f"Generando código para categoría {categoria.nombre}: {codigo}")  # Debug
                return JsonResponse({'codigo': codigo})
            else:
                return JsonResponse({'error': 'Categoría no especificada'}, status=400)
                
        except Categoria.DoesNotExist:
            return JsonResponse({'error': 'Categoría no encontrada'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Datos JSON inválidos'}, status=400)
        except Exception as e:
            print(f"Error en api_generar_codigo: {str(e)}")  # Debug
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required
@csrf_exempt
def api_areas_por_sede(request):
    """API para obtener áreas por sede"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            sede_id = data.get('sede_id')
            
            if sede_id:
                areas = Area.objects.filter(sede_id=sede_id, activo=True).values('id', 'nombre')
                print(f"API: Buscando áreas para sede {sede_id}, encontradas: {len(areas)}")  # Debug
                return JsonResponse({'areas': list(areas)})
            else:
                return JsonResponse({'error': 'ID de sede no especificado'}, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Datos JSON inválidos'}, status=400)
        except Exception as e:
            print(f"Error en API áreas por sede: {str(e)}")  # Debug
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required
@csrf_exempt
def api_personal_por_area(request):
    """API para obtener personal por área"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            area_id = data.get('area_id')
            
            if area_id:
                personal = Personal.objects.filter(area_id=area_id, activo=True).values('id', 'nombre', 'apellido')
                print(f"API: Buscando personal para área {area_id}, encontrados: {len(personal)}")  # Debug
                return JsonResponse({'personal': list(personal)})
            else:
                return JsonResponse({'error': 'ID de área no especificado'}, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Datos JSON inválidos'}, status=400)
        except Exception as e:
            print(f"Error en API personal por área: {str(e)}")  # Debug
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required
def detalle_movimiento(request, movimiento_id):
    """Ver detalles de un movimiento"""
    try:
        movimiento = get_object_or_404(Movimiento, id=movimiento_id)
        
        context = {
            'movimiento': movimiento,
        }
        
        return render(request, 'inventario/detalle_movimiento.html', context)
        
    except Movimiento.DoesNotExist:
        messages.error(request, 'Movimiento no encontrado.')
        return redirect('inventario:lista_movimientos')


@login_required
@user_passes_test(lambda u: u.is_staff)
def editar_movimiento(request, movimiento_id):
    """Editar movimiento"""
    try:
        movimiento = get_object_or_404(Movimiento, id=movimiento_id)
        
        if request.method == 'POST':
            # Obtener datos del formulario
            producto_id = request.POST.get('producto')
            tipo_movimiento_id = request.POST.get('tipo_movimiento')
            cantidad = request.POST.get('cantidad')
            motivo = request.POST.get('motivo')
            
            # Campos de origen
            sede_origen_id = request.POST.get('sede_origen')
            area_origen_id = request.POST.get('area_origen')
            personal_origen_id = request.POST.get('personal_origen')
            
            # Campos de destino
            sede_destino_id = request.POST.get('sede_destino')
            area_destino_id = request.POST.get('area_destino')
            personal_destino_id = request.POST.get('personal_destino')
            
            try:
                producto = Producto.objects.get(id=producto_id)
                tipo_movimiento = TipoMovimiento.objects.get(id=tipo_movimiento_id)
                
                # Obtener objetos relacionados
                sede_origen = None
                area_origen = None
                personal_origen = None
                sede_destino = None
                area_destino = None
                personal_destino = None
                
                if sede_origen_id:
                    sede_origen = Sede.objects.get(id=sede_origen_id)
                if area_origen_id:
                    area_origen = Area.objects.get(id=area_origen_id)
                if personal_origen_id:
                    personal_origen = Personal.objects.get(id=personal_origen_id)
                if sede_destino_id:
                    sede_destino = Sede.objects.get(id=sede_destino_id)
                if area_destino_id:
                    area_destino = Area.objects.get(id=area_destino_id)
                if personal_destino_id:
                    personal_destino = Personal.objects.get(id=personal_destino_id)
                
                # Actualizar el movimiento
                movimiento.producto = producto
                movimiento.tipo_movimiento = tipo_movimiento
                movimiento.cantidad = cantidad
                movimiento.motivo = motivo
                movimiento.sede_origen = sede_origen
                movimiento.area_origen = area_origen
                movimiento.personal_origen = personal_origen
                movimiento.sede_destino = sede_destino
                movimiento.area_destino = area_destino
                movimiento.personal_destino = personal_destino
                movimiento.save()
                
                messages.success(request, f'Movimiento #{movimiento.id} actualizado exitosamente.')
                return redirect('inventario:lista_movimientos')
                
            except (Producto.DoesNotExist, TipoMovimiento.DoesNotExist, Sede.DoesNotExist, 
                    Area.DoesNotExist, Personal.DoesNotExist) as e:
                messages.error(request, f'Error al actualizar movimiento: {str(e)}')
        
        # Obtener datos para el formulario
        productos = Producto.objects.filter(estado='activo').order_by('nombre')
        tipos_movimiento = TipoMovimiento.objects.filter(activo=True).order_by('nombre')
        sedes = Sede.objects.filter(activo=True).order_by('nombre')
        areas = Area.objects.filter(activo=True).order_by('nombre')
        personal = Personal.objects.filter(activo=True).order_by('nombre')
        
        context = {
            'movimiento': movimiento,
            'productos': productos,
            'tipos_movimiento': tipos_movimiento,
            'sedes': sedes,
            'areas': areas,
            'personal': personal,
        }
        
        return render(request, 'inventario/editar_movimiento.html', context)
        
    except Movimiento.DoesNotExist:
        messages.error(request, 'Movimiento no encontrado.')
        return redirect('inventario:lista_movimientos')


@login_required
@user_passes_test(lambda u: u.is_staff)
def eliminar_movimiento(request, movimiento_id):
    """Eliminar movimiento"""
    try:
        movimiento = get_object_or_404(Movimiento, id=movimiento_id)
        movimiento_id_str = str(movimiento.id)
        producto_nombre = movimiento.producto.nombre
        
        # Eliminar el movimiento
        movimiento.delete()
        messages.success(request, f'Movimiento #{movimiento_id_str} eliminado exitosamente.')
        
    except Movimiento.DoesNotExist:
        messages.error(request, 'Movimiento no encontrado.')
    except Exception as e:
        messages.error(request, f'Error al eliminar el movimiento: {str(e)}')
    
    return redirect('inventario:lista_movimientos')


# Nuevas vistas para gestión de licencias
@login_required
@user_passes_test(lambda u: u.is_staff)
def gestion_licencias(request):
    """Vista para gestionar licencias y su asignación"""
    # Obtener estadísticas de licencias
    total_licencias = Licencia.objects.count()
    licencias_activas = Licencia.objects.filter(activo=True).count()
    licencias_disponibles = Licencia.objects.filter(activo=True, licencias_disponibles__gt=0).count()
    licencias_asignadas = Licencia.objects.filter(activo=True, licencias_disponibles__lt=models.F('cantidad_licencias')).count()
    
    # Obtener productos con licencias asignadas
    productos_con_licencias = Producto.objects.filter(licencias__isnull=False).distinct()
    
    # Obtener licencias por tipo de distribución
    licencias_oem = Licencia.objects.filter(tipo_distribucion='oem', activo=True)
    licencias_retail = Licencia.objects.filter(tipo_distribucion='retail', activo=True)
    licencias_volume = Licencia.objects.filter(tipo_distribucion='volume', activo=True)
    
    context = {
        'total_licencias': total_licencias,
        'licencias_activas': licencias_activas,
        'licencias_disponibles': licencias_disponibles,
        'licencias_asignadas': licencias_asignadas,
        'productos_con_licencias': productos_con_licencias,
        'licencias_oem': licencias_oem,
        'licencias_retail': licencias_retail,
        'licencias_volume': licencias_volume,
    }
    
    return render(request, 'inventario/gestion_licencias.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def asignar_licencia_producto(request, producto_id):
    """Asignar licencia a un producto específico"""
    try:
        producto = Producto.objects.get(id=producto_id)
    except Producto.DoesNotExist:
        messages.error(request, 'Producto no encontrado.')
        return redirect('inventario:lista_productos')
    
    if request.method == 'POST':
        form = AsignarLicenciaForm(request.POST, producto=producto)
        if form.is_valid():
            licencia = form.cleaned_data['licencia']
            observaciones = form.cleaned_data['observaciones']
            
            # Verificar que hay licencias disponibles
            if licencia.licencias_disponibles > 0:
                # Crear la relación ProductoLicencia
                producto_licencia = ProductoLicencia.objects.create(
                    producto=producto,
                    licencia=licencia,
                    observaciones=observaciones
                )
                
                # Actualizar licencias disponibles
                licencia.licencias_disponibles -= 1
                licencia.save()
                
                messages.success(request, f'Licencia "{licencia.nombre}" asignada exitosamente al producto "{producto.nombre}".')
                return redirect('inventario:detalle_producto', producto_id=producto.id)
            else:
                messages.error(request, 'No hay licencias disponibles para asignar.')
    else:
        form = AsignarLicenciaForm(producto=producto)
    
    # Obtener licencias ya asignadas al producto
    licencias_asignadas = producto.licencias.all()
    
    context = {
        'producto': producto,
        'form': form,
        'licencias_asignadas': licencias_asignadas,
    }
    
    return render(request, 'inventario/asignar_licencia_producto.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def quitar_licencia_producto(request, producto_id, licencia_id):
    """Quitar licencia de un producto"""
    try:
        producto = Producto.objects.get(id=producto_id)
        licencia = Licencia.objects.get(id=licencia_id)
        producto_licencia = ProductoLicencia.objects.get(producto=producto, licencia=licencia)
        
        # Eliminar la asignación
        producto_licencia.delete()
        
        # Actualizar licencias disponibles
        licencia.licencias_disponibles += 1
        licencia.save()
        
        messages.success(request, f'Licencia "{licencia.nombre}" removida exitosamente del producto "{producto.nombre}".')
        
    except (Producto.DoesNotExist, Licencia.DoesNotExist, ProductoLicencia.DoesNotExist):
        messages.error(request, 'Error al quitar la licencia.')
    
    return redirect('inventario:detalle_producto', producto_id=producto_id)


@login_required
@user_passes_test(lambda u: u.is_staff)
def detalle_licencia(request, licencia_id):
    """Vista para mostrar detalles de una licencia"""
    licencia = get_object_or_404(Licencia, id=licencia_id)
    
    # Obtener productos que tienen esta licencia asignada
    productos_asignados = ProductoLicencia.objects.filter(licencia=licencia, activo=True)
    
    # Obtener productos para mostrar en la tabla
    productos = [asignacion.producto for asignacion in productos_asignados]
    
    # Obtener historial de asignaciones
    asignaciones = ProductoLicencia.objects.filter(licencia=licencia).order_by('-fecha_asignacion')
    
    context = {
        'licencia': licencia,
        'productos_asignados': productos,
        'asignaciones': asignaciones,
        'today': timezone.now().date(),
    }
    
    return render(request, 'inventario/detalle_licencia.html', context)


# ============================================================================
# VISTAS PARA GESTIÓN DE CUENTAS
# ============================================================================

@login_required
@user_passes_test(lambda u: u.is_staff)
def lista_cuentas(request):
    """Vista para listar todas las cuentas"""
    cuentas = Cuenta.objects.filter(activo=True).order_by('tipo_cuenta', 'nombre')
    
    # Filtros
    tipo_cuenta = request.GET.get('tipo_cuenta')
    estado = request.GET.get('estado')
    sede_id = request.GET.get('sede')
    
    if tipo_cuenta:
        cuentas = cuentas.filter(tipo_cuenta=tipo_cuenta)
    if estado:
        cuentas = cuentas.filter(estado=estado)
    if sede_id:
        cuentas = cuentas.filter(sede_id=sede_id)
    
    # Paginación
    paginator = Paginator(cuentas, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    total_cuentas = cuentas.count()
    cuentas_activas = cuentas.filter(estado='activa').count()
    cuentas_vencidas = cuentas.filter(estado='vencida').count()
    cuentas_proximo_vencimiento = cuentas.filter(
        fecha_vencimiento__lte=timezone.now().date() + timedelta(days=30),
        fecha_vencimiento__gte=timezone.now().date()
    ).count()
    
    context = {
        'page_obj': page_obj,
        'total_cuentas': total_cuentas,
        'cuentas_activas': cuentas_activas,
        'cuentas_vencidas': cuentas_vencidas,
        'cuentas_proximo_vencimiento': cuentas_proximo_vencimiento,
        'tipos_cuenta': Cuenta.TIPOS_CUENTA,
        'estados_cuenta': Cuenta.ESTADOS_CUENTA,
        'sedes': Sede.objects.filter(activo=True),
        'filtros': {
            'tipo_cuenta': tipo_cuenta,
            'estado': estado,
            'sede_id': sede_id,
        }
    }
    
    return render(request, 'inventario/lista_cuentas.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def crear_cuenta(request):
    """Vista para crear una nueva cuenta"""
    if request.method == 'POST':
        form = CuentaForm(request.POST)
        if form.is_valid():
            cuenta = form.save()
            messages.success(request, f'Cuenta "{cuenta.nombre}" creada exitosamente')
            return redirect('inventario:lista_cuentas')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario')
    else:
        form = CuentaForm()
    
    context = {
        'form': form,
        'titulo': 'Crear Nueva Cuenta',
        'tipos_cuenta': Cuenta.TIPOS_CUENTA,
    }
    
    return render(request, 'inventario/crear_cuenta.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def editar_cuenta(request, cuenta_id):
    """Vista para editar una cuenta existente"""
    cuenta = get_object_or_404(Cuenta, id=cuenta_id)
    
    if request.method == 'POST':
        form = CuentaForm(request.POST, instance=cuenta)
        if form.is_valid():
            cuenta = form.save()
            messages.success(request, f'Cuenta "{cuenta.nombre}" actualizada exitosamente')
            return redirect('inventario:lista_cuentas')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario')
    else:
        form = CuentaForm(instance=cuenta)
    
    context = {
        'form': form,
        'cuenta': cuenta,
        'titulo': f'Editar Cuenta: {cuenta.nombre}',
        'tipos_cuenta': Cuenta.TIPOS_CUENTA,
    }
    
    return render(request, 'inventario/editar_cuenta.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def detalle_cuenta(request, cuenta_id):
    """Vista para mostrar detalles de una cuenta"""
    cuenta = get_object_or_404(Cuenta, id=cuenta_id)
    
    # Calcular el valor absoluto de días de vencimiento para el template
    dias_absolutos = abs(cuenta.dias_vencimiento) if cuenta.dias_vencimiento is not None else None
    
    context = {
        'cuenta': cuenta,
        'dias_absolutos': dias_absolutos,
    }
    
    return render(request, 'inventario/detalle_cuenta.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def eliminar_cuenta(request, cuenta_id):
    """Vista para eliminar una cuenta"""
    cuenta = get_object_or_404(Cuenta, id=cuenta_id)
    
    if request.method == 'POST':
        nombre_cuenta = cuenta.nombre
        cuenta.activo = False
        cuenta.save()
        messages.success(request, f'Cuenta "{nombre_cuenta}" eliminada exitosamente')
        return redirect('inventario:lista_cuentas')
    
    context = {
        'cuenta': cuenta,
    }
    
    return render(request, 'inventario/eliminar_cuenta.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def gestion_cuentas(request):
    """Vista para gestión avanzada de cuentas"""
    # Estadísticas generales
    total_cuentas = Cuenta.objects.filter(activo=True).count()
    cuentas_activas = Cuenta.objects.filter(activo=True, estado='activa').count()
    cuentas_vencidas = Cuenta.objects.filter(activo=True, estado='vencida').count()
    
    # Cuentas por tipo
    cuentas_por_tipo = Cuenta.objects.filter(activo=True).values('tipo_cuenta').annotate(
        total=Count('id')
    ).order_by('tipo_cuenta')
    
    # Cuentas próximas a vencer (30 días)
    cuentas_proximo_vencimiento = Cuenta.objects.filter(
        activo=True,
        fecha_vencimiento__lte=timezone.now().date() + timedelta(days=30),
        fecha_vencimiento__gte=timezone.now().date()
    ).order_by('fecha_vencimiento')
    
    # Cuentas vencidas
    cuentas_vencidas_lista = Cuenta.objects.filter(
        activo=True,
        fecha_vencimiento__lt=timezone.now().date()
    ).order_by('fecha_vencimiento')
    
    # Calcular días absolutos para cada cuenta vencida
    for cuenta in cuentas_vencidas_lista:
        cuenta.dias_absolutos = abs(cuenta.dias_vencimiento) if cuenta.dias_vencimiento is not None else 0
    
    # Costo total mensual
    costo_total_mensual = Cuenta.objects.filter(
        activo=True, 
        costo_mensual__isnull=False
    ).aggregate(total=Sum('costo_mensual'))['total'] or 0
    
    context = {
        'total_cuentas': total_cuentas,
        'cuentas_activas': cuentas_activas,
        'cuentas_vencidas': cuentas_vencidas,
        'cuentas_por_tipo': cuentas_por_tipo,
        'cuentas_proximo_vencimiento': cuentas_proximo_vencimiento,
        'cuentas_vencidas_lista': cuentas_vencidas_lista,
        'costo_total_mensual': costo_total_mensual,
        'tipos_cuenta': Cuenta.TIPOS_CUENTA,
    }
    
    return render(request, 'inventario/gestion_cuentas.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
@csrf_exempt
def api_get_license_key(request, licencia_id):
    """API para obtener la clave de licencia desencriptada"""
    try:
        licencia = get_object_or_404(Licencia, id=licencia_id)
        clave = licencia.get_license_key()
        
        if clave:
            return JsonResponse({
                'success': True,
                'key': clave
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'No se pudo desencriptar la clave'
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@user_passes_test(lambda u: u.is_staff)
@csrf_exempt
def api_get_account_password(request, cuenta_id):
    """API para obtener la contraseña de cuenta desencriptada"""
    try:
        cuenta = get_object_or_404(Cuenta, id=cuenta_id)
        password = cuenta.get_password()
        
        if password:
            return JsonResponse({
                'success': True,
                'password': password
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'No se pudo desencriptar la contraseña'
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


# ============================================================================
# VISTAS PARA PLANIFICACIÓN SEMANAL
# ============================================================================

@login_required
def lista_planificacion_semanal(request):
    """Lista de planificación semanal"""
    tareas = PlanificacionSemanal.objects.filter(activo=True).select_related(
        'personal_asignado', 'sede', 'area'
    ).order_by('dia_semana', 'hora_inicio')
    
    # Filtros
    dia = request.GET.get('dia')
    estado = request.GET.get('estado')
    prioridad = request.GET.get('prioridad')
    personal_id = request.GET.get('personal')
    
    if dia:
        tareas = tareas.filter(dia_semana=dia)
    if estado:
        tareas = tareas.filter(estado=estado)
    if prioridad:
        tareas = tareas.filter(prioridad=prioridad)
    if personal_id:
        tareas = tareas.filter(personal_asignado_id=personal_id)
    
    # Agrupar por día
    tareas_por_dia = {}
    for tarea in tareas:
        dia = tarea.get_dia_semana_display()
        if dia not in tareas_por_dia:
            tareas_por_dia[dia] = []
        tareas_por_dia[dia].append(tarea)
    
    context = {
        'tareas_por_dia': tareas_por_dia,
        'dias_semana': PlanificacionSemanal.DIAS_SEMANA,
        'estados': PlanificacionSemanal.ESTADOS,
        'prioridades': PlanificacionSemanal.PRIORIDADES,
        'personal_list': Personal.objects.filter(activo=True),
        'filtros': {
            'dia': dia,
            'estado': estado,
            'prioridad': prioridad,
            'personal': personal_id,
        }
    }
    
    return render(request, 'inventario/lista_planificacion_semanal.html', context)


@login_required
def crear_planificacion_semanal(request):
    """Crear nueva tarea de planificación semanal"""
    if request.method == 'POST':
        form = PlanificacionSemanalForm(request.POST)
        if form.is_valid():
            tarea = form.save()
            messages.success(request, f'Tarea "{tarea.titulo}" creada exitosamente.')
            return redirect('inventario:lista_planificacion_semanal')
    else:
        form = PlanificacionSemanalForm()
    
    context = {
        'form': form,
        'titulo': 'Nueva Tarea Semanal'
    }
    
    return render(request, 'inventario/crear_planificacion_semanal.html', context)


@login_required
def editar_planificacion_semanal(request, tarea_id):
    """Editar tarea de planificación semanal"""
    tarea = get_object_or_404(PlanificacionSemanal, id=tarea_id)
    
    if request.method == 'POST':
        form = PlanificacionSemanalForm(request.POST, instance=tarea)
        if form.is_valid():
            form.save()
            messages.success(request, f'Tarea "{tarea.titulo}" actualizada exitosamente.')
            return redirect('inventario:lista_planificacion_semanal')
    else:
        form = PlanificacionSemanalForm(instance=tarea)
    
    context = {
        'form': form,
        'tarea': tarea,
        'titulo': f'Editar Tarea: {tarea.titulo}'
    }
    
    return render(request, 'inventario/editar_planificacion_semanal.html', context)


@login_required
def eliminar_planificacion_semanal(request, tarea_id):
    """Eliminar tarea de planificación semanal"""
    tarea = get_object_or_404(PlanificacionSemanal, id=tarea_id)
    
    if request.method == 'POST':
        tarea.activo = False
        tarea.save()
        messages.success(request, f'Tarea "{tarea.titulo}" eliminada exitosamente.')
        return redirect('inventario:lista_planificacion_semanal')
    
    context = {
        'tarea': tarea
    }
    
    return render(request, 'inventario/eliminar_planificacion_semanal.html', context)


@login_required
def cambiar_estado_tarea(request, tarea_id):
    """Cambiar estado de una tarea"""
    tarea = get_object_or_404(PlanificacionSemanal, id=tarea_id)
    nuevo_estado = request.POST.get('estado')
    
    if nuevo_estado in dict(PlanificacionSemanal.ESTADOS):
        tarea.estado = nuevo_estado
        if nuevo_estado == 'completada':
            tarea.fecha_completada = timezone.now()
        tarea.save()
        messages.success(request, f'Estado de la tarea "{tarea.titulo}" cambiado a {tarea.get_estado_display()}.')
    
    return redirect('inventario:lista_planificacion_semanal')


# ============================================================================
# VISTAS PARA CONEXIONES WINBOX
# ============================================================================

@login_required
def lista_conexiones_winbox(request):
    """Lista de conexiones Winbox"""
    conexiones = ConexionWinbox.objects.filter(activo=True).select_related(
        'sede', 'area', 'ultimo_usuario_conectado'
    ).order_by('sede', 'area', 'nombre')
    
    # Filtros
    tipo_equipo = request.GET.get('tipo_equipo')
    estado = request.GET.get('estado')
    sede_id = request.GET.get('sede')
    
    if tipo_equipo:
        conexiones = conexiones.filter(tipo_equipo=tipo_equipo)
    if estado:
        conexiones = conexiones.filter(estado=estado)
    if sede_id:
        conexiones = conexiones.filter(sede_id=sede_id)
    
    context = {
        'conexiones': conexiones,
        'tipos_equipo': ConexionWinbox.TIPOS_EQUIPO,
        'estados_conexion': ConexionWinbox.ESTADOS_CONEXION,
        'sedes': Sede.objects.filter(activo=True),
        'filtros': {
            'tipo_equipo': tipo_equipo,
            'estado': estado,
            'sede': sede_id,
        }
    }
    
    return render(request, 'inventario/lista_conexiones_winbox.html', context)


@login_required
def crear_conexion_winbox(request):
    """Crear nueva conexión Winbox"""
    if request.method == 'POST':
        form = ConexionWinboxForm(request.POST)
        if form.is_valid():
            conexion = form.save()
            messages.success(request, f'Conexión "{conexion.nombre}" creada exitosamente.')
            return redirect('inventario:lista_conexiones_winbox')
    else:
        form = ConexionWinboxForm()
    
    context = {
        'form': form,
        'titulo': 'Nueva Conexión Winbox'
    }
    
    return render(request, 'inventario/crear_conexion_winbox.html', context)


@login_required
def editar_conexion_winbox(request, conexion_id):
    """Editar conexión Winbox"""
    conexion = get_object_or_404(ConexionWinbox, id=conexion_id)
    
    if request.method == 'POST':
        form = ConexionWinboxForm(request.POST, instance=conexion)
        if form.is_valid():
            form.save()
            messages.success(request, f'Conexión "{conexion.nombre}" actualizada exitosamente.')
            return redirect('inventario:lista_conexiones_winbox')
    else:
        form = ConexionWinboxForm(instance=conexion)
    
    context = {
        'form': form,
        'conexion': conexion,
        'titulo': f'Editar Conexión: {conexion.nombre}'
    }
    
    return render(request, 'inventario/editar_conexion_winbox.html', context)


@login_required
def eliminar_conexion_winbox(request, conexion_id):
    """Eliminar conexión Winbox"""
    conexion = get_object_or_404(ConexionWinbox, id=conexion_id)
    
    if request.method == 'POST':
        conexion.activo = False
        conexion.save()
        messages.success(request, f'Conexión "{conexion.nombre}" eliminada exitosamente.')
        return redirect('inventario:lista_conexiones_winbox')
    
    context = {
        'conexion': conexion
    }
    
    return render(request, 'inventario/eliminar_conexion_winbox.html', context)


@login_required
def conectar_winbox(request, conexion_id):
    """Registrar conexión a Winbox"""
    conexion = get_object_or_404(ConexionWinbox, id=conexion_id)
    
    # Actualizar información de conexión
    conexion.ultima_conexion = timezone.now()
    conexion.ultimo_usuario_conectado = request.user
    conexion.save()
    
    messages.success(request, f'Conexión registrada a "{conexion.nombre}".')
    return redirect('inventario:lista_conexiones_winbox')


@login_required
@csrf_exempt
def api_get_winbox_password(request, conexion_id):
    """API para obtener contraseña de conexión Winbox"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'No tienes permisos para acceder a esta información'}, status=403)
    
    conexion = get_object_or_404(ConexionWinbox, id=conexion_id)
    password = conexion.get_password()
    
    return JsonResponse({
        'password': password,
        'conexion': conexion.nombre
    })


