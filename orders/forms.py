# orders/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import ServiceOrder, ServiceMaterial


class ServiceOrderForm(forms.ModelForm):
    fecha_servicio = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"})
    )
    reagenda_fecha = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"})
    )
    reagenda_hora = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={"type": "time"})
    )
    # opcional: permitir subir firma como archivo además del canvas
    firma = forms.ImageField(required=False)

    class Meta:
        model = ServiceOrder
        fields = [
            "cliente_nombre", "cliente_email", "ubicacion", "fecha_servicio",
            "contacto_nombre", "tipo_servicio", "ingeniero_nombre",
            "equipo_marca", "equipo_modelo", "equipo_serie", "equipo_descripcion",
            "titulo", "actividades", "comentarios", "resguardo",
            "horas", "costo_mxn", "costo_no_aplica", "costo_se_cotizara",
            "reagenda", "reagenda_fecha", "reagenda_hora", "reagenda_motivo",
            "firma",
        ]
        widgets = {
            "actividades": forms.Textarea(attrs={"rows": 4}),
            "comentarios": forms.Textarea(attrs={"rows": 3}),
            "equipo_descripcion": forms.Textarea(attrs={"rows": 3}),
            "reagenda_motivo": forms.Textarea(attrs={"rows": 2}),
        }


class MaterialForm(forms.ModelForm):
    class Meta:
        model = ServiceMaterial
        fields = ["cantidad", "descripcion", "comentarios"]
        widgets = {
            "descripcion": forms.TextInput(attrs={"placeholder": "Descripción"}),
            "comentarios": forms.TextInput(attrs={"placeholder": "Comentarios opcionales"}),
        }


class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = ["marca", "modelo", "serie", "descripcion"]
        widgets = {
            "marca": forms.TextInput(attrs={"class": "form-control", "placeholder": "Marca"}),
            "modelo": forms.TextInput(attrs={"class": "form-control", "placeholder": "Modelo"}),
            "serie": forms.TextInput(attrs={"class": "form-control", "placeholder": "Serie"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Descripción"}),
        }

EquipmentFormSet = inlineformset_factory(
    ServiceOrder, Equipment,
    form=EquipmentForm,
    extra=1, can_delete=True
)
MaterialFormSet = inlineformset_factory(
    ServiceOrder,
    ServiceMaterial,
    form=MaterialForm,
    extra=1,
    can_delete=True,
)
