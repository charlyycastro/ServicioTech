from django import forms
from django.forms import inlineformset_factory
from .models import ServiceOrder, ServiceMaterial


class ServiceOrderForm(forms.ModelForm):
class Meta:
model = ServiceOrder
fields = [
'cliente_nombre','cliente_email','ubicacion','fecha_servicio','contacto_nombre',
'tipo_servicio','ingeniero_nombre','equipo_marca','equipo_modelo','equipo_serie',
'equipo_descripcion','titulo','actividades','comentarios','resguardo','horas',
'costo_mxn','costo_no_aplica','costo_se_cotizara','reagenda','reagenda_fecha',
'reagenda_hora','reagenda_motivo','firma'
]
widgets = {
'fecha_servicio': forms.DateInput(attrs={'type':'date'}),
'reagenda_fecha': forms.DateInput(attrs={'type':'date'}),
'reagenda_hora': forms.TimeInput(attrs={'type':'time'}),
'comentarios': forms.Textarea(attrs={'rows':3}),
'actividades': forms.Textarea(attrs={'rows':4}),
'equipo_descripcion': forms.Textarea(attrs={'rows':3}),
}


MaterialFormSet = inlineformset_factory(
ServiceOrder, ServiceMaterial,
fields=['cantidad','descripcion','comentarios'], extra=1, can_delete=True
)