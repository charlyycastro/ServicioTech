from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache # <--- IMPORTANTE: Faltaba esto
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import logout
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db.models import Q
from django.conf import settings
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.core.files.base import ContentFile
from django.utils.dateparse import parse_date

# --- LIBRERÍAS EXTERNAS ---
import weasyprint
import smtplib
import ssl
import base64
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# --- MODELOS Y FORMULARIOS ---
from .models import ServiceOrder, EngineerProfile
from .forms import (
    ServiceOrderForm, EquipmentFormSet, ServiceMaterialFormSet,
    ShelterEquipmentFormSet, ServiceEvidenceFormSet, 
    CustomUserCreationForm, UserEditForm
)

# ================================================================
# FUNCIONES AUXILIARES DE SEGURIDAD Y UTILIDADES
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
        full_name = user.get_full_name()
        # Comparación flexible (nombre completo o username si no tiene nombre)
        if full_name == nombre_ingeniero or user.username == nombre_ingeniero:
            if hasattr(user, 'profile') and user.profile.firma:
                return request.build_absolute_uri(user.profile.firma.url)
    return None

def guardar_firma(user, data_url):
    """Decodifica el string base64 del canvas y lo guarda como imagen en el perfil."""
    try:
        if ';base64,' in data_url:
            format, imgstr = data_url.split(';base64,') 
            ext = format.split('/')[-1] 
            data = ContentFile(base64.b64decode(imgstr), name=f'firma_{user.username}_{uuid.uuid4()}.{ext}')
            
            profile, created = EngineerProfile.objects.get_or_create(user=user)
            profile.firma = data
            profile.save()
    except Exception as e:
        print(f"Error guardando firma de usuario: {e}")

# ================================================================
# VISTAS DE ÓRDENES (CRUD)
# ================================================================

@login_required
def order_list(request):
    query = request.GET.get('q', '').strip()
    # Ordenar por fecha de creación descendente
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
    
    # Obtener firma del ingeniero asignado
    firma_url = obtener_firma_ingeniero(order.ingeniero_nombre, request)

    return render(request, 'orders/order_detail.html', {
        'object': order,
        'firma_ingeniero_url': firma_url
    })

# ===== CREAR ORDEN (Con Resguardos, Evidencias y Pausa) =====
@login_required
@user_passes_test(es_ingeniero_o_admin)
def order_create(request):
    if request.method == "POST":
        form = ServiceOrderForm(request.POST, request.FILES)
        
        # Inicializamos los 4 FormSets
        equipos_fs = EquipmentFormSet(request.POST, request.FILES, prefix="equipos")
        materiales_fs = ServiceMaterialFormSet(request.POST, request.FILES, prefix="materiales")
        resguardos_fs = ShelterEquipmentFormSet(request.POST, request.FILES, prefix="resguardos")
        evidencias_fs = ServiceEvidenceFormSet(request.POST, request.FILES, prefix="evidencias")

        if form.is_valid() and equipos_fs.is_valid() and materiales_fs.is_valid() and resguardos_fs.is_valid() and evidencias_fs.is_valid():
            order = form.save(commit=False)
            accion = request.POST.get('accion', 'borrador')

            # === VALIDACIÓN MANUAL PARA FINALIZAR ===
            if accion == 'finalizar':
                errores = []
                # Validamos solo campos críticos
                if not order.cliente_contacto: errores.append("Persona de contacto")
                if not order.cliente_email: errores.append("Correo del cliente")
                if not order.ingeniero_nombre: errores.append("Ingeniero asignado")
                if not order.tipos_servicio: errores.append("Tipo de servicio")
                
                if errores:
                    messages.error(request, f"Para finalizar, faltan: {', '.join(errores)}")
                    ctx = {
                        "form": form, "equipos_fs": equipos_fs, "materiales_fs": materiales_fs,
                        "resguardos_fs": resguardos_fs, "evidencias_fs": evidencias_fs,
                        "titulo": "Nueva Orden de Servicio"
                    }
                    return render(request, "orders/order_form.html", ctx)

                order.estatus = 'finalizado'
                mensaje_exito = f"Orden {order.folio} FINALIZADA correctamente."
            else:
                order.estatus = 'borrador'
                mensaje_exito = f"Borrador guardado. Puedes continuar después."

            # Procesar firma del cliente (Base64)
            firma_b64 = (request.POST.get("firma_b64") or "").strip()
            if firma_b64.startswith("data:image"):
                try:
                    header, data = firma_b64.split(",", 1)
                    ext = "png"
                    if "jpeg" in header.lower(): ext = "jpg"
                    file_data = ContentFile(base64.b64decode(data), name=f"firma_cliente_{uuid.uuid4().hex}.{ext}")
                    order.firma = file_data
                except Exception as e:
                    print(f"Error firma cliente: {e}")

            order.save()

            # Guardar todas las tablas relacionadas
            equipos_fs.instance = order
            equipos_fs.save()
            materiales_fs.instance = order
            materiales_fs.save()
            resguardos_fs.instance = order
            resguardos_fs.save()
            evidencias_fs.instance = order
            evidencias_fs.save()

            messages.success(request, mensaje_exito)
            return redirect("orders:detail", pk=order.pk)
        else:
            messages.error(request, "Hay errores en el formulario.")
    else:
        # Pre-llenado inicial
        initial_data = {}
        if request.user.is_staff:
             initial_data['ingeniero_nombre'] = request.user.get_full_name() or request.user.username

        form = ServiceOrderForm(initial=initial_data)
        equipos_fs = EquipmentFormSet(prefix="equipos")
        materiales_fs = ServiceMaterialFormSet(prefix="materiales")
        resguardos_fs = ShelterEquipmentFormSet(prefix="resguardos")
        evidencias_fs = ServiceEvidenceFormSet(prefix="evidencias")

    ctx = {
        "form": form,
        "equipos_fs": equipos_fs,
        "materiales_fs": materiales_fs,
        "resguardos_fs": resguardos_fs,
        "evidencias_fs": evidencias_fs,
        "titulo": "Nueva Orden de Servicio"
    }
    return render(request, "orders/order_form.html", ctx)


# ===== EDITAR ORDEN (Retomar Borrador) =====
@login_required
@user_passes_test(es_ingeniero_o_admin)
def order_update(request, pk):
    order = get_object_or_404(ServiceOrder, pk=pk)

    if request.method == "POST":
        form = ServiceOrderForm(request.POST, request.FILES, instance=order)
        
        equipos_fs = EquipmentFormSet(request.POST, request.FILES, instance=order, prefix="equipos")
        materiales_fs = ServiceMaterialFormSet(request.POST, request.FILES, instance=order, prefix="materiales")
        resguardos_fs = ShelterEquipmentFormSet(request.POST, request.FILES, instance=order, prefix="resguardos")
        evidencias_fs = ServiceEvidenceFormSet(request.POST, request.FILES, instance=order, prefix="evidencias")

        if form.is_valid() and equipos_fs.is_valid() and materiales_fs.is_valid() and resguardos_fs.is_valid() and evidencias_fs.is_valid():
            order = form.save(commit=False)
            accion = request.POST.get('accion', 'borrador')

            # === VALIDACIÓN MANUAL PARA FINALIZAR ===
            if accion == 'finalizar':
                errores = []
                if not order.cliente_contacto: errores.append("Persona de contacto")
                if not order.cliente_email: errores.append("Correo del cliente")
                if not order.ingeniero_nombre: errores.append("Ingeniero asignado")
                if not order.tipos_servicio: errores.append("Tipo de servicio")
                
                if errores:
                    messages.error(request, f"Para finalizar, faltan: {', '.join(errores)}")
                    ctx = {
                        "form": form, "equipos_fs": equipos_fs, "materiales_fs": materiales_fs,
                        "resguardos_fs": resguardos_fs, "evidencias_fs": evidencias_fs,
                        "titulo": f"Editar Orden {order.folio}"
                    }
                    return render(request, "orders/order_form.html", ctx)

                order.estatus = 'finalizado'
                mensaje = f"Orden {order.folio} FINALIZADA y actualizada."
            else:
                order.estatus = 'borrador'
                mensaje = f"Cambios guardados en el BORRADOR {order.folio}."

            # Firma (si se actualizó)
            firma_b64 = (request.POST.get("firma_b64") or "").strip()
            if firma_b64.startswith("data:image"):
                try:
                    import base64
                    from django.core.files.base import ContentFile
                    import uuid
                    header, data = firma_b64.split(",", 1)
                    ext = "png" if "png" in header.lower() else "jpg"
                    file_data = ContentFile(base64.b64decode(data), name=f"firma_cliente_{uuid.uuid4().hex}.{ext}")
                    order.firma = file_data
                except Exception:
                    pass

            order.save()
            equipos_fs.save()
            materiales_fs.save()
            resguardos_fs.save()
            evidencias_fs.save()

            messages.success(request, mensaje)
            return redirect("orders:detail", pk=order.pk)
        else:
            messages.error(request, "Hay errores en el formulario.")
    else:
        form = ServiceOrderForm(instance=order)
        equipos_fs = EquipmentFormSet(instance=order, prefix="equipos")
        materiales_fs = ServiceMaterialFormSet(instance=order, prefix="materiales")
        resguardos_fs = ShelterEquipmentFormSet(instance=order, prefix="resguardos")
        evidencias_fs = ServiceEvidenceFormSet(instance=order, prefix="evidencias")

    ctx = {
        "form": form,
        "equipos_fs": equipos_fs,
        "materiales_fs": materiales_fs,
        "resguardos_fs": resguardos_fs,
        "evidencias_fs": evidencias_fs,
        "titulo": f"Editar Orden {order.folio}"
    }
    return render(request, "orders/order_form.html", ctx)


# ===== ELIMINAR ORDENES (Bulk) =====
@require_POST
@login_required
@user_passes_test(es_superusuario)
def bulk_delete(request):
    ids = request.POST.getlist("ids") or request.POST.getlist("selected")
    if not ids:
        messages.warning(request, "No seleccionaste ninguna orden.")
        return redirect("orders:list")

    qs = ServiceOrder.objects.filter(id__in=ids)
    count = qs.count()
    qs.delete()

    messages.success(request, f"Se eliminaron {count} órdenes correctamente.")
    return redirect("orders:list")

# ===== ENVIAR CORREO MANUAL =====
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
            'print_mode': True,
            'firma_ingeniero_url': obtener_firma_ingeniero(order.ingeniero_nombre, request)
        }, request=request)

        pdf_bytes = weasyprint.HTML(
            string=html_string,
            base_url=request.build_absolute_uri()
        ).write_pdf()

        # 2. Configurar SMTP
        smtp_server = settings.EMAIL_HOST
        smtp_port = settings.EMAIL_PORT
        smtp_user = settings.EMAIL_HOST_USER
        smtp_password = settings.EMAIL_HOST_PASSWORD

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

        attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
        attachment.add_header('Content-Disposition', 'attachment', filename=f"{order.folio}.pdf")
        msg.attach(attachment)

        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
        server.starttls(context=context)
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()

        order.email_enviado = True
        order.save(update_fields=['email_enviado'])
        messages.success(request, f"Correo reenviado exitosamente a {order.cliente_email}")

    except Exception as e:
        print(f"❌ ERROR SMTP: {e}")
        messages.error(request, f"Error al enviar correo: {e}")

    return redirect('orders:detail', pk=pk)


# ================================================================
# GESTIÓN DE USUARIOS
# ================================================================

@login_required
@user_passes_test(es_superusuario)
def user_list_view(request):
    users = User.objects.all().order_by('username')
    return render(request, 'orders/user_list.html', {'users': users})

@login_required
@user_passes_test(es_superusuario)
def create_user_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.password = make_password(form.cleaned_data['password'])
            
            role = form.cleaned_data['role']
            user.is_staff = (role in ['ingeniero', 'superuser'])
            user.is_superuser = (role == 'superuser')
            user.save()

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
    user_to_edit = get_object_or_404(User, pk=pk)
    
    rol_inicial = 'visor'
    if user_to_edit.is_superuser: rol_inicial = 'superuser'
    elif user_to_edit.is_staff: rol_inicial = 'ingeniero'

    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user_to_edit)
        if form.is_valid():
            user = form.save(commit=False)
            if form.cleaned_data['password']:
                user.password = make_password(form.cleaned_data['password'])
            
            role = form.cleaned_data['role']
            user.is_staff = (role in ['ingeniero', 'superuser'])
            user.is_superuser = (role == 'superuser')
            user.save()

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

# ===== LOGIN / LOGOUT =====
def login_view(request):
    pass

@require_POST
@never_cache # <--- Evita que el navegador guarde la página después de salir
def logout_view(request):
    logout(request)
    messages.info(request, "Has cerrado sesión.")
    return redirect("login")