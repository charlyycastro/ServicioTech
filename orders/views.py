from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import logout
from django.db.models import Q
from django.utils.dateparse import parse_date

from .models import ServiceOrder
from .forms import ServiceOrderForm, EquipmentFormSet, ServiceMaterialFormSet


@login_required
def order_list(request):
    qs = ServiceOrder.objects.all()

    # Filtros opcionales que usa tu template (q, desde, hasta)
    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(
            Q(folio__icontains=q)
            | Q(cliente_nombre__icontains=q)
            | Q(titulo__icontains=q)
            | Q(ingeniero_nombre__icontains=q)
        )

    desde = parse_date(request.GET.get("desde") or "")
    hasta = parse_date(request.GET.get("hasta") or "")
    if desde:
        qs = qs.filter(fecha_servicio__gte=desde)
    if hasta:
        qs = qs.filter(fecha_servicio__lte=hasta)

    qs = qs.order_by("-fecha_servicio", "-id")
    return render(request, "orders/order_list.html", {"orders": qs})


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
            order = form.save()
            equipos_fs.instance = order
            materiales_fs.instance = order
            equipos_fs.save()
            materiales_fs.save()
            messages.success(request, "Orden creada correctamente.")
            return redirect(reverse("orders:detail", args=[order.pk]))
    else:
        form = ServiceOrderForm()
        equipos_fs = EquipmentFormSet(prefix="equipos")
        materiales_fs = ServiceMaterialFormSet(prefix="materiales")

    ctx = {"form": form, "equipos_fs": equipos_fs, "materiales_fs": materiales_fs}
    return render(request, "orders/order_form.html", ctx)


@require_POST
@login_required
def bulk_delete(request):
    """
    Recibe una lista de IDs (checkbox name='ids') y elimina en bloque.
    Tu template hace POST a {% url 'orders:bulk_delete' %}.
    """
    ids = request.POST.getlist("ids")  # p.ej. ["3","5","8"]
    if not ids:
        messages.warning(request, "No seleccionaste órdenes para eliminar.")
        return redirect("orders:list")

    deleted, _ = ServiceOrder.objects.filter(pk__in=ids).delete()
    # 'deleted' puede incluir objetos relacionados; solo mostramos un mensaje general
    messages.success(request, "Órdenes seleccionadas eliminadas.")
    return redirect("orders:list")


@require_POST
def logout_view(request):
    logout(request)
    return redirect("login")
