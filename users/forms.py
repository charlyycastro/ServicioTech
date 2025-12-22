from django import forms
from django.contrib.auth.models import User

# --- FORMULARIO DE CREACIÓN (NUEVO USUARIO) ---
class CustomUserCreationForm(forms.ModelForm):
    first_name = forms.CharField(
        label="Nombre(s)", 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Juan Carlos'})
    )
    last_name = forms.CharField(
        label="Apellidos", 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Pérez López'})
    )
    email = forms.EmailField(
        label="Correo Electrónico", 
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@inovatech.com.mx'})
    )
    password = forms.CharField(
        label="Contraseña", 
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Ingresa una contraseña segura'})
    )
    confirm_password = forms.CharField(
        label="Confirmar Contraseña", 
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repite la contraseña'})
    )
    
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('ingeniero', 'Ingeniero de Soporte'),
        ('visor', 'Visor / Ventas'),
    ]
    role = forms.ChoiceField(
        label="Rol del Usuario", 
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}) # 'form-select' es para listas desplegables bonitas
    )

    # Campo oculto para la firma
    firma_b64 = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'usuario.sistema'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("confirm_password")
        if p1 and p2 and p1 != p2:
            self.add_error('confirm_password', "Las contraseñas no coinciden.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        # Asignar permisos básicos
        rol = self.cleaned_data['role']
        if rol == 'admin':
            user.is_staff = True; user.is_superuser = True
        elif rol == 'ingeniero':
            user.is_staff = True; user.is_superuser = False
        else:
            user.is_staff = False; user.is_superuser = False
            
        if commit:
            user.save()
        return user


# --- FORMULARIO DE EDICIÓN (MODIFICAR USUARIO) ---
class CustomUserChangeForm(forms.ModelForm):
    first_name = forms.CharField(
        label="Nombre(s)", 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label="Apellidos", 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label="Correo Electrónico", 
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    # Campos opcionales de contraseña con estilo
    password = forms.CharField(
        label="Nueva Contraseña", 
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Dejar vacío para mantener la actual'})
    )
    confirm_password = forms.CharField(
        label="Confirmar Nueva Contraseña", 
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repetir para confirmar'})
    )

    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('ingeniero', 'Ingeniero de Soporte'),
        ('visor', 'Visor / Ventas'),
    ]
    role = forms.ChoiceField(
        label="Rol", 
        choices=ROLE_CHOICES, 
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    firma_b64 = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}), # Readonly para que no cambien el login fácilmente
        }

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("confirm_password")
        
        if p1 or p2:
            if p1 != p2:
                self.add_error('confirm_password', "Las contraseñas no coinciden.")
        return cleaned_data