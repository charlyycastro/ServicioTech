from django import forms
from django.forms import inlineformset_factory
from django.contrib.auth.models import User
from .models import ServiceOrder, Equipment, ServiceMaterial, ShelterEquipment, ServiceEvidence, SERVICE_TYPES, EngineerProfile

# ================================================================
# FORMULARIO PRINCIPAL DE LA ORDEN
# ================================================================
class ServiceOrderForm(forms.ModelForm):
    # Checkboxes para tipos de servicio
    tipos_servicio = forms.MultipleChoiceField(
        label="Tipo de servicio solicitado",
        required=True,
        widget=forms.CheckboxSelectMultiple,
        choices=SERVICE_TYPES,
    )

    class Meta:
        model = ServiceOrder
        fields = [
            "cliente_nombre",
            "cliente_contacto",
            "cliente_email",
            "cliente_telefono",
            "ubicacion",
            "fecha_servicio",
            "contacto_nombre",
            "tipos_servicio",
            "tipo_servicio_otro",
            "ingeniero_nombre", # Ahora será un Select
            "ticket_id",
            "titulo",
            "actividades",
            "comentarios",
            "horas",
            "costo_mxn",
            "costo_no_aplica",
            "costo_se_cotizara",
            "reagenda",
            "reagenda_fecha",
            "reagenda_hora",
            "reagenda_motivo",
            "indicaciones_especiales",
            "firma",
            "estatus", # Nuevo campo
        ]
        widgets = {
            "fecha_servicio": forms.DateInput(attrs={"type": "date"}),
            "reagenda_fecha": forms.DateInput(attrs={"type": "date"}),
            "reagenda_hora": forms.TimeInput(attrs={"type": "time"}),
            "actividades": forms.Textarea(attrs={"rows": 3}),
            "comentarios": forms.Textarea(attrs={"rows": 3}),
            "indicaciones_especiales": forms.Textarea(attrs={"rows": 2}),
            # El estatus lo manejaremos con botones, así que lo ocultamos aquí
            "estatus": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # --- 1. CONVERTIR INGENIERO A DROPDOWN (SELECT) ---
        ingenieros = User.objects.filter(is_staff=True).order_by('first_name')
        opciones_ingenieros = []
        for ing in ingenieros:
            nombre_completo = ing.get_full_name() or ing.username
            opciones_ingenieros.append((nombre_completo, nombre_completo))
        
        self.fields['ingeniero_nombre'].widget = forms.Select(choices=[('', 'Seleccione un Ingeniero...')] + opciones_ingenieros)

        # --- 2. ETIQUETAS ---
        self.fields["cliente_nombre"].label = "Cliente / Empresa"
        self.fields["cliente_contacto"].label = "Persona de contacto"
        self.fields["ticket_id"].label = "ID Ticket"

        # --- 3. RELAJAR VALIDACIÓN (Permitir Borradores) ---
        # Hacemos que NADA sea obligatorio en el formulario HTML/Django por defecto.
        # Validaremos manualmente en la vista si el usuario quiere "Finalizar".
        for field in self.fields:
            self.fields[field].required = False
        
        # Solo obligamos el Nombre del Cliente para que la orden exista
        if 'cliente_nombre' in self.fields:
            self.fields['cliente_nombre'].required = True

        # Inicializar JSON
        if self.instance and self.instance.pk and self.instance.tipos_servicio:
            self.initial.setdefault("tipos_servicio", self.instance.tipos_servicio)


# ================================================================
# INLINE FORMSETS (TABLAS DINÁMICAS)
# ================================================================

# --- A) Formulario Relajado para EQUIPOS (Evita errores si hay filas vacías) ---
class EquipmentForm(forms.ModelForm):
    marca = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    modelo = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    serie = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    descripcion = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Equipment
        fields = ["marca", "modelo", "serie", "descripcion"]

# 1. Equipos del Cliente (Sección B)
EquipmentFormSet = inlineformset_factory(
    ServiceOrder, Equipment, 
    form=EquipmentForm, # <--- Usamos el form relajado
    extra=0, can_delete=True
)

# 2. Materiales (Sección E)
ServiceMaterialFormSet = inlineformset_factory(
    ServiceOrder, ServiceMaterial, fields=["cantidad", "descripcion", "comentarios"],
    extra=0, can_delete=True
)

# --- B) Formulario Relajado para RESGUARDOS ---
class ShelterEquipmentForm(forms.ModelForm):
    descripcion = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    cantidad = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    comentarios = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = ShelterEquipment
        fields = ["cantidad", "descripcion", "comentarios"]

# 3. Equipos en Resguardo (Interno)
ShelterEquipmentFormSet = inlineformset_factory(
    ServiceOrder, ShelterEquipment, 
    form=ShelterEquipmentForm, 
    extra=0, can_delete=True
)

# 4. Evidencias
ServiceEvidenceFormSet = inlineformset_factory(
    ServiceOrder, ServiceEvidence,
    fields=["archivo", "comentario"],
    extra=0, can_delete=True
)


# ================================================================
# GESTIÓN DE USUARIOS (CREAR / EDITAR)
# ================================================================

# --- FORMULARIO PARA CREAR (Alta) ---
class CustomUserCreationForm(forms.ModelForm):
    first_name = forms.CharField(label="Nombre(s)", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Juan Carlos'}))
    last_name = forms.CharField(label="Apellidos", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Pérez López'}))
    email = forms.EmailField(label="Correo electrónico", widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@empresa.com'}))
    
    password = forms.CharField(
        label="Contraseña", 
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True
    )
    confirm_password = forms.CharField(
        label="Confirmar contraseña", 
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True
    )

    ROLE_CHOICES = [
        ('visor', 'Visor (Solo ve reportes)'),
        ('ingeniero', 'Ingeniero (Crea reportes, tiene firma)'),
        ('superuser', 'Superusuario (Administrador total)'),
    ]
    role = forms.ChoiceField(
        label="Rol / Permisos", 
        choices=ROLE_CHOICES, 
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    # Campo oculto para recibir la firma dibujada (Base64)
    firma_b64 = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Usuario para login'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Las contraseñas no coinciden.")
        return cleaned_data

# --- FORMULARIO PARA EDITAR (Modificación) ---
class UserEditForm(CustomUserCreationForm):
    # En edición, la contraseña es opcional
    password = forms.CharField(label="Nueva Contraseña (Opcional)", widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=False)
    confirm_password = forms.CharField(label="Confirmar Nueva (Opcional)", widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=False)

    def clean(self):
        cleaned_data = super(forms.ModelForm, self).clean() # Saltamos la validación del padre
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Las contraseñas no coinciden.")
        return cleaned_data