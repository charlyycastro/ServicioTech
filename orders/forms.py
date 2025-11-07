from django import forms
from django.forms import inlineformset_factory
from .models import ServiceOrder, Equipment, ServiceMaterial, SERVICE_TYPES

TIPOS_CHOICES = SERVICE_TYPES + [("otro", "Otro (especifique)")]

class ServiceOrderForm(forms.ModelForm):
    # ✅ Checkboxes múltiples
    tipos_servicio = forms.MultipleChoiceField(
        choices=TIPOS_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Tipo(s) de servicio",
    )
    # ✅ Texto para "otro"
    tipo_servicio_otro = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Especifique otro tipo…"})
    )

    class Meta:
        model = ServiceOrder
        fields = [
            "cliente_nombre", "cliente_email", "ubicacion", "fecha_servicio",
            "contacto_nombre", "tipos_servicio", "tipo_servicio_otro", "ingeniero_nombre",
            "titulo", "actividades", "comentarios",
            "equipo_marca", "equipo_modelo", "equipo_serie", "equipo_descripcion",
            # "resguardo"  # ❌ no lo mostramos
            "horas", "costo_mxn", "costo_no_aplica", "costo_se_cotizara",
            "reagenda", "reagenda_fecha", "reagenda_hora", "reagenda_motivo",
        ]
        widgets = {
            "fecha_servicio": forms.DateInput(attrs={"type": "date"}),
            "reagenda_fecha": forms.DateInput(attrs={"type": "date"}),
            "reagenda_hora": forms.TimeInput(attrs={"type": "time"}),
            "actividades": forms.Textarea(attrs={"rows": 3}),
            "comentarios": forms.Textarea(attrs={"rows": 3}),
            "equipo_descripcion": forms.Textarea(attrs={"rows": 2}),
            "reagenda_motivo": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Inicializa checkboxes con lo guardado
        if self.instance and self.instance.pk:
            self.fields["tipos_servicio"].initial = self.instance.tipos_servicio or []

        # Bootstrap classes
        for _, field in self.fields.items():
            w = field.widget
            if isinstance(w, forms.CheckboxInput):
                w.attrs["class"] = (w.attrs.get("class", "") + " form-check-input").strip()
            elif isinstance(w, forms.CheckboxSelectMultiple):
                # se estiliza en plantilla/CSS
                pass
            elif isinstance(w, (forms.Select, forms.SelectMultiple)):
                w.attrs["class"] = (w.attrs.get("class", "") + " form-select").strip()
            else:
                w.attrs["class"] = (w.attrs.get("class", "") + " form-control").strip()

        # Placeholders rápidos
        self.fields["cliente_nombre"].widget.attrs["placeholder"] = "Nombre del cliente"
        self.fields["ubicacion"].widget.attrs["placeholder"] = "Dirección o sitio"
        self.fields["contacto_nombre"].widget.attrs["placeholder"] = "Persona de contacto"
        self.fields["ingeniero_nombre"].widget.attrs["placeholder"] = "Nombre del ingeniero"
        self.fields["titulo"].widget.attrs["placeholder"] = "Título breve del servicio"

    def clean(self):
        data = super().clean()
        seleccionados = data.get("tipos_servicio") or []
        otro = (data.get("tipo_servicio_otro") or "").strip()
        if "otro" in seleccionados and not otro:
            self.add_error("tipo_servicio_otro", "Especifique el tipo de servicio.")
        return data

    def save(self, commit=True):
        inst: ServiceOrder = super().save(commit=False)
        seleccionados = self.cleaned_data.get("tipos_servicio") or []
        inst.tipos_servicio = [v for v in seleccionados if v != "otro"]
        inst.tipo_servicio_otro = (self.cleaned_data.get("tipo_servicio_otro") or "").strip()
        # compat: guarda el primero en el campo antiguo (por si algo lo usa)
        inst.tipo_servicio = inst.tipos_servicio[0] if inst.tipos_servicio else ""
        if commit:
            inst.save()
        return inst


EquipmentFormSet = inlineformset_factory(
    parent_model=ServiceOrder,
    model=Equipment,
    fields=["marca", "modelo", "serie", "descripcion"],
    widgets={"descripcion": forms.Textarea(attrs={"rows": 1})},
    extra=1,
    can_delete=True,
)

ServiceMaterialFormSet = inlineformset_factory(
    parent_model=ServiceOrder,
    model=ServiceMaterial,
    fields=["descripcion", "cantidad", "comentarios"],
    widgets={"descripcion": forms.TextInput(), "cantidad": forms.NumberInput()},
    extra=1,
    can_delete=True,
)
