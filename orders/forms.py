from django import forms
from django.forms import inlineformset_factory
from django.contrib.auth.models import User
from .models import ServiceOrder, Equipment, ServiceMaterial, ShelterEquipment, ServiceEvidence, SERVICE_TYPES, EngineerProfile

# ================================================================
# FORMULARIO PRINCIPAL DE LA ORDEN
# ================================================================
class ServiceOrderForm(forms.ModelForm):
    # 1. Selector de INGENIEROS (Staff = True)
    ingeniero_nombre = forms.ModelChoiceField(
        queryset=User.objects.filter(is_staff=True, is_active=True).order_by('first_name'),
        to_field_name='username', # Guarda el username en la BD
        label="Ingeniero Asignado",
        empty_label="Seleccione un Ingeniero...",
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )

    # 2. Selector de VISORES (Staff = False) -> Para "Contacto Interno"
    contacto_nombre = forms.ModelChoiceField(
        queryset=User.objects.filter(is_staff=False, is_superuser=False, is_active=True).order_by('first_name'),
        to_field_name='username', # Guarda el username en la BD
        label="Contacto Interno (Visor)",
        empty_label="Seleccione un Visor...",
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )

    tipos_servicio = forms.MultipleChoiceField(
        label="Tipo de servicio solicitado",
        required=False,
        widget=forms.CheckboxSelectMultiple,
        choices=SERVICE_TYPES,
    )

    class Meta:
        model = ServiceOrder
        fields = [
            "cliente_nombre", "cliente_contacto", "cliente_email", "cliente_telefono",
            "ubicacion", "fecha_servicio", "contacto_nombre", "tipos_servicio",
            "tipo_servicio_otro", "ingeniero_nombre", "ticket_id", "titulo",
            "actividades", "comentarios", "horas", "costo_mxn", "costo_no_aplica",
            "costo_se_cotizara", "reagenda", "reagenda_fecha", "reagenda_hora",
            "reagenda_motivo", "indicaciones_especiales", "firma", "estatus",
        ]
        widgets = {
            "fecha_servicio": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "reagenda_fecha": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "reagenda_hora": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "actividades": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "comentarios": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "indicaciones_especiales": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "estatus": forms.HiddenInput(),
            
            # Estilos Bootstrap genéricos para el resto
            "cliente_nombre": forms.TextInput(attrs={"class": "form-control"}),
            "cliente_contacto": forms.TextInput(attrs={"class": "form-control"}),
            "cliente_email": forms.EmailInput(attrs={"class": "form-control"}),
            "cliente_telefono": forms.TextInput(attrs={"class": "form-control"}),
            "ubicacion": forms.TextInput(attrs={"class": "form-control"}),
            "ticket_id": forms.TextInput(attrs={"class": "form-control"}),
            "titulo": forms.TextInput(attrs={"class": "form-control"}),
            "tipo_servicio_otro": forms.TextInput(attrs={"class": "form-control"}),
            "horas": forms.TextInput(attrs={"class": "form-control"}),
            "costo_mxn": forms.NumberInput(attrs={"class": "form-control"}),
            "reagenda_motivo": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ETIQUETAS PERSONALIZADAS
        self.fields["cliente_nombre"].label = "Cliente / Empresa"
        self.fields["cliente_contacto"].label = "Persona de contacto"
        self.fields["ticket_id"].label = "ID Ticket"

        # Relajamiento de campos para Borradores (todo opcional al inicio)
        for field in self.fields:
            self.fields[field].required = False
        
        # Solo el nombre del cliente es obligatorio siempre para no perder la referencia
        self.fields['cliente_nombre'].required = True

        # Inicializar JSON de Tipos de Servicio
        if self.instance and self.instance.pk and self.instance.tipos_servicio:
            self.initial.setdefault("tipos_servicio", self.instance.tipos_servicio)

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.tipos_servicio = self.cleaned_data.get("tipos_servicio", [])
        if commit:
            instance.save()
        return instance


# ================================================================
# FORMULARIOS DE TABLAS (RELAJADOS)
# ================================================================

# Definiciones de Forms base para Tablas
class EquipmentForm(forms.ModelForm):
    marca = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    modelo = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    serie = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    descripcion = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    class Meta: model = Equipment; fields = "__all__"

class ServiceMaterialForm(forms.ModelForm):
    cantidad = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    descripcion = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    comentarios = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    class Meta: model = ServiceMaterial; fields = "__all__"

class ShelterEquipmentForm(forms.ModelForm):
    cantidad = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    descripcion = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    comentarios = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    class Meta: model = ShelterEquipment; fields = "__all__"

class ServiceEvidenceForm(forms.ModelForm):
    archivo = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    comentario = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    class Meta: model = ServiceEvidence; fields = "__all__"

# Definiciones de FormSets
EquipmentFormSet = inlineformset_factory(ServiceOrder, Equipment, form=EquipmentForm, extra=0, can_delete=True)
ServiceMaterialFormSet = inlineformset_factory(ServiceOrder, ServiceMaterial, form=ServiceMaterialForm, extra=0, can_delete=True)
ShelterEquipmentFormSet = inlineformset_factory(ServiceOrder, ShelterEquipment, form=ShelterEquipmentForm, extra=0, can_delete=True)
ServiceEvidenceFormSet = inlineformset_factory(ServiceOrder, ServiceEvidence, form=ServiceEvidenceForm, extra=0, can_delete=True)

# ================================================================
# GESTIÓN DE USUARIOS (CREAR / EDITAR)
# ================================================================

class CustomUserCreationForm(forms.ModelForm):
    first_name = forms.CharField(label="Nombre(s)", required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label="Apellidos", required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label="Correo electrónico", required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=True)
    confirm_password = forms.CharField(label="Confirmar contraseña", widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=True)
    role = forms.ChoiceField(label="Rol / Permisos", choices=[('visor', 'Visor'), ('ingeniero', 'Ingeniero'), ('superuser', 'Administrador')], widget=forms.Select(attrs={'class': 'form-select'}))
    firma_b64 = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {'username': forms.TextInput(attrs={'class': 'form-control'})}

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Las contraseñas no coinciden.")
        return cleaned_data

class UserEditForm(CustomUserCreationForm):
    password = forms.CharField(label="Nueva Contraseña (Opcional)", widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=False)
    confirm_password = forms.CharField(label="Confirmar Nueva (Opcional)", widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=False)

    def clean(self):
        # Esta es la validación para edición (donde la contraseña es opcional)
        cleaned_data = super(forms.ModelForm, self).clean() 
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        # Se exige que la confirmación coincida SIEMPRE que se haya escrito ALGO en password o confirm_password
        if password or confirm_password:
            if password != confirm_password:
                self.add_error('confirm_password', "Las nuevas contraseñas no coinciden.")
                
        return cleaned_data