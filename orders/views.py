from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import logout
from django.db.models import Q,F
from django.utils.dateparse import parse_date
from django.core.paginator import Paginator
from django.utils.dateparse import parse_date
from .models import ServiceOrder
from .forms import ServiceOrderForm, EquipmentFormSet, ServiceMaterialFormSet
from django.shortcuts import render

# para firma base64 -> ImageField
import base64, uuid
from django.core.files.base import ContentFile


@login_required
def order_list(request):
    qs = ServiceOrder.objects.all().order_by('-id')  # nuevas arriba

    # DEBUG en consola: confirma cuántos trae y qué DB está usando
    print("ORDER_LIST count:", qs.count())
    print("DB:", settings.DATABASES['default'])

    ctx = {
        "orders": qs,          # <- ÚNICO nombre que usará la plantilla
        "page_obj": None,
        "paginator": None,
        "is_paginated": False,
    }
    return render(request, "orders/order_list.html", ctx)


@login_required
def order_detail(request, pk):
    obj = get_object_or_404(ServiceOrder, pk=pk)
    return render(request, "orders/order_detail.html", {"object": obj})


@login_required
def order_create(request):
    if request.method == "POST":
        form = ServiceOrderForm(request.POST, request.FILES)
        equipos_fs = EquipmentFormSet(request.POST, request.FILES, prefix="equipos")
        materiales_fs = ServiceMaterialFormSet(request.POST, request.FILES, prefix="materiales")

        if form.is_valid() and equipos_fs.is_valid() and materiales_fs.is_valid():
            # Guardar orden (y meter firma si viene en base64)
            order = form.save(commit=False)

            # El input hidden en el template se llama name="firma" (id="firma-base64")
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

            # Formsets
            equipos_fs.instance = order
            materiales_fs.instance = order
            equipos_fs.save()
            materiales_fs.save()

            messages.success(request, "Orden creada correctamente.")
            return redirect(reverse("orders:detail", args=[order.pk]))
        else:
            # Mostrar errores en pantalla
            messages.error(request, "Revisa los errores del formulario marcado en rojo.")
    else:
        form = ServiceOrderForm()
        equipos_fs = EquipmentFormSet(prefix="equipos")
        materiales_fs = ServiceMaterialFormSet(prefix="materiales")

    ctx = {"form": form, "equipos_fs": equipos_fs, "materiales_fs": materiales_fs}
    return render(request, "orders/order_form.html", ctx)


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


@require_POST
def logout_view(request):
    logout(request)
    return redirect("login")
