# orders/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import ServiceOrder, Equipment, ServiceMaterial

class ServiceOrderForm(forms.ModelForm):
    class Meta:
        model = ServiceOrder
        fields = [
            "cliente_nombre", "cliente_email", "ubicacion", "fecha_servicio",
            "contacto_nombre", "tipo_servicio", "ingeniero_nombre",
            "titulo", "actividades", "comentarios",
            "equipo_marca", "equipo_modelo", "equipo_serie", "equipo_descripcion",
            "resguardo", "horas", "costo_mxn", "costo_no_aplica", "costo_se_cotizara",
            "reagenda", "reagenda_fecha", "reagenda_hora", "reagenda_motivo",
        ]
        widgets = {
            "fecha_servicio": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "reagenda_fecha": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "reagenda_hora": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
        }

EquipmentFormSet = inlineformset_factory(
    parent_model=ServiceOrder,
    model=Equipment,
    fields=["marca", "modelo", "serie", "descripcion"],
    widgets={
        "marca": forms.TextInput(attrs={"class": "form-control"}),
        "modelo": forms.TextInput(attrs={"class": "form-control"}),
        "serie": forms.TextInput(attrs={"class": "form-control"}),
        "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 1}),
    },
    extra=1,
    can_delete=True,
)

ServiceMaterialFormSet = inlineformset_factory(
    parent_model=ServiceOrder,
    model=ServiceMaterial,
    fields=["descripcion", "cantidad", "comentarios"],
    widgets={
        "descripcion": forms.TextInput(attrs={"class": "form-control"}),
        "cantidad": forms.NumberInput(attrs={"class": "form-control"}),
        "comentarios": forms.TextInput(attrs={"class": "form-control"}),
    },
    extra=1,
    can_delete=True,
)
