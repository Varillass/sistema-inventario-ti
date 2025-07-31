from django import forms
from .models import Categoria, Sede, Area, Personal, Licencia, Producto, Cuenta

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la categoría'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción de la categoría'
            })
        }


class SedeForm(forms.ModelForm):
    class Meta:
        model = Sede
        fields = ['nombre', 'direccion', 'telefono']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la sede'
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Dirección de la sede'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono de la sede'
            })
        }


class AreaForm(forms.ModelForm):
    class Meta:
        model = Area
        fields = ['nombre', 'sede', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del área'
            }),
            'sede': forms.Select(attrs={
                'class': 'form-select'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del área'
            })
        }


class PersonalForm(forms.ModelForm):
    class Meta:
        model = Personal
        fields = ['nombre', 'apellido', 'email', 'telefono', 'area', 'cargo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre'
            }),
            'apellido': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellido'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@empresa.com'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono'
            }),
            'area': forms.Select(attrs={
                'class': 'form-select'
            }),
            'cargo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cargo'
            })
        }


class LicenciaForm(forms.ModelForm):
    clave_licencia_plana = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese la clave de licencia',
            'type': 'password'
        }),
        help_text="La clave será encriptada automáticamente"
    )
    
    class Meta:
        model = Licencia
        fields = ['nombre', 'tipo', 'tipo_distribucion', 'proveedor', 'fecha_adquisicion', 'fecha_vencimiento', 'precio', 'cantidad_licencias', 'licencias_disponibles', 'observaciones']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la licencia'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tipo_distribucion': forms.Select(attrs={
                'class': 'form-select'
            }),
            'proveedor': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Proveedor'
            }),
            'fecha_adquisicion': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'fecha_vencimiento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'precio': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'cantidad_licencias': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': '1'
            }),
            'licencias_disponibles': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '1'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones'
            })
        }
    
    def save(self, commit=True):
        licencia = super().save(commit=False)
        
        # Encriptar la clave de licencia si se proporcionó
        if self.cleaned_data.get('clave_licencia_plana'):
            licencia.set_license_key(self.cleaned_data['clave_licencia_plana'])
        
        if commit:
            licencia.save()
        return licencia


class AsignarLicenciaForm(forms.Form):
    """Formulario para asignar licencias a productos"""
    licencia = forms.ModelChoiceField(
        queryset=Licencia.objects.filter(activo=True, licencias_disponibles__gt=0),
        empty_label="Seleccione una licencia",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        })
    )
    observaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Observaciones sobre la asignación'
        })
    )
    
    def __init__(self, *args, **kwargs):
        producto = kwargs.pop('producto', None)
        super().__init__(*args, **kwargs)
        
        if producto:
            # Excluir licencias que ya están asignadas al producto
            from .models import ProductoLicencia
            licencias_asignadas = ProductoLicencia.objects.filter(producto=producto).values_list('licencia_id', flat=True)
            self.fields['licencia'].queryset = Licencia.objects.filter(
                activo=True, 
                licencias_disponibles__gt=0
            ).exclude(id__in=licencias_asignadas)


class CuentaForm(forms.ModelForm):
    """Formulario para gestionar cuentas con contraseñas encriptadas"""
    password_plana = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese la contraseña',
            'type': 'password'
        }),
        help_text="La contraseña será encriptada automáticamente"
    )
    
    class Meta:
        model = Cuenta
        fields = [
            'nombre', 'tipo_cuenta', 'email', 'usuario', 'url_acceso',
            'fecha_creacion_cuenta', 'fecha_vencimiento', 'estado',
            'personal_asignado', 'sede', 'area', 'plan_suscripcion',
            'costo_mensual', 'proveedor', 'observaciones'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre descriptivo de la cuenta'
            }),
            'tipo_cuenta': forms.Select(attrs={
                'class': 'form-select'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@empresa.com'
            }),
            'usuario': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de usuario'
            }),
            'url_acceso': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://ejemplo.com'
            }),
            'fecha_creacion_cuenta': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'fecha_vencimiento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'estado': forms.Select(attrs={
                'class': 'form-select'
            }),
            'personal_asignado': forms.Select(attrs={
                'class': 'form-select'
            }),
            'sede': forms.Select(attrs={
                'class': 'form-select'
            }),
            'area': forms.Select(attrs={
                'class': 'form-select'
            }),
            'plan_suscripcion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Plan o tipo de suscripción'
            }),
            'costo_mensual': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'proveedor': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Proveedor del servicio'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones adicionales'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer que el campo area dependa de la sede seleccionada
        if 'instance' in kwargs and kwargs['instance']:
            if kwargs['instance'].sede:
                self.fields['area'].queryset = Area.objects.filter(sede=kwargs['instance'].sede)
            else:
                self.fields['area'].queryset = Area.objects.none()
        else:
            self.fields['area'].queryset = Area.objects.none()
    
    def save(self, commit=True):
        cuenta = super().save(commit=False)
        
        # Encriptar la contraseña si se proporcionó
        if self.cleaned_data.get('password_plana'):
            cuenta.set_password(self.cleaned_data['password_plana'])
        
        if commit:
            cuenta.save()
        return cuenta 