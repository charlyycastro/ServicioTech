from django import forms
from django.forms import inlineformset_factory
from .models import ServiceOrder, Equipment, ServiceMaterial, SERVICE_TYPES

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
            "ingeniero_nombre",
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
        ]
        widgets = {
            "fecha_servicio": forms.DateInput(attrs={"type": "date"}),
            "reagenda_fecha": forms.DateInput(attrs={"type": "date"}),
            "reagenda_hora": forms.TimeInput(attrs={"type": "time"}),
            "actividades": forms.Textarea(attrs={"rows": 3}),
            "comentarios": forms.Textarea(attrs={"rows": 3}),
            "indicaciones_especiales": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # --- 1. ETIQUETAS ---
        self.fields["cliente_nombre"].label = "Cliente"
        self.fields["cliente_contacto"].label = "Nombre del cliente"
        self.fields["cliente_email"].label = "Correo del cliente"
        self.fields["cliente_telefono"].label = "Número de teléfono del cliente"
        self.fields["contacto_nombre"].label = "Contacto interno"
        self.fields["ticket_id"].label = "ID Ticket"

        # --- 2. CAMPOS OBLIGATORIOS (SECCIÓN A) ---
        campos_obligatorios_a = [
            'cliente_nombre',
            'cliente_contacto',
            'cliente_email',
            'cliente_telefono',
            'ubicacion',
            'fecha_servicio',
            'contacto_nombre',
            'ingeniero_nombre',
            'ticket_id',
            'tipos_servicio'
        ]

        for field in campos_obligatorios_a:
            if field in self.fields:
                self.fields[field].required = True

        # --- 3. CAMPOS OPCIONALES ---
        if 'indicaciones_especiales' in self.fields:
            self.fields['indicaciones_especiales'].required = False
        
        if 'tipo_servicio_otro' in self.fields:
            self.fields['tipo_servicio_otro'].required = False
        if 'reagenda_motivo' in self.fields:
            self.fields['reagenda_motivo'].required = False
        if 'firma' in self.fields:
            self.fields['firma'].required = False

        # --- 4. INICIALIZAR JSON ---
        if self.instance and self.instance.pk and self.instance.tipos_servicio:
            self.initial.setdefault("tipos_servicio", self.instance.tipos_servicio)

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.tipos_servicio = self.cleaned_data.get("tipos_servicio", [])
        if commit:
            instance.save()
        return instance


# ========== Inline formsets ==========

# TABLA DE EQUIPOS (Opcional, puede ir vacía)
EquipmentFormSet = inlineformset_factory(
    ServiceOrder,
    Equipment,
    fields=["marca", "modelo", "serie", "descripcion"],
    extra=0,
    can_delete=True,
)

# TABLA DE MATERIALES (CORREGIDO: Opcional y limpia al inicio)
ServiceMaterialFormSet = inlineformset_factory(
    ServiceOrder,
    ServiceMaterial,
    fields=["cantidad", "descripcion", "comentarios"],
    extra=0,             # <--- IMPORTANTE: 0 filas vacías al inicio.
    can_delete=True,     # Permite borrar si te equivocas.
    # Quitamos min_num y validate_min para que NO sea obligatorio.
)