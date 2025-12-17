import os
import uuid
import base64
import unicodedata
import weasyprint 

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
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
from django.core.mail import EmailMessage
from django.core.files.base import ContentFile
from django.utils.dateparse import parse_date
from django.db import IntegrityError

# --- Imports para Word ---
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# --- MODELOS Y FORMULARIOS ---
from .models import ServiceOrder, EngineerProfile, ServiceEvidence 
from .forms import (
    ServiceOrderForm, EquipmentFormSet, ServiceMaterialFormSet,
    ShelterEquipmentFormSet, ServiceEvidenceFormSet,
    CustomUserCreationForm, UserEditForm
)

# ================================================================
# HELPERS (FUNCIONES DE APOYO)
# ================================================================

def es_ingeniero_o_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

def es_superusuario(user):
    return user.is_authenticated and user.is_superuser

def obtener_firma_ingeniero(nombre_busqueda, request):
    """
    Busca la firma de un usuario (Ingeniero o Visor).
    Es 'inteligente': ignora mayúsculas y busca por Nombre Completo o Usuario.
    """
    if not nombre_busqueda:
        return None
    
    # Convertimos a string y minúsculas para comparar
    busqueda = str(nombre_busqueda).lower().strip()
    
    for user in User.objects.all():
        # Obtenemos nombre y usuario del sistema en minúsculas
        full_name = (user.get_full_name() or "").lower().strip()
        username = user.username.lower().strip()
        
        # Comparamos: ¿Coincide el nombre O el usuario?
        if full_name == busqueda or username == busqueda:
            # Si encontramos al usuario, buscamos su firma en cualquier perfil
            if hasattr(user, 'engineerprofile') and user.engineerprofile.firma:
                return request.build_absolute_uri(user.engineerprofile.firma.url)
            elif hasattr(user, 'profile') and user.profile.firma:
                return request.build_absolute_uri(user.profile.firma.url)
                
    return None

def guardar_firma(user, data_url):
    """Guarda la firma base64 en el perfil del usuario."""
    try:
        if ';base64,' in data_url:
            format, imgstr = data_url.split(';base64,') 
            ext = format.split('/')[-1] 
            data = ContentFile(base64.b64decode(imgstr), name=f'firma_{user.username}_{uuid.uuid4()}.{ext}')
            
            if hasattr(user, 'engineerprofile'):
                profile, _ = EngineerProfile.objects.get_or_create(user=user)
                profile.firma = data
                profile.save()
            elif hasattr(user, 'profile'):
                user.profile.firma = data
                user.profile.save()
            else:
                # Si no tiene perfil, creamos uno de Ingeniero por defecto
                profile = EngineerProfile.objects.create(user=user)
                profile.firma = data
                profile.save()
    except Exception as e:
        print(f"Error guardando firma: {e}")

# ================================================================
# DASHBOARD
# ================================================================

@login_required
def dashboard_view(request):
    user = request.user
    pendientes = 0; mis_asignadas = 0; finalizadas = 0; total = 0; recientes = []

    if user.is_superuser:
        pendientes = ServiceOrder.objects.filter(estatus='borrador').count()
        nombre = (user.get_full_name() or user.username)
        mis_asignadas = ServiceOrder.objects.filter(ingeniero_nombre__icontains=nombre).exclude(estatus='finalizado').count()
        finalizadas = ServiceOrder.objects.filter(estatus='finalizado').count()
        total = ServiceOrder.objects.count()
        recientes = ServiceOrder.objects.all().order_by('-creado')[:5]
    else:
        nombre = (user.get_full_name() or user.username)
        mis_ordenes = ServiceOrder.objects.filter(ingeniero_nombre__icontains=nombre)
        pendientes = mis_ordenes.filter(estatus='borrador').count()
        mis_asignadas = mis_ordenes.count()
        finalizadas = ServiceOrder.objects.filter(estatus='finalizado').count()
        total = ServiceOrder.objects.count()
        recientes = ServiceOrder.objects.all().order_by('-creado')[:5]

    return render(request, 'orders/dashboard.html', locals())

# ================================================================
# CRUD DE ÓRDENES
# ================================================================

@login_required
def order_list(request):
    orders = ServiceOrder.objects.all().order_by('-creado')
    query = request.GET.get('q', '').strip()
    
    if query:
        orders = orders.filter(
            Q(folio__icontains=query) | Q(cliente_nombre__icontains=query) |
            Q(cliente_contacto__icontains=query) | Q(titulo__icontains=query)
        )
    
    # Filtros
    if request.GET.get('empresa'): orders = orders.filter(cliente_nombre=request.GET.get('empresa'))
    if request.GET.get('estatus'): orders = orders.filter(estatus=request.GET.get('estatus'))
    if request.GET.get('ingeniero'): orders = orders.filter(ingeniero_nombre=request.GET.get('ingeniero'))
    if request.GET.get('fecha_inicio'): orders = orders.filter(creado__date__gte=request.GET.get('fecha_inicio'))
    if request.GET.get('fecha_fin'): orders = orders.filter(creado__date__lte=request.GET.get('fecha_fin'))

    empresas = ServiceOrder.objects.values_list('cliente_nombre', flat=True).distinct().order_by('cliente_nombre')
    ingenieros_list = ServiceOrder.objects.values_list('ingeniero_nombre', flat=True).distinct().order_by('ingeniero_nombre')

    paginator = Paginator(orders, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    ctx = {
        'page_obj': page_obj, 'query': query, 'empresas': empresas, 
        'ingenieros_list': ingenieros_list, 'STATUS_CHOICES': ServiceOrder.STATUS_CHOICES
    }
    return render(request, 'orders/order_list.html', ctx)

@login_required
def order_detail(request, pk):
    order = get_object_or_404(ServiceOrder, pk=pk)
    
    # Buscamos firmas (Ingeniero Y Visor) y las mandamos al HTML
    firma_ing = obtener_firma_ingeniero(order.ingeniero_nombre, request)
    firma_vis = obtener_firma_ingeniero(order.contacto_nombre, request)

    return render(request, 'orders/order_detail.html', {
        'object': order,
        'firma_ingeniero_url': firma_ing,
        'firma_visor_url': firma_vis, 
    })

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
            
            if accion == 'finalizar':
                if not all([order.cliente_contacto, order.cliente_email, order.ingeniero_nombre]):
                    messages.error(request, "Faltan datos obligatorios para finalizar.")
                    return render(request, "orders/order_form.html", locals())
                order.estatus = 'finalizado'
                msg = f"Orden {order.folio} FINALIZADA."
            else:
                order.estatus = 'borrador'
                msg = "Borrador guardado."

            # Firma Cliente
            firma_b64 = request.POST.get("firma_b64", "").strip()
            if firma_b64.startswith("data:image"):
                try:
                    head, data = firma_b64.split(",", 1)
                    ext = "png" if "png" in head else "jpg"
                    order.firma = ContentFile(base64.b64decode(data), name=f"firma_cli_{uuid.uuid4().hex}.{ext}")
                except: pass

            order.save()
            equipos_fs.instance = order; equipos_fs.save()
            materiales_fs.instance = order; materiales_fs.save()
            resguardos_fs.instance = order; resguardos_fs.save()
            evidencias_fs.instance = order; evidencias_fs.save()

            # --- CARGA MASIVA DE FOTOS ---
            imagenes_extra = request.FILES.getlist('imagenes_masivas')
            if imagenes_extra:
                for img in imagenes_extra:
                    ServiceEvidence.objects.create(order=order, archivo=img, comentario="Carga masiva")
                messages.info(request, f"📸 {len(imagenes_extra)} fotos adicionales subidas.")

            messages.success(request, msg)
            return redirect("orders:detail", pk=order.pk)
        else:
            messages.error(request, "Errores en el formulario. Revisa los campos rojos.")
    else:
        initial = {'ingeniero_nombre': request.user.get_full_name()} if request.user.is_staff else {}
        form = ServiceOrderForm(initial=initial)
        equipos_fs = EquipmentFormSet(prefix="equipos")
        materiales_fs = ServiceMaterialFormSet(prefix="materiales")
        resguardos_fs = ShelterEquipmentFormSet(prefix="resguardos")
        evidencias_fs = ServiceEvidenceFormSet(prefix="evidencias")

    return render(request, "orders/order_form.html", locals())

@login_required
@user_passes_test(es_ingeniero_o_admin)
def order_update(request, pk):
    order = get_object_or_404(ServiceOrder, pk=pk)
    if not request.user.is_superuser and order.estatus == 'finalizado':
        messages.error(request, "No puedes editar una orden finalizada.")
        return redirect('orders:detail', pk=pk)

    if request.method == "POST":
        form = ServiceOrderForm(request.POST, request.FILES, instance=order)
        equipos_fs = EquipmentFormSet(request.POST, request.FILES, instance=order, prefix="equipos")
        materiales_fs = ServiceMaterialFormSet(request.POST, request.FILES, instance=order, prefix="materiales")
        resguardos_fs = ShelterEquipmentFormSet(request.POST, request.FILES, instance=order, prefix="resguardos")
        evidencias_fs = ServiceEvidenceFormSet(request.POST, request.FILES, instance=order, prefix="evidencias")

        if form.is_valid() and equipos_fs.is_valid() and materiales_fs.is_valid() and resguardos_fs.is_valid() and evidencias_fs.is_valid():
            order = form.save(commit=False)
            accion = request.POST.get('accion', 'borrador')
            
            if accion == 'finalizar':
                order.estatus = 'finalizado'
            else:
                order.estatus = 'borrador'

            firma_b64 = request.POST.get("firma_b64", "").strip()
            if firma_b64.startswith("data:image"):
                try:
                    head, data = firma_b64.split(",", 1)
                    ext = "png" if "png" in head else "jpg"
                    order.firma = ContentFile(base64.b64decode(data), name=f"firma_cli_{uuid.uuid4().hex}.{ext}")
                except: pass

            order.save()
            equipos_fs.save(); materiales_fs.save(); resguardos_fs.save(); evidencias_fs.save()

            # --- CARGA MASIVA DE FOTOS (EDICIÓN) ---
            imagenes_extra = request.FILES.getlist('imagenes_masivas')
            if imagenes_extra:
                for img in imagenes_extra:
                    ServiceEvidence.objects.create(order=order, archivo=img, comentario="Carga masiva")
                messages.info(request, f"📸 {len(imagenes_extra)} fotos adicionales subidas.")

            messages.success(request, "Orden actualizada.")
            return redirect("orders:detail", pk=order.pk)
    else:
        form = ServiceOrderForm(instance=order)
        equipos_fs = EquipmentFormSet(instance=order, prefix="equipos")
        materiales_fs = ServiceMaterialFormSet(instance=order, prefix="materiales")
        resguardos_fs = ShelterEquipmentFormSet(instance=order, prefix="resguardos")
        evidencias_fs = ServiceEvidenceFormSet(instance=order, prefix="evidencias")
    
    ctx = {"form": form, "equipos_fs": equipos_fs, "materiales_fs": materiales_fs,
           "resguardos_fs": resguardos_fs, "evidencias_fs": evidencias_fs, "titulo": f"Editar {order.folio}"}
    return render(request, "orders/order_form.html", ctx)

@require_POST
@login_required
@user_passes_test(es_superusuario)
def bulk_delete(request):
    ids = request.POST.getlist("ids") or request.POST.getlist("selected")
    if ids:
        ServiceOrder.objects.filter(id__in=ids).delete()
        messages.success(request, "Órdenes eliminadas.")
    return redirect("orders:list")

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
            firma = form.cleaned_data.get('firma_b64')
            if firma and role in ['ingeniero', 'visor']: guardar_firma(user, firma)
            messages.success(request, f"Usuario {user.username} creado.")
            return redirect('orders:user_list')
    else:
        form = CustomUserCreationForm()
    return render(request, 'orders/user_form.html', {'form': form, 'titulo': 'Alta de Nuevo Usuario'})

@login_required
@user_passes_test(es_superusuario)
def edit_user_view(request, pk):
    u_edit = get_object_or_404(User, pk=pk)
    role_ini = 'superuser' if u_edit.is_superuser else 'ingeniero' if u_edit.is_staff else 'visor'
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=u_edit)
        if form.is_valid():
            user = form.save(commit=False)
            if form.cleaned_data['password']: user.password = make_password(form.cleaned_data['password'])
            role = form.cleaned_data['role']
            user.is_staff = (role in ['ingeniero', 'superuser'])
            user.is_superuser = (role == 'superuser')
            user.save()
            firma = form.cleaned_data.get('firma_b64')
            if firma and role in ['ingeniero', 'visor']: guardar_firma(user, firma)
            messages.success(request, f"Usuario actualizado.")
            return redirect('orders:user_list')
    else:
        form = UserEditForm(instance=u_edit, initial={'role': role_ini})
    return render(request, 'orders/user_form.html', {'form': form, 'titulo': f'Editar a {u_edit.username}'})

@login_required
@user_passes_test(es_superusuario)
def delete_user_view(request, pk):
    u = get_object_or_404(User, pk=pk)
    if u.is_superuser:
        messages.error(request, "No puedes eliminar al Superadmin.")
    else:
        try: u.delete(); messages.success(request, "Usuario eliminado.")
        except: messages.error(request, "Error eliminando usuario.")
    return redirect('orders:user_list')

# ================================================================
# LOGIN / LOGOUT
# ================================================================

def login_view(request):
    return redirect('account_login')

@require_POST
@never_cache 
def logout_view(request):
    logout(request)
    messages.info(request, "Has cerrado sesión.")
    return redirect("account_login")

# ================================================================
# CORREO
# ================================================================

@login_required
@user_passes_test(es_ingeniero_o_admin)
def email_order(request, pk):
    order = get_object_or_404(ServiceOrder, pk=pk)
    if not order.cliente_email:
        messages.warning(request, "Falta correo del cliente.")
        return redirect('orders:detail', pk=pk)

    # Obtenemos ambas firmas para el PDF
    firma_ing = obtener_firma_ingeniero(order.ingeniero_nombre, request)
    firma_vis = obtener_firma_ingeniero(order.contacto_nombre, request)
    survey = "https://www.cognitoforms.com/INOVATECH1/EncuestaDeServicio"

    try:
        # Generar PDF
        html = render_to_string('orders/order_detail.html', {
            'object': order, 
            'print_mode': True, 
            'firma_ingeniero_url': firma_ing,
            'firma_visor_url': firma_vis,
            'es_pdf': True 
        }, request=request)
        
        pdf = weasyprint.HTML(string=html, base_url=request.build_absolute_uri()).write_pdf()

        msg = EmailMessage(
            subject=f"Reporte Servicio {order.folio}",
            body=f"Hola {order.cliente_contacto},\n\nAdjunto reporte.\nCalifícanos: {survey}\n\nAtte, ServicioTech.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.cliente_email]
        )
        msg.attach(f"{order.folio}.pdf", pdf, "application/pdf")
        msg.send(fail_silently=False)

        order.email_enviado = True
        order.save(update_fields=['email_enviado'])
        messages.success(request, f"Enviado a {order.cliente_email}")

    except Exception as e:
        messages.error(request, f"Error: {e}")

    return redirect('orders:detail', pk=pk)

# ================================================================
# WORD GENERATION (HELPERS)
# ================================================================

def set_cell_color(cell, color):
    tc = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:fill'), color)
    tc.append(shd)

def make_header_blue(cell, text):
    cell.text = ""; p = cell.paragraphs[0]; r = p.add_run(text)
    r.bold = True; r.font.color.rgb = RGBColor(255,255,255); set_cell_color(cell, '1F4E78')

def make_label_gray(cell, text):
    cell.text = ""; p = cell.paragraphs[0]; r = p.add_run(text)
    r.bold = True; r.font.size = Pt(9); r.font.color.rgb = RGBColor(0,0,0); set_cell_color(cell, 'F2F2F2')

def set_value_text(cell, text):
    cell.text = str(text) if text else "-"; cell.paragraphs[0].runs[0].font.size = Pt(9)

def insert_signature(cell, title, img_field, name):
    cell.text = ""; p = cell.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if img_field:
        try:
            if hasattr(img_field, 'path') and os.path.exists(img_field.path):
                p.add_run().add_picture(img_field.path, height=Inches(0.6))
            elif isinstance(img_field, str) and os.path.exists(img_field):
                p.add_run().add_picture(img_field, height=Inches(0.6))
        except: pass
    else: p.add_run("\n\n\n")
    p.add_run("\n_______________________\n")
    if name: p.add_run(str(name)+"\n").bold=True
    p.add_run(title).font.size = Pt(7)

# ==============================================================================
# VISTA PRINCIPAL DE DESCARGA DE WORD (COMPLETA)
# ==============================================================================
@login_required
def download_word(request, pk):
    from docx.enum.table import WD_TABLE_ALIGNMENT 
    
    order = get_object_or_404(ServiceOrder, pk=pk)
    doc = Document()
    s = doc.sections[0]; s.left_margin=s.right_margin=s.top_margin=s.bottom_margin = Inches(0.4)
    w_total = s.page_width - s.left_margin - s.right_margin

    # 1. Header
    t = doc.add_table(rows=1, cols=3); t.autofit=False; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.columns[0].width = int(w_total*0.2); t.columns[1].width = int(w_total*0.5); t.columns[2].width = int(w_total*0.3)
    
    logo = os.path.join(settings.BASE_DIR, 'static', 'orders', 'inovatech-logo.png')
    if os.path.exists(logo): t.rows[0].cells[0].paragraphs[0].add_run().add_picture(logo, width=Inches(1.2))
    
    p = t.rows[0].cells[1].paragraphs[0]; p.alignment=1
    r = p.add_run("ORDEN DE SERVICIO TÉCNICO"); r.bold=True; r.font.size=Pt(16); r.font.color.rgb=RGBColor(31,78,120)
    
    tf = t.rows[0].cells[2].add_table(rows=2, cols=1); tf.alignment=2
    tbl = tf._tbl; borders = OxmlElement('w:tblBorders')
    for b in ['top','left','bottom','right','insideH']:
        el = OxmlElement(f'w:{b}'); el.set(qn('w:val'),'single'); el.set(qn('w:sz'),'4'); borders.append(el)
    tbl.tblPr.append(borders)
    
    tf.cell(0,0).paragraphs[0].add_run("FOLIO").bold=True
    r = tf.cell(1,0).paragraphs[0].add_run(str(order.folio)); r.bold=True; r.font.color.rgb=RGBColor(192,0,0); r.font.size=Pt(12)
    doc.add_paragraph()

    # 2. Body
    t = doc.add_table(rows=0, cols=4); t.style='Table Grid'
    w1=int(w_total*0.15); w2=int(w_total*0.35)
    for i in range(4): t.columns[i].width = w1 if i%2==0 else w2

    # A. Info
    r=t.add_row(); r.cells[0].merge(r.cells[3]); make_header_blue(r.cells[0], " A. INFORMACIÓN GENERAL")
    r=t.add_row(); make_label_gray(r.cells[0],"1. Cliente"); set_value_text(r.cells[1], order.cliente_nombre)
    make_label_gray(r.cells[2],"2. Ubicación"); set_value_text(r.cells[3], order.ubicacion)
    
    r=t.add_row(); make_label_gray(r.cells[0],"3. Fecha"); set_value_text(r.cells[1], order.fecha_servicio)
    make_label_gray(r.cells[2],"4. Contacto"); set_value_text(r.cells[3], order.cliente_contacto)

    r=t.add_row(); make_label_gray(r.cells[0],"5. Tipo serv.")
    bd = str(order.tipos_servicio).lower()
    chk = lambda x: "☒" if x in bd else "☐"
    txt = (f"{chk('instal')} Instalación   {chk('config')} Configuración\n"
           f"{chk('mantenim')} Mantenimiento   {chk('garant')} Garantía\n"
           f"{chk('revis')} Falla/Revisión   {chk('capacit')} Capacitación")
    set_value_text(r.cells[1], txt)
    make_label_gray(r.cells[2],"6. Ingeniero"); set_value_text(r.cells[3], order.ingeniero_nombre)

    r=t.add_row(); set_cell_color(r.cells[0],'FFFFFF'); set_cell_color(r.cells[1],'FFFFFF')
    make_label_gray(r.cells[2],"7. ID Ticket"); set_value_text(r.cells[3], order.ticket_id)

    # B. Equipo
    r=t.add_row(); r.cells[0].merge(r.cells[3]); make_header_blue(r.cells[0], " B. DATOS DEL EQUIPO")
    r=t.add_row()
    for i,x in enumerate(["Marca","Modelo","Serie","Descripción"]): make_label_gray(r.cells[i], x)
    eq = order.equipos.first()
    r=t.add_row()
    if eq:
        set_value_text(r.cells[0], eq.marca); set_value_text(r.cells[1], eq.modelo)
        set_value_text(r.cells[2], eq.serie); set_value_text(r.cells[3], eq.descripcion)
    else: r.cells[0].merge(r.cells[3]); set_value_text(r.cells[0], "Sin equipo.")

    # C. Datos
    r=t.add_row(); r.cells[0].merge(r.cells[3]); make_header_blue(r.cells[0], " C. DATOS TÉCNICOS")
    r=t.add_row(); make_label_gray(r.cells[0],"1. Título"); r.cells[1].merge(r.cells[3]); set_value_text(r.cells[1], order.titulo)
    
    r=t.add_row(); make_label_gray(r.cells[0],"2. Actividades"); c=r.cells[1]; c.merge(r.cells[3]); c.text=""
    c.paragraphs[0].add_run(str(order.actividades)).font.size=Pt(9)
    
    # Fotos
    if order.evidencias.exists():
        c.paragraphs[0].add_run("\n\n--- EVIDENCIA FOTOGRÁFICA ---\n").bold=True
        for f in order.evidencias.all():
            if f.archivo and os.path.exists(f.archivo.path):
                try: c.paragraphs[0].add_run().add_picture(f.archivo.path, width=Inches(3.0))
                except: pass

    r=t.add_row(); make_label_gray(r.cells[0],"3. Comentarios"); r.cells[1].merge(r.cells[3]); set_value_text(r.cells[1], order.comentarios)

    # D. Costos
    r=t.add_row(); r.cells[0].merge(r.cells[3]); make_header_blue(r.cells[0], " D. COSTOS Y TIEMPOS")
    r=t.add_row(); make_label_gray(r.cells[0],"Tiempo (hrs)"); set_value_text(r.cells[1], order.horas)
    make_label_gray(r.cells[2],"Costo"); set_value_text(r.cells[3], str(order.costo_mxn))

    # E. Firmas
    r=t.add_row(); r.cells[0].merge(r.cells[3]); make_header_blue(r.cells[0], " E. ACEPTACIÓN DEL SERVICIO")
    r=t.add_row(); r.cells[0].merge(r.cells[3])
    r.cells[0].paragraphs[0].add_run("Al firmar acepta conformidad.").font.size=Pt(7)

    r=t.add_row(); c=r.cells[0]; c.merge(r.cells[3]); ts=c.add_table(rows=1,cols=3); ts.autofit=False; ts.alignment=1
    w3 = int(w_total/3)
    for cl in ts.rows[0].cells: cl.width = w3

    # Buscar usuarios (Insensible a mayúsculas)
    def find_u(n):
        if not n: return None
        target = str(n).lower().strip()
        for u in User.objects.all():
            fn = (u.get_full_name() or "").lower().strip()
            un = u.username.lower().strip()
            if fn == target or un == target: return u
        return None

    fi = None; ui = find_u(order.ingeniero_nombre)
    if ui:
        if hasattr(ui,'engineerprofile') and ui.engineerprofile.firma: fi=ui.engineerprofile.firma
        elif hasattr(ui,'profile') and ui.profile.firma: fi=ui.profile.firma
    
    fv = None; uv = find_u(order.contacto_nombre)
    if uv:
        if hasattr(uv,'engineerprofile') and uv.engineerprofile.firma: fv=uv.engineerprofile.firma
        elif hasattr(uv,'profile') and uv.profile.firma: fv=uv.profile.firma

    insert_signature(ts.cell(0,0), "Ingeniero de Soporte", fi, order.ingeniero_nombre)
    insert_signature(ts.cell(0,1), "Cliente", order.firma, order.cliente_contacto)
    insert_signature(ts.cell(0,2), "Contacto Interno / Visor", fv, order.contacto_nombre)

    resp = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    resp['Content-Disposition'] = f'attachment; filename="Orden_{order.folio}.docx"'
    doc.save(resp)
    return resp