from django.shortcuts import render, redirect, get_object_or_404
# Importamos decoradores de seguridad adicionales
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import logout
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db.models import Q
from django.conf import settings
from django.core.paginator import Paginator
from django.contrib.auth.models import User


#Usuarios ----
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from .models import EngineerProfile
from .forms import CustomUserCreationForm
import base64
import uuid
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from .forms import CustomUserCreationForm, UserEditForm

# --- LIBRERÍAS PARA PDF Y CORREO MANUAL (SMTP) ---
import weasyprint
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# --- MODELOS Y FORMULARIOS ---
from .models import ServiceOrder
from .forms import ServiceOrderForm, EquipmentFormSet, ServiceMaterialFormSet

# --- UTILIDADES ---
import base64, uuid
from django.core.files.base import ContentFile
from django.utils.dateparse import parse_date

# ================================================================
# FUNCIONES AUXILIARES DE SEGURIDAD
# ================================================================
def es_ingeniero_o_admin(user):
    """Verifica si el usuario es Staff (Ingeniero) o Superusuario"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)

def es_superusuario(user):
    """Verifica si el usuario es Superusuario (Admin total)"""
    return user.is_authenticated and user.is_superuser

def obtener_firma_ingeniero(nombre_ingeniero, request):
    """Busca el perfil del ingeniero por nombre completo y retorna la URL absoluta de su firma."""
    if not nombre_ingeniero:
        return None
        
    # Buscamos quién tiene ese nombre completo
    for user in User.objects.all():
        if user.get_full_name() == nombre_ingeniero:
            # Verificamos si tiene perfil y firma
            if hasattr(user, 'profile') and user.profile.firma:
                return request.build_absolute_uri(user.profile.firma.url)
    return None

# ================================================================
# VISTAS
# ================================================================

@login_required
def order_list(request):
    query = request.GET.get('q', '').strip()
    orders = ServiceOrder.objects.all().order_by('-creado')

    if query:
        orders = orders.filter(
            Q(folio__icontains=query) |
            Q(cliente_empresa__icontains=query) |
            Q(cliente_nombre__icontains=query) |
            Q(titulo__icontains=query)
        )

    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    ctx = {'page_obj': page_obj, 'query': query}
    return render(request, 'orders/order_list.html', ctx)

@login_required
def order_detail(request, pk):
    order = get_object_or_404(ServiceOrder, pk=pk)
    
    # AQUI ES DONDE LLAMAMOS A LA FUNCIÓN
    firma_url = obtener_firma_ingeniero(order.ingeniero_nombre, request)

    # Y AQUÍ LA PASAMOS AL TEMPLATE
    return render(request, 'orders/order_detail.html', {
        'object': order,
        'firma_ingeniero_url': firma_url  # <--- Esto es lo que faltaba
    })


# ===== CREAR (Restringido a Ingenieros y Admin) =====
@login_required
@user_passes_test(es_ingeniero_o_admin) # <--- CANDADO DE SEGURIDAD
def order_create(request):
    if request.method == "POST":
        form = ServiceOrderForm(request.POST, request.FILES)
        equipos_fs = EquipmentFormSet(request.POST, request.FILES, prefix="equipos")
        materiales_fs = ServiceMaterialFormSet(request.POST, request.FILES, prefix="materiales")

        if form.is_valid() and equipos_fs.is_valid() and materiales_fs.is_valid():
            order = form.save(commit=False)

            # --- A) ASIGNACIÓN AUTOMÁTICA DE INGENIERO ---
            # Usa el nombre completo si existe, si no, el nombre de usuario
            nombre_completo = request.user.get_full_name()
            if nombre_completo:
                order.ingeniero_nombre = nombre_completo
            else:
                order.ingeniero_nombre = request.user.username

            # --- B) PROCESAR FIRMA ---
            firma_b64 = (request.POST.get("firma_b64") or "").strip()
            if firma_b64.startswith("data:image"):
                try:
                    header, data = firma_b64.split(",", 1)
                    ext = "png"
                    if "jpeg" in header.lower() or "jpg" in header.lower():
                        ext = "jpg"
                    file_data = ContentFile(base64.b64decode(data), name=f"firma_{uuid.uuid4().hex}.{ext}")
                    order.firma = file_data
                except Exception:
                    messages.warning(request, "No pude procesar la firma. Se guardará sin firma.")

            order.save()

            # --- C) GUARDAR RELACIONES ---
            equipos_fs.instance = order
            materiales_fs.instance = order
            equipos_fs.save()
            materiales_fs.save()

            # ========================================================
            #   ENVÍO MANUAL SMTP (BYPASS TOTAL DE SEGURIDAD DJANGO)
            # ========================================================
            if order.cliente_email:
                try:
                    # 1. Generar PDF
                    html_string = render_to_string('orders/order_detail.html', {
                        'object': order,
                        'print_mode': True
                    }, request=request)

                    pdf_bytes = weasyprint.HTML(
                        string=html_string,
                        base_url=request.build_absolute_uri()
                    ).write_pdf()

                    # 2. Configurar Servidor SMTP Manualmente
                    smtp_server = settings.EMAIL_HOST
                    smtp_port = settings.EMAIL_PORT
                    smtp_user = settings.EMAIL_HOST_USER
                    smtp_password = settings.EMAIL_HOST_PASSWORD

                    # Crear mensaje
                    msg = MIMEMultipart()
                    msg['From'] = settings.DEFAULT_FROM_EMAIL
                    msg['To'] = order.cliente_email
                    msg['Subject'] = f"Reporte de Servicio {order.folio} - ServicioTech"

                    body = f"""
                    Hola {order.cliente_contacto or 'Cliente'},

                    Adjunto encontrarás el reporte de servicio técnico realizado el {order.fecha_servicio}.

                    Folio: {order.folio}
                    Título: {order.titulo}

                    Gracias por tu preferencia.
                    Atentamente,
                    El equipo de ServicioTech.
                    """
                    msg.attach(MIMEText(body, 'plain'))

                    # Adjuntar PDF
                    attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
                    attachment.add_header('Content-Disposition', 'attachment', filename=f"{order.folio}.pdf")
                    msg.attach(attachment)

                    # 3. CONEXIÓN SEGURA MANUAL
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE

                    server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
                    server.starttls(context=context)
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)
                    server.quit()

                    # 4. Éxito
                    order.email_enviado = True
                    order.save(update_fields=['email_enviado'])
                    messages.success(request, f"Orden enviada correctamente a {order.cliente_email}")

                except Exception as e:
                    print(f"❌ ERROR SMTP MANUAL: {e}")
                    messages.warning(request, f"Orden guardada. Error de correo: {e}")
            else:
                messages.success(request, "Orden guardada (Cliente sin correo).")

            return redirect(reverse("orders:detail", args=[order.pk]))
        else:
            messages.error(request, "Revisa los errores del formulario.")
    else:
        # --- D) PRE-LLENADO VISUAL (GET) ---
        # Pre-llenamos el formulario para que el usuario vea su nombre
        initial_data = {
            'ingeniero_nombre': request.user.get_full_name() or request.user.username
        }
        form = ServiceOrderForm(initial=initial_data)
        equipos_fs = EquipmentFormSet(prefix="equipos")
        materiales_fs = ServiceMaterialFormSet(prefix="materiales")

    ctx = {"form": form, "equipos_fs": equipos_fs, "materiales_fs": materiales_fs}
    return render(request, "orders/order_form.html", ctx)


# ===== ELIMINAR (Restringido solo a Superusuario) =====
@require_POST
@login_required
@user_passes_test(es_superusuario) # <--- CANDADO TOTAL
def bulk_delete(request):
    ids = request.POST.getlist("ids") or request.POST.getlist("selected")
    if not ids:
        messages.warning(request, "No seleccionaste ninguna orden.")
        return redirect("orders:list")

    # Filtramos por los IDs recibidos y borramos
    qs = ServiceOrder.objects.filter(id__in=ids)
    count = qs.count()
    qs.delete()

    messages.success(request, f"Se eliminaron {count} órdenes correctamente.")
    return redirect("orders:list")

# ===== LOGIN / LOGOUT =====
def login_view(request):
    # ... (tu código de login actual) ...
    # Si usas el login por defecto de Django, no necesitas esta función aquí.
    # Si tienes una vista personalizada, pégala aquí.
    pass

@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "Has cerrado sesión.")
    return redirect("login")

# ===== RE-ENVIAR CORREO (Botón manual desde el detalle) =====
@login_required
@user_passes_test(es_ingeniero_o_admin)
def email_order(request, pk):
    order = get_object_or_404(ServiceOrder, pk=pk)

    if not order.cliente_email:
        messages.warning(request, "Esta orden no tiene un correo de cliente registrado.")
        return redirect('orders:detail', pk=pk)

    try:
        # 1. Generar PDF
        html_string = render_to_string('orders/order_detail.html', {
            'object': order,
            'print_mode': True
        }, request=request)

        pdf_bytes = weasyprint.HTML(
            string=html_string,
            base_url=request.build_absolute_uri()
        ).write_pdf()

        # 2. Configurar Servidor SMTP Manualmente
        smtp_server = settings.EMAIL_HOST
        smtp_port = settings.EMAIL_PORT
        smtp_user = settings.EMAIL_HOST_USER
        smtp_password = settings.EMAIL_HOST_PASSWORD

        # Crear mensaje
        msg = MIMEMultipart()
        msg['From'] = settings.DEFAULT_FROM_EMAIL
        msg['To'] = order.cliente_email
        msg['Subject'] = f"Reporte de Servicio {order.folio} - ServicioTech (Reenvío)"

        body = f"""
        Hola {order.cliente_contacto or 'Cliente'},

        Adjunto encontrarás el reporte de servicio técnico realizado el {order.fecha_servicio}.

        Folio: {order.folio}
        Título: {order.titulo}

        Gracias por tu preferencia.
        Atentamente,
        El equipo de ServicioTech.
        """
        msg.attach(MIMEText(body, 'plain'))

        # Adjuntar PDF
        attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
        attachment.add_header('Content-Disposition', 'attachment', filename=f"{order.folio}.pdf")
        msg.attach(attachment)

        # 3. CONEXIÓN SEGURA MANUAL
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
        server.starttls(context=context)
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()

        # 4. Éxito
        order.email_enviado = True
        order.save(update_fields=['email_enviado'])
        messages.success(request, f"Correo reenviado exitosamente a {order.cliente_email}")

    except Exception as e:
        print(f"❌ ERROR SMTP MANUAL: {e}")
        messages.error(request, f"Error al enviar correo: {e}")

    return redirect('orders:detail', pk=pk)

@login_required
@user_passes_test(es_superusuario)
def user_list_view(request):
    """Muestra la lista de todos los usuarios para administrar."""
    users = User.objects.all().order_by('username')
    return render(request, 'orders/user_list.html', {'users': users})

@login_required
@user_passes_test(es_superusuario)
def create_user_view(request):
    """Crea un usuario nuevo con firma digital."""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.password = make_password(form.cleaned_data['password'])
            
            # Asignar Rol
            role = form.cleaned_data['role']
            user.is_staff = (role in ['ingeniero', 'superuser'])
            user.is_superuser = (role == 'superuser')
            user.save()

            # Procesar Firma Digital (Base64)
            firma_b64 = form.cleaned_data.get('firma_b64')
            if firma_b64 and role == 'ingeniero':
                guardar_firma(user, firma_b64)

            messages.success(request, f"Usuario {user.username} creado correctamente.")
            return redirect('orders:user_list')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'orders/user_form.html', {'form': form, 'titulo': 'Alta de Nuevo Usuario'})

@login_required
@user_passes_test(es_superusuario)
def edit_user_view(request, pk):
    """Edita un usuario existente."""
    user_to_edit = get_object_or_404(User, pk=pk)
    
    # Determinar rol actual
    rol_inicial = 'visor'
    if user_to_edit.is_superuser: rol_inicial = 'superuser'
    elif user_to_edit.is_staff: rol_inicial = 'ingeniero'

    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user_to_edit)
        if form.is_valid():
            user = form.save(commit=False)
            # Solo cambiar password si escribieron algo
            if form.cleaned_data['password']:
                user.password = make_password(form.cleaned_data['password'])
            
            # Actualizar Rol
            role = form.cleaned_data['role']
            user.is_staff = (role in ['ingeniero', 'superuser'])
            user.is_superuser = (role == 'superuser')
            user.save()

            # Actualizar Firma
            firma_b64 = form.cleaned_data.get('firma_b64')
            if firma_b64 and role == 'ingeniero':
                guardar_firma(user, firma_b64)

            messages.success(request, f"Usuario {user.username} actualizado.")
            return redirect('orders:user_list')
    else:
        form = UserEditForm(instance=user_to_edit, initial={'role': rol_inicial})

    return render(request, 'orders/user_form.html', {'form': form, 'titulo': f'Editar a {user_to_edit.username}'})

@login_required
@user_passes_test(es_superusuario)
def delete_user_view(request, pk):
    user_to_delete = get_object_or_404(User, pk=pk)
    if user_to_delete == request.user:
        messages.error(request, "No puedes eliminar tu propio usuario.")
    else:
        user_to_delete.delete()
        messages.success(request, "Usuario eliminado permanentemente.")
    return redirect('orders:user_list')

# --- AUXILIAR PARA GUARDAR FIRMA ---
def guardar_firma(user, data_url):
    """Decodifica el string base64 del canvas y lo guarda como imagen."""
    try:
        format, imgstr = data_url.split(';base64,') 
        ext = format.split('/')[-1] 
        data = ContentFile(base64.b64decode(imgstr), name=f'firma_{user.username}_{uuid.uuid4()}.{ext}')
        
        profile, created = EngineerProfile.objects.get_or_create(user=user)
        profile.firma = data
        profile.save()
    except Exception as e:
        print(f"Error guardando firma: {e}")