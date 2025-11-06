# orders/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import Order, Equipo, Material  # Asegúrate de tener estos modelos

class OrderForm(forms.ModelForm):
  class Meta:
    model = Order
    fields = ["folio", "fecha", "cliente", "ingeniero", "titulo", "descripcion"]
    widgets = {
      "folio": forms.TextInput(attrs={"class": "form-control"}),
      "fecha": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
      "cliente": forms.TextInput(attrs={"class": "form-control"}),
      "ingeniero": forms.TextInput(attrs={"class": "form-control"}),
      "titulo": forms.TextInput(attrs={"class": "form-control"}),
      "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    }

EquipoFormSet = inlineformset_factory(
  parent_model=Order,
  model=Equipo,
  fields=["tipo", "marca", "modelo", "serie", "falla"],
  widgets={
    "tipo": forms.TextInput(attrs={"class": "form-control"}),
    "marca": forms.TextInput(attrs={"class": "form-control"}),
    "modelo": forms.TextInput(attrs={"class": "form-control"}),
    "serie": forms.TextInput(attrs={"class": "form-control"}),
    "falla": forms.Textarea(attrs={"class": "form-control", "rows": 1}),
  },
  extra=1,
  can_delete=True,
)

MaterialFormSet = inlineformset_factory(
  parent_model=Order,
  model=Material,
  fields=["descripcion", "cantidad", "unidad"],
  widgets={
    "descripcion": forms.TextInput(attrs={"class": "form-control"}),
    "cantidad": forms.NumberInput(attrs={"class": "form-control"}),
    "unidad": forms.TextInput(attrs={"class": "form-control"}),
  },
  extra=1,
  can_delete=True,
)
