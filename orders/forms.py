from django import forms
from django.forms import inlineformset_factory
from django.contrib.auth.models import User
from .models import ServiceOrder, Equipment, ServiceMaterial, ShelterEquipment, ServiceEvidence, SERVICE_TYPES, EngineerProfile

# ================================================================
# FORMULARIO PRINCIPAL DE LA ORDEN
# ================================================================
class ServiceOrderForm(forms.ModelForm):
    tipos_servicio = forms.MultipleChoiceField(
        label="Tipo de servicio solicitado",
        required=False, # <--- RELAJADO PARA BORRADORES
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
            "fecha_servicio": forms.DateInput(attrs={"type": "date"}),
            "reagenda_fecha": forms.DateInput(attrs={"type": "date"}),
            "reagenda_hora": forms.TimeInput(attrs={"type": "time"}),
            "actividades": forms.Textarea(attrs={"rows": 3}),
            "comentarios": forms.Textarea(attrs={"rows": 3}),
            "indicaciones_especiales": forms.Textarea(attrs={"rows": 2}),
            "estatus": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Selector de Ingenieros
        ingenieros = User.objects.filter(is_staff=True).order_by('first_name')
        opciones = [(u.get_full_name() or u.username, u.get_full_name() or u.username) for u in ingenieros]
        self.fields['ingeniero_nombre'].widget = forms.Select(choices=[('', 'Seleccione...')] + opciones)

        # ETIQUETAS
        self.fields["cliente_nombre"].label = "Cliente / Empresa"
        self.fields["cliente_contacto"].label = "Persona de contacto"
        self.fields["ticket_id"].label = "ID Ticket"

        # --- MAGIA PARA BORRADORES: NADA ES OBLIGATORIO EXCEPTO EL CLIENTE ---
        for field in self.fields:
            self.fields[field].required = False
        
        self.fields['cliente_nombre'].required = True # Solo este es vital

        # Inicializar JSON
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

# 1. EQUIPOS (Relajado)
class EquipmentForm(forms.ModelForm):
    marca = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    modelo = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    serie = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    descripcion = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    class Meta: model = Equipment; fields = "__all__"

EquipmentFormSet = inlineformset_factory(
    ServiceOrder, Equipment, form=EquipmentForm, extra=0, can_delete=True
)

# 2. MATERIALES (Relajado)
class ServiceMaterialForm(forms.ModelForm):
    cantidad = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    descripcion = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    comentarios = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    class Meta: model = ServiceMaterial; fields = "__all__"

ServiceMaterialFormSet = inlineformset_factory(
    ServiceOrder, ServiceMaterial, form=ServiceMaterialForm, extra=0, can_delete=True
)

# 3. RESGUARDOS (Relajado)
class ShelterEquipmentForm(forms.ModelForm):
    cantidad = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    descripcion = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    comentarios = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    class Meta: model = ShelterEquipment; fields = "__all__"

ShelterEquipmentFormSet = inlineformset_factory(
    ServiceOrder, ShelterEquipment, form=ShelterEquipmentForm, extra=0, can_delete=True
)

# 4. EVIDENCIAS (Relajado)
class ServiceEvidenceForm(forms.ModelForm):
    archivo = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    comentario = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    class Meta: model = ServiceEvidence; fields = "__all__"

ServiceEvidenceFormSet = inlineformset_factory(
    ServiceOrder, ServiceEvidence, form=ServiceEvidenceForm, extra=0, can_delete=True
)


# ================================================================
# USUARIOS
# ================================================================
class CustomUserCreationForm(forms.ModelForm):
    first_name = forms.CharField(label="Nombre", required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label="Apellidos", required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label="Correo", required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=True)
    confirm_password = forms.CharField(label="Confirmar", widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=True)
    role = forms.ChoiceField(label="Rol", choices=[('visor','Visor'),('ingeniero','Ingeniero'),('superuser','Admin')], widget=forms.Select(attrs={'class': 'form-select'}))
    firma_b64 = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta: model = User; fields = ['username', 'first_name', 'last_name', 'email']; widgets = {'username': forms.TextInput(attrs={'class': 'form-control'})}

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password") != cleaned_data.get("confirm_password"):
            self.add_error('confirm_password', "Las contraseñas no coinciden.")
        return cleaned_data

class UserEditForm(CustomUserCreationForm):
    password = forms.CharField(label="Nueva Contraseña (Opcional)", widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=False)
    confirm_password = forms.CharField(label="Confirmar", widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=False)