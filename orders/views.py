from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import logout
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db.models import Q
from django.conf import settings
from django.core.paginator import Paginator

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


# ===== LISTA =====
def order_list(request):
    q = (request.GET.get("q") or "").strip()

    qs = ServiceOrder.objects.all()
    if q:
        qs = qs.filter(
            Q(folio__icontains=q) |
            Q(ticket_id__icontains=q) |
            Q(cliente_nombre__icontains=q) |
            Q(titulo__icontains=q)
        )
    qs = qs.order_by("-id")

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get("page") or 1)

    return render(
        request,
        "orders/order_list.html",
        {
            "ordenes": page_obj.object_list,   # lo que itera la plantilla
            "page_obj": page_obj,
            "paginator": paginator,
            "is_paginated": page_obj.has_other_pages(),
            "q": q,  # para mantener el valor en el input de búsqueda
        },
    )


# ===== DIAGNÓSTICO OPCIONAL =====
@login_required
def order_list_diag(request):
    n = ServiceOrder.objects.count()
    tpl = get_template("orders/order_list.html").origin.name
    db = settings.DATABASES["default"]
    return HttpResponse(
        "DIAG\n"
        f"count={n}\n"
        f"db={db}\n"
        f"template={tpl}\n",
        content_type="text/plain; charset=utf-8"
    )


# ===== DETALLE =====
@login_required
def order_detail(request, pk):
    obj = get_object_or_404(ServiceOrder, pk=pk)
    return render(request, "orders/order_detail.html", {"object": obj})


# ===== CREAR =====

@login_required
def order_create(request):
    if request.method == "POST":
        form = ServiceOrderForm(request.POST, request.FILES)
        equipos_fs = EquipmentFormSet(request.POST, request.FILES, prefix="equipos")
        materiales_fs = ServiceMaterialFormSet(request.POST, request.FILES, prefix="materiales")

        if form.is_valid() and equipos_fs.is_valid() and materiales_fs.is_valid():
            # 1. Guardar la orden y firma
            order = form.save(commit=False)
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

            # 2. Guardar relaciones
            equipos_fs.instance = order
            materiales_fs.instance = order
            equipos_fs.save()
            materiales_fs.save()

            # ========================================================
            #   ENVÍO MANUAL SMTP (BYPASS TOTAL DE SEGURIDAD DJANGO)
            # ========================================================
            if order.cliente_email:
                try:
                    # --- A) Generar PDF ---
                    html_string = render_to_string('orders/order_detail.html', {
                        'object': order,
                        'print_mode': True
                    }, request=request)

                    pdf_bytes = weasyprint.HTML(
                        string=html_string, 
                        base_url=request.build_absolute_uri()
                    ).write_pdf()

                    # --- B) Configurar Servidor SMTP Manualmente ---
                    smtp_server = settings.EMAIL_HOST
                    smtp_port = settings.EMAIL_PORT
                    smtp_user = settings.EMAIL_HOST_USER
                    smtp_password = settings.EMAIL_HOST_PASSWORD

                    # Crear objeto del mensaje
                    msg = MIMEMultipart()
                    msg['From'] = settings.DEFAULT_FROM_EMAIL
                    msg['To'] = order.cliente_email
                    msg['Subject'] = f"Reporte de Servicio {order.folio} - ServicioTech"

                    # Cuerpo del correo
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

                    # --- C) CONEXIÓN SEGURA MANUAL (Aquí ocurre la magia) ---
                    # Creamos un contexto SSL que IGNORA TODO
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE

                    # Conectamos al servidor
                    server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
                    # server.set_debuglevel(1) # Descomenta si quieres ver el log detallado en la terminal
                    
                    # Iniciamos TLS con nuestro contexto permisivo
                    server.starttls(context=context)
                    
                    # Login y Envío
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)
                    server.quit()

                    # --- D) Éxito ---
                    order.email_enviado = True
                    order.save(update_fields=['email_enviado'])
                    messages.success(request, f"Orden enviada correctamente a {order.cliente_email}")

                except Exception as e:
                    print(f"❌ ERROR SMTP MANUAL: {e}")
                    messages.warning(request, f"Orden guardada. Error de correo: {e}")
            else:
                messages.success(request, "Orden guardada (Cliente sin correo).")
            
            # ========================================================

            return redirect(reverse("orders:detail", args=[order.pk]))
        else:
            messages.error(request, "Revisa los errores del formulario.")
    else:
        form = ServiceOrderForm()
        equipos_fs = EquipmentFormSet(prefix="equipos")
        materiales_fs = ServiceMaterialFormSet(prefix="materiales")

    ctx = {"form": form, "equipos_fs": equipos_fs, "materiales_fs": materiales_fs}
    return render(request, "orders/order_form.html", ctx)


# ===== BORRADO MASIVO =====
@require_POST
@login_required
def bulk_delete(request):
    # Acepta ambos nombres por si tu template usa "selected" o "ids"
    ids = request.POST.getlist("ids") or request.POST.getlist("selected")
    if not ids:
        messages.warning(request, "No seleccionaste órdenes para eliminar.")
        return redirect("orders:list")

    qs = ServiceOrder.objects.filter(pk__in=ids)
    deleted_orders = qs.count()   # contamos solo órdenes
    qs.delete()                   # aquí se borran también relaciones en cascada
    messages.success(request, f"Órdenes eliminadas: {deleted_orders}.")
    return redirect("orders:list")

# ===== LOGOUT =====
@require_POST
def logout_view(request):
    logout(request)
    return redirect("login")

# 2. AGREGA ESTA FUNCIÓN AL FINAL DEL ARCHIVO
@login_required
def email_order(request, pk):
    order = get_object_or_404(ServiceOrder, pk=pk)
    
    # Validar que tenga correo
    if not order.cliente_email:
        messages.error(request, "El cliente no tiene un correo registrado.")
        return redirect("orders:detail", pk=pk)

    # --- GENERACIÓN DEL PDF ---
    # Renderizamos el mismo HTML del detalle, pero le pasamos 'print_mode=True'
    html_string = render_to_string('orders/order_detail.html', {
        'object': order,
        'print_mode': True  # Variable clave para el CSS
    }, request=request)

    # Convertimos ese HTML a PDF usando WeasyPrint
    # base_url es necesario para que encuentre el logo en static
    pdf_file = weasyprint.HTML(
        string=html_string, 
        base_url=request.build_absolute_uri()
    ).write_pdf()

    # --- ARMADO DEL CORREO ---
    subject = f"Reporte de Servicio {order.folio} - ServicioTech"
    body = f"""
    Hola {order.cliente_contacto or 'Cliente'},

    Adjunto encontrarás el reporte de servicio técnico realizado el {order.fecha_servicio}.

    Folio: {order.folio}
    Título: {order.titulo}

    Atentamente,
    El equipo de ServicioTech.
    """
    
    email = EmailMessage(
        subject=subject,
        body=body,
        from_email='noreply@serviciotech.com',
        to=[order.cliente_email],
    )

    # Adjuntamos el PDF (nombre archivo, contenido, tipo mime)
    filename = f"{order.folio}.pdf"
    email.attach(filename, pdf_file, 'application/pdf')
    
    try:
        email.send()
        # Marcamos como enviado
        order.email_enviado = True
        order.save()
        messages.success(request, f"Correo enviado exitosamente a {order.cliente_email}")
    except Exception as e:
        messages.error(request, f"Error al enviar: {e}")

    return redirect("orders:detail", pk=pk)