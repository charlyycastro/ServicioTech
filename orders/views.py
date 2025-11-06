# orders/views.py
import base64
from django.core.files.base import ContentFile

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from django.shortcuts import render, redirect
from django.db.models import Q

from .models import ServiceOrder
from .forms import ServiceOrderForm, EquipmentFormSet, ServiceMaterialFormSet

@require_POST
@login_required
def logout_view(request):
    logout(request)
    return redirect("login")

@method_decorator(login_required, name="dispatch")
class OrderListView(ListView):
    model = ServiceOrder
    template_name = "orders/order_list.html"
    context_object_name = "ordenes"
    paginate_by = 10

    def get_queryset(self):
        qs = ServiceOrder.objects.all().order_by("-fecha_servicio")
        q = self.request.GET.get("q")
        cliente = self.request.GET.get("cliente")
        ingeniero = self.request.GET.get("ingeniero")
        f_desde = self.request.GET.get("desde")
        f_hasta = self.request.GET.get("hasta")

        if q:
            qs = qs.filter(
                Q(folio__icontains=q) |
                Q(titulo__icontains=q) |
                Q(cliente_nombre__icontains=q) |
                Q(ingeniero_nombre__icontains=q)
            )
        if cliente:
            qs = qs.filter(cliente_nombre__icontains=cliente)
        if ingeniero:
            qs = qs.filter(ingeniero_nombre__icontains=ingeniero)
        if f_desde:
            qs = qs.filter(fecha_servicio__gte=f_desde)
        if f_hasta:
            qs = qs.filter(fecha_servicio__lte=f_hasta)
        return qs

@login_required
def order_create(request):
    if request.method == "POST":
        form = ServiceOrderForm(request.POST, request.FILES)
        equipos_fs = EquipmentFormSet(request.POST, request.FILES, prefix="equipos")
        materiales_fs = ServiceMaterialFormSet(request.POST, request.FILES, prefix="materiales")
        if form.is_valid() and equipos_fs.is_valid() and materiales_fs.is_valid():
            order = form.save(commit=False)

            # Firma base64 → ImageField
            b64 = request.POST.get("firma")
            if b64 and b64.startswith("data:image"):
                header, data = b64.split(",", 1)  # ej. data:image/png;base64,XXXXX
                ext = "png" if "png" in header else "jpg"
                file_data = base64.b64decode(data)
                filename = f"{order.folio or 'firma'}.{ext}"
                order.firma.save(filename, ContentFile(file_data), save=False)

            order.save()

            equipos_fs.instance = order
            equipos_fs.save()

            materiales_fs.instance = order
            materiales_fs.save()

            messages.success(request, "Orden creada correctamente.")
            return redirect("orders:list")
    else:
        form = ServiceOrderForm()
        equipos_fs = EquipmentFormSet(prefix="equipos")
        materiales_fs = ServiceMaterialFormSet(prefix="materiales")

    return render(request, "orders/order_form.html", {
        "form": form,
        "equipos_fs": equipos_fs,
        "materiales_fs": materiales_fs,
    })
