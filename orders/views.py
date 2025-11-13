from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import logout
from django.http import HttpResponse
from django.template.loader import get_template
from django.conf import settings

from .models import ServiceOrder
from .forms import ServiceOrderForm, EquipmentFormSet, ServiceMaterialFormSet

import base64, uuid
from django.core.files.base import ContentFile

# ===== LISTA =====
@login_required
def order_list(request):
    qs = ServiceOrder.objects.all().order_by('-id')
    return render(request, "orders/order_list.html", {"orders": qs, "ordenes": qs})

# ===== DIAGNÓSTICO =====
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
            firma_b64 = request.POST.get("firma") or ""
            if firma_b64.startswith("data:image"):
                try:
                    header, data = firma_b64.split(",", 1)
                    ext = "png" if "png" in header.lower() else "jpg"
                    file_data = ContentFile(base64.b64decode(data), name=f"firma_{uuid.uuid4().hex}.{ext}")
                    order.firma = file_data
                except Exception:
                    messages.warning(request, "No se pudo procesar la firma. Puedes intentar firmar de nuevo.")
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
    return render(request, "orders/order_form.html", {
        "form": form, "equipos_fs": equipos_fs, "materiales_fs": materiales_fs
    })

# ===== BORRADO MASIVO =====
@require_POST
@login_required
def bulk_delete(request):
    ids = request.POST.getlist("ids")
    if not ids:
        messages.warning(request, "No seleccionaste órdenes para eliminar.")
        return redirect("orders:list")
    ServiceOrder.objects.filter(pk__in=ids).delete()
    messages.success(request, "Órdenes seleccionadas eliminadas.")
    return redirect("orders:list")

# ===== LOGOUT =====
@require_POST
def logout_view(request):
    logout(request)
    return redirect("login")
