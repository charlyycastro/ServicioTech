from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import logout, authenticate, login
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db.models import Q
from django.conf import settings
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.core.mail import EmailMessage
from django.core.files.base import ContentFile
from django.utils.dateparse import parse_date
from django.contrib.auth.forms import AuthenticationForm 

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
    
    for user in User.objects.all():
        full_name = user.get_full_name()
        if full_name == nombre_ingeniero or user.username == nombre_ingeniero:
            if hasattr(user, 'profile') and user.profile.firma:
                return request.build_absolute_uri(user.profile.firma.url)
    return None

# --- NUEVA FUNCIÓN: Obtener la firma del Contacto Interno/Ventas ---
def obtener_firma_contacto_interno(nombre_contacto, request):
    """Busca el perfil del usuario Visor/Contacto por nombre y retorna la URL de su firma."""
    if not nombre_contacto:
        return None
    
    for user in User.objects.all():
        full_name = user.get_full_name()
        if full_name == nombre_contacto or user.username == nombre_contacto:
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
    orders = ServiceOrder.objects.all().order_by('-creado')

    # --- CAPTURA Y APLICACIÓN DE FILTROS ---
    query = request.GET.get('q', '').strip()
    filtro_empresa = request.GET.get('empresa')
    filtro_estatus = request.GET.get('estatus')
    filtro_ingeniero = request.GET.get('ingeniero')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')


    if query:
        orders = orders.filter(Q(folio__icontains=query) | Q(cliente_nombre__icontains=query) | Q(cliente_contacto__icontains=query) | Q(titulo__icontains=query))
    if filtro_empresa:
        orders = orders.filter(cliente_nombre=filtro_empresa)
    if filtro_estatus:
        orders = orders.filter(estatus=filtro_estatus)
    if filtro_ingeniero:
        orders = orders.filter(ingeniero_nombre__icontains=filtro_ingeniero)
    if fecha_inicio:
        orders = orders.filter(creado__date__gte=fecha_inicio) 
    if fecha_fin:
        orders = orders.filter(creado__date__lte=fecha_fin)


    # PREPARACIÓN DE CONTEXTO Y PAGINACIÓN
    empresas = ServiceOrder.objects.exclude(cliente_nombre__isnull=True).exclude(cliente_nombre__exact='').values_list('cliente_nombre', flat=True).distinct().order_by('cliente_nombre')
    ingenieros_list = ServiceOrder.objects.exclude(ingeniero_nombre__isnull=True).exclude(ingeniero_nombre__exact='').values_list('ingeniero_nombre', flat=True).distinct().order_by('ingeniero_nombre')

    paginator = Paginator(orders, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    ctx = {
        'page_obj': page_obj, 
        'query': query,
        'empresas': empresas,
        'ingenieros_list': ingenieros_list,
        'filtro_empresa': filtro_empresa,
        'filtro_estatus': filtro_estatus,
        'filtro_ingeniero': filtro_ingeniero,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,       
        'STATUS_CHOICES': ServiceOrder.STATUS_CHOICES 
    }
    return render(request, 'orders/order_list.html', ctx)

@login_required
def order_detail(request, pk):
    order = get_object_or_404(ServiceOrder, pk=pk)
    
    # Firma de Ingeniero
    firma_ingeniero_url = obtener_firma_ingeniero(order.ingeniero_nombre, request)
    
    # Firma de Contacto Interno/Ventas (Visor)
    firma_contacto_url = obtener_firma_contacto_interno(order.contacto_nombre, request)
    
    return render(request, 'orders/order_detail.html', {
        'object': order, 
        'firma_ingeniero_url': firma_ingeniero_url,
        'firma_contacto_url': firma_contacto_url,
    })

# ===== CREAR ORDEN (Con Resguardos, Evidencias y Pausa) =====
@login_required
@user_passes_test(es_ingeniero_o_admin)
def order_create(request):
    if request.method == "POST":
        form = ServiceOrderForm(request.POST, request.FILES)
        
        equipos_fs = EquipmentFormSet(request.POST, request.FILES, prefix="equipos")
        materiales_fs = ServiceMaterialFormSet(request.POST, request.FILES, prefix="materiales")
        resguardos_fs = ShelterEquipmentFormSet(request.POST, request.FILES, prefix="resguardos")
        evidencias_fs = ServiceEvidenceFormSet(request.POST, request.FILES, prefix="evidencias")

        if form.is_valid() and equipos_fs.is_valid() and materiales_fs.is_valid() and resguardos_fs.is_valid() and evidencias_fs.is_valid():
            order = form.save(commit=False)
            accion = request.POST.get('accion', 'borrador')

            # VALIDACIÓN MANUAL PARA FINALIZAR
            if accion == 'finalizar':
                errores = []
                if not order.cliente_contacto: errores.append("Persona de contacto")
                if not order.cliente_email: errores.append("Correo del cliente")
                if not order.ingeniero_nombre: errores.append("Ingeniero asignado")
                if not order.tipos_servicio: errores.append("Tipo de servicio")
                
                if errores:
                    messages.error(request, f"Para finalizar, faltan: {', '.join(errores)}")
                    ctx = {"form": form, "equipos_fs": equipos_fs, "materiales_fs": materiales_fs, "resguardos_fs": resguardos_fs, "evidencias_fs": evidencias_fs, "titulo": "Nueva Orden de Servicio"}
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
            equipos_fs.instance = order; equipos_fs.save()
            materiales_fs.instance = order; materiales_fs.save()
            resguardos_fs.instance = order; resguardos_fs.save(); evidencias_fs.instance = order; evidencias_fs.save()

            messages.success(request, mensaje_exito)
            return redirect("orders:detail", pk=order.pk)
        else:
            messages.error(request, "Hay errores en el formulario. Revisa los campos en rojo.")
    else:
        # GET: Pre-llenado inicial
        initial_data = {}
        if request.user.is_staff:
             initial_data['ingeniero_nombre'] = request.user.get_full_name() or request.user.username

        form = ServiceOrderForm(initial=initial_data)
        equipos_fs = EquipmentFormSet(prefix="equipos"); materiales_fs = ServiceMaterialFormSet(prefix="materiales")
        resguardos_fs = ShelterEquipmentFormSet(prefix="resguardos"); evidencias_fs = ServiceEvidenceFormSet(prefix="evidencias")

    ctx = {"form": form, "equipos_fs": equipos_fs, "materiales_fs": materiales_fs, "resguardos_fs": resguardos_fs, "evidencias_fs": evidencias_fs, "titulo": "Nueva Orden de Servicio"}
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

            # VALIDACIÓN MANUAL PARA FINALIZAR
            if accion == 'finalizar':
                errores = []
                if not order.cliente_contacto: errores.append("Persona de contacto")
                if not order.cliente_email: errores.append("Correo del cliente")
                if not order.ingeniero_nombre: errores.append("Ingeniero asignado")
                if not order.tipos_servicio: errores.append("Tipo de servicio")
                
                if errores:
                    messages.error(request, f"Para finalizar, faltan: {', '.join(errores)}")
                    ctx = {"form": form, "equipos_fs": equipos_fs, "materiales_fs": materiales_fs, "resguardos_fs": resguardos_fs, "evidencias_fs": evidencias_fs, "titulo": f"Editar Orden {order.folio}"}
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
            equipos_fs.save(); materiales_fs.save(); resguardos_fs.save(); evidencias_fs.save()
            messages.success(request, mensaje)
            return redirect("orders:detail", pk=order.pk)
        else:
            messages.error(request, "Hay errores en el formulario.")
    else:
        form = ServiceOrderForm(instance=order)
        equipos_fs = EquipmentFormSet(instance=order, prefix="equipos"); materiales_fs = ServiceMaterialFormSet(instance=order, prefix="materiales")
        resguardos_fs = ShelterEquipmentFormSet(instance=order, prefix="resguardos"); evidencias_fs = ServiceEvidenceFormSet(instance=order, prefix="evidencias")

    ctx = {"form": form, "equipos_fs": equipos_fs, "materiales_fs": materiales_fs, "resguardos_fs": resguardos_fs, "evidencias_fs": evidencias_fs, "titulo": f"Editar Orden {order.folio}"}
    return render(request, "orders/order_form.html", ctx)


# ===== ENVIAR CORREO MANUAL (Actualizado con Firma de Contacto) =====
@login_required
@user_passes_test(es_ingeniero_o_admin)
def email_order(request, pk):
    order = get_object_or_404(ServiceOrder, pk=pk)

    if not order.cliente_email:
        messages.warning(request, "Esta orden no tiene un correo de cliente registrado.")
        return redirect('orders:detail', pk=pk)

    # 1. VALIDACIONES DE FIRMA
    firma_ingeniero_url = obtener_firma_ingeniero(order.ingeniero_nombre, request)
    firma_contacto_url = obtener_firma_contacto_interno(order.contacto_nombre, request) # <-- Nueva Firma Visor/Ventas

    if not firma_ingeniero_url:
        messages.error(request, f"No se puede enviar. El perfil del ingeniero '{order.ingeniero_nombre}' no tiene firma digital precargada.")
        return redirect('orders:detail', pk=pk)

    try:
        # 2. GENERAR PDF
        html_string = render_to_string('orders/order_detail.html', {
            'object': order, 
            'print_mode': True, 
            'firma_ingeniero_url': firma_ingeniero_url,
            'firma_contacto_url': firma_contacto_url # <-- Pasamos la firma del Contacto
        }, request=request)

        pdf_bytes = weasyprint.HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

        # 3. ENVIAR CORREO (Lógica SMTP simplificada)
        subject = f"Reporte de Servicio {order.folio} - ServicioTech"
        survey_link = "https://www.cognitoforms.com/INOVATECH1/EncuestaDeServicio" # Usando el link de encuesta

        body = (
            f"Hola {order.cliente_contacto or 'Cliente'},\n\n"
            f"Adjunto encontrarás el reporte de servicio técnico realizado el {order.fecha_servicio}.\n\n"
            f"Folio: {order.folio}\n"
            f"Título: {order.titulo}\n\n"
            "=============================================\n"
            "¡AYÚDANOS A MEJORAR! (Encuesta de Satisfacción)\n"
            "=============================================\n"
            "Por favor, tómate un minuto para calificar nuestro servicio haciendo clic en el siguiente enlace:\n"
            f"{survey_link}\n\n" 
            "Gracias por tu preferencia.\n"
            "Atentamente,\n"
            "El equipo de ServicioTech."
        )

        email = EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, [order.cliente_email])
        email.attach(f"{order.folio}.pdf", pdf_bytes, 'application/pdf')

        email.send(fail_silently=False) 

        order.email_enviado = True
        order.save(update_fields=['email_enviado'])
        messages.success(request, f"Correo enviado correctamente a {order.cliente_email}")

    except Exception as e:
        error_msg = f"Error al enviar/generar PDF. Detalles: {e}"
        print(f"❌ ERROR EN EL ENVÍO: {e}")
        messages.error(request, error_msg)

    return redirect('orders:detail', pk=pk)


# ===== DASHBOARD =====
@login_required
def dashboard_view(request):
    nombre_usuario = request.user.get_full_name() or request.user.username
    total_ordenes = ServiceOrder.objects.count()
    pendientes = ServiceOrder.objects.filter(estatus='borrador').count()
    finalizadas = ServiceOrder.objects.filter(estatus='finalizado').count()
    
    # Mis Asignaciones (Cuenta TODO del ingeniero, sin importar el estatus)
    mis_asignadas = ServiceOrder.objects.filter(ingeniero_nombre__icontains=nombre_usuario).count()
    
    recientes = ServiceOrder.objects.all().order_by('-creado')[:5]

    context = {'total': total_ordenes, 'pendientes': pendientes, 'finalizadas': finalizadas, 'mis_asignadas': mis_asignadas, 'recientes': recientes}
    return render(request, 'orders/dashboard.html', context)


# ===== GESTIÓN DE USUARIOS (CRUD RESTAURADO) =====
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
            role = form.cleaned_data['role']; user.is_staff = (role in ['ingeniero', 'superuser'])
            user.is_superuser = (role == 'superuser'); user.save()

            firma_b64 = form.cleaned_data.get('firma_b64')
            # Permite guardar la firma para cualquier rol si se proporciona el dato
            if firma_b64: guardar_firma(user, firma_b64)

            messages.success(request, f"Usuario {user.username} creado correctamente.")
            return redirect('orders:user_list')
    else: form = CustomUserCreationForm()
    
    return render(request, 'orders/user_form.html', {'form': form, 'titulo': 'Alta de Nuevo Usuario'})

@login_required
@user_passes_test(es_superusuario)
def edit_user_view(request, pk):
    user_to_edit = get_object_or_404(User, pk=pk)
    rol_inicial = 'visor'
    if user_to_edit.is_superuser: rol_inicial = 'superuser';
    elif user_to_edit.is_staff: rol_inicial = 'ingeniero'

    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user_to_edit)
        if form.is_valid():
            user = form.save(commit=False)
            if form.cleaned_data['password']: user.password = make_password(form.cleaned_data['password'])
            
            role = form.cleaned_data['role']; user.is_staff = (role in ['ingeniero', 'superuser'])
            user.is_superuser = (role == 'superuser'); user.save()

            firma_b64 = form.cleaned_data.get('firma_b64')
            # Permite guardar la firma para cualquier rol si se proporciona el dato
            if firma_b64: guardar_firma(user, firma_b64)

            messages.success(request, f"Usuario {user.username} actualizado.")
            return redirect('orders:user_list')
        else: messages.error(request, "Error al actualizar usuario. Revisa los campos.")
    else: form = UserEditForm(instance=user_to_edit, initial={'role': rol_inicial})

    return render(request, 'orders/user_form.html', {'form': form, 'titulo': f'Editar a {user_to_edit.username}'})

@login_required
@user_passes_test(es_superusuario)
def delete_user_view(request, pk):
    user_to_delete = get_object_or_404(User, pk=pk)
    if user_to_delete == request.user: messages.error(request, "No puedes eliminar tu propio usuario.")
    else: user_to_delete.delete(); messages.success(request, "Usuario eliminado permanentemente.")
    return redirect('orders:user_list')

# ===== UTILIDADES / AUTENTICACIÓN =====
@require_POST
@login_required
@user_passes_test(es_superusuario)
def bulk_delete(request):
    ids = request.POST.getlist("ids") or request.POST.getlist("selected")
    if not ids: messages.warning(request, "No seleccionaste ninguna orden."); return redirect("orders:list")

    qs = ServiceOrder.objects.filter(id__in=ids); count = qs.count(); qs.delete()
    messages.success(request, f"Se eliminaron {count} órdenes correctamente.")
    return redirect("orders:list")

def login_view(request): pass

@require_POST
@never_cache 
def logout_view(request):
    logout(request); messages.info(request, "Has cerrado sesión."); return redirect("login")