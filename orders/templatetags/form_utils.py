from django import template

register = template.Library()

@register.filter(name='add_class_if_error')
def add_class_if_error(field, css_class='is-invalid'):
    """
    Agrega una clase CSS (por defecto 'is-invalid') al widget del campo
    si este tiene errores de validación.
    Uso en template: {{ form.campo|add_class_if_error }}
    """
    if hasattr(field, 'errors') and field.errors:
        # Obtenemos las clases actuales
        existing_classes = field.field.widget.attrs.get('class', '')
        # Si ya tiene la clase, no la repetimos
        if css_class not in existing_classes:
            new_classes = f"{existing_classes} {css_class}"
            return field.as_widget(attrs={"class": new_classes})
    return field