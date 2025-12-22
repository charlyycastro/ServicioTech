import base64
from django.core.files.base import ContentFile
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

# Si no tienes forms.py aún, el paso 2 lo arreglará.
from .forms import CustomUserCreationForm, CustomUserChangeForm
# Importamos el perfil desde ORDERS (que es donde ya existe)
from orders.models import EngineerProfile

# --- Decorador: Solo Admins ---
def superuser_required(user):
    return user.is_superuser

@method_decorator(user_passes_test(superuser_required), name='dispatch')
class UserListView(ListView):
    model = User
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    ordering = ['-date_joined']

@method_decorator(user_passes_test(superuser_required), name='dispatch')
class UserCreateView(CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('users:user_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = "Crear Nuevo Usuario"
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object
        
        # --- LÓGICA DE FIRMA ---
        firma_b64 = form.cleaned_data.get('firma_b64')
        # Intentamos obtener el rol del form, si no, lo deducimos
        rol = form.cleaned_data.get('role', 'visor') 

        if firma_b64:
            try:
                format, imgstr = firma_b64.split(';base64,') 
                ext = format.split('/')[-1] 
                data = ContentFile(base64.b64decode(imgstr), name=f'firma_{user.username}.{ext}')
                
                # Guardar en orders.EngineerProfile
                perfil, created = EngineerProfile.objects.get_or_create(user=user)
                perfil.firma.save(f'firma_{user.username}.{ext}', data, save=True)
            except Exception as e:
                messages.warning(self.request, f"Usuario creado, pero error en firma: {e}")

        messages.success(self.request, f"Usuario {user.username} creado correctamente.")
        return response

@method_decorator(user_passes_test(superuser_required), name='dispatch')
class UserUpdateView(UpdateView):
    # --- ESTO ES LO QUE TE FALTABA ---
    model = User  # <--- ¡INDISPENSABLE!
    form_class = CustomUserChangeForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('users:user_list')
    # ---------------------------------

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = f"Editar Usuario: {self.object.username}"
        
        # Prellenar el select de "Rol" según los permisos actuales
        if self.object.is_superuser:
            ctx['form'].fields['role'].initial = 'admin'
        elif self.object.is_staff:
            ctx['form'].fields['role'].initial = 'ingeniero'
        else:
            ctx['form'].fields['role'].initial = 'visor'
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object
        
        # 1. Actualizar Rol
        rol = form.cleaned_data.get('role')
        if rol == 'admin':
            user.is_staff = True; user.is_superuser = True
        elif rol == 'ingeniero':
            user.is_staff = True; user.is_superuser = False
        else:
            user.is_staff = False; user.is_superuser = False
        
        # 2. Actualizar Contraseña (si se escribió algo nuevo)
        new_pass = form.cleaned_data.get('password')
        if new_pass:
            user.set_password(new_pass)
        
        user.save()

        # 3. Actualizar Firma
        firma_b64 = form.cleaned_data.get('firma_b64')
        if firma_b64:
            try:
                format, imgstr = firma_b64.split(';base64,') 
                ext = format.split('/')[-1] 
                data = ContentFile(base64.b64decode(imgstr), name=f'firma_{user.username}.{ext}')
                
                perfil, created = EngineerProfile.objects.get_or_create(user=user)
                perfil.firma.save(f'firma_{user.username}.{ext}', data, save=True)
            except Exception as e:
                messages.warning(self.request, f"Error actualizando firma: {e}")

        messages.success(self.request, "Usuario actualizado correctamente.")
        return response

@method_decorator(user_passes_test(superuser_required), name='dispatch')
class UserDeleteView(DeleteView):
    model = User
    template_name = 'users/user_confirm_delete.html'
    success_url = reverse_lazy('users:user_list')