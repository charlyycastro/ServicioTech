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
            "fecha_servicio": forms.DateInput(attrs={"type": "date"}),
            "reagenda_fecha": forms.DateInput(attrs={"type": "date"}),
            "reagenda_hora": forms.TimeInput(attrs={"type": "time"}),
            "tipo_servicio": forms.Select(),
            "actividades": forms.Textarea(attrs={"rows": 3}),
            "comentarios": forms.Textarea(attrs={"rows": 3}),
            "equipo_descripcion": forms.Textarea(attrs={"rows": 2}),
            "reagenda_motivo": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            w = field.widget
            # Asignar clases Bootstrap según tipo de widget
            if isinstance(w, (forms.CheckboxInput,)):
                w.attrs["class"] = (w.attrs.get("class", "") + " form-check-input").strip()
            elif isinstance(w, (forms.Select, forms.SelectMultiple)):
                w.attrs["class"] = (w.attrs.get("class", "") + " form-select").strip()
            else:
                w.attrs["class"] = (w.attrs.get("class", "") + " form-control").strip()
        # Placeholders útiles (opcional)
        self.fields["cliente_nombre"].widget.attrs["placeholder"] = "Nombre del cliente"
        self.fields["ubicacion"].widget.attrs["placeholder"] = "Dirección o sitio"
        self.fields["contacto_nombre"].widget.attrs["placeholder"] = "Persona de contacto"
        self.fields["ingeniero_nombre"].widget.attrs["placeholder"] = "Nombre del ingeniero"
        self.fields["titulo"].widget.attrs["placeholder"] = "Título breve del servicio"

EquipmentFormSet = inlineformset_factory(
    parent_model=ServiceOrder,
    model=Equipment,
    fields=["marca", "modelo", "serie", "descripcion"],
    widgets={
        "marca": forms.TextInput(),
        "modelo": forms.TextInput(),
        "serie": forms.TextInput(),
        "descripcion": forms.Textarea(attrs={"rows": 1}),
    },
    extra=1,
    can_delete=True,
)

ServiceMaterialFormSet = inlineformset_factory(
    parent_model=ServiceOrder,
    model=ServiceMaterial,
    fields=["descripcion", "cantidad", "comentarios"],
    widgets={
        "descripcion": forms.TextInput(),
        "cantidad": forms.NumberInput(),
        "comentarios": forms.TextInput(),
    },
    extra=1,
    can_delete=True,
)
