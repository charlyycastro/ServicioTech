from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import logout
from django.http import HttpResponse
from django.template.loader import get_template
from django.db.models import Q
from django.conf import settings
from django.core.paginator import Paginator

from .models import ServiceOrder
from .forms import ServiceOrderForm, EquipmentFormSet, ServiceMaterialFormSet

# para firma base64 -> ImageField
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
            order = form.save(commit=False)

            # --- Firma en base64 (renombramos a 'firma_b64' para evitar colisiones) ---
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
                    messages.warning(request, "No pude procesar la firma. Intenta firmar de nuevo.")
            else:
                # No bloquear el guardado; solo avisar en DEBUG
                messages.warning(request, "No recibí la firma (input hidden vacío o formato no reconocido).")

            order.save()

            equipos_fs.instance = order
            materiales_fs.instance = order
            equipos_fs.save()
            materiales_fs.save()

            messages.success(request, "Orden creada correctamente.")
            return redirect(reverse("orders:detail", args=[order.pk]))
        else:
            messages.error(request, "Revisa los errores del formulario marcado en rojo.")
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
