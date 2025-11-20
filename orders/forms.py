from django import forms
from django.forms import inlineformset_factory

from .models import ServiceOrder, Equipment, ServiceMaterial, SERVICE_TYPES


class ServiceOrderForm(forms.ModelForm):
    # mostramos tipos_servicio como checkboxes
    tipos_servicio = forms.MultipleChoiceField(
        label="Tipo de servicio solicitado",
        required=False,
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
            "contacto_nombre",       # ahora “Contacto interno”
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
            "indicaciones_especiales",  # campo interno
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

        # Etiquetas como las pediste
        self.fields["cliente_nombre"].label = "Cliente"
        self.fields["cliente_contacto"].label = "Nombre del cliente"
        self.fields["cliente_email"].label = "Correo del cliente"
        self.fields["cliente_telefono"].label = "Número de teléfono del cliente"
        self.fields["contacto_nombre"].label = "Contacto interno"
        self.fields["ticket_id"].label = "ID Ticket" # <--- ETIQUETA

        # Inicializar tipos_servicio desde el JSONField
        if self.instance and self.instance.pk and self.instance.tipos_servicio:
            self.initial.setdefault("tipos_servicio", self.instance.tipos_servicio)

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Guardar lista seleccionada en el JSONField
        instance.tipos_servicio = self.cleaned_data.get("tipos_servicio", [])
        if commit:
            instance.save()
        return instance


# ========== Inline formsets para equipos y materiales ==========

EquipmentFormSet = inlineformset_factory(
    ServiceOrder,
    Equipment,
    fields=["marca", "modelo", "serie", "descripcion"],
    extra=1,
    can_delete=True,
)

ServiceMaterialFormSet = inlineformset_factory(
    ServiceOrder,
    ServiceMaterial,
    fields=["cantidad", "descripcion", "comentarios"],
    extra=1,
    can_delete=True,
)
