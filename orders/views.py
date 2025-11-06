# orders/views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from django.shortcuts import render, redirect
from django.db.models import Q

from .models import Order
from .forms import OrderForm, EquipoFormSet, MaterialFormSet

@require_POST
@login_required
def logout_view(request):
    logout(request)
    return redirect("login")

@method_decorator(login_required, name="dispatch")
class OrderListView(ListView):
    model = Order
    template_name = "orders/order_list.html"
    context_object_name = "ordenes"
    paginate_by = 10

    def get_queryset(self):
        qs = Order.objects.all().order_by("-fecha")
        q = self.request.GET.get("q")
        cliente = self.request.GET.get("cliente")
        ingeniero = self.request.GET.get("ingeniero")
        f_desde = self.request.GET.get("desde")
        f_hasta = self.request.GET.get("hasta")

        if q:
            qs = qs.filter(
                Q(folio__icontains=q) |
                Q(titulo__icontains=q) |
                Q(cliente__icontains=q) |
                Q(ingeniero__icontains=q)
            )
        if cliente:
            qs = qs.filter(cliente__icontains=cliente)
        if ingeniero:
            qs = qs.filter(ingeniero__icontains=ingeniero)
        if f_desde:
            qs = qs.filter(fecha__gte=f_desde)
        if f_hasta:
            qs = qs.filter(fecha__lte=f_hasta)
        return qs

@login_required
def order_create(request):
    if request.method == "POST":
        form = OrderForm(request.POST, request.FILES)
        equipos_fs = EquipoFormSet(request.POST, request.FILES, prefix="equipos")
        materiales_fs = MaterialFormSet(request.POST, request.FILES, prefix="materiales")
        if form.is_valid() and equipos_fs.is_valid() and materiales_fs.is_valid():
            order = form.save()
            equipos_fs.instance = order
            equipos_fs.save()
            materiales_fs.instance = order
            materiales_fs.save()
            messages.success(request, "Orden creada correctamente.")
            return redirect("orders:list")
    else:
        form = OrderForm()
        equipos_fs = EquipoFormSet(prefix="equipos")
        materiales_fs = MaterialFormSet(prefix="materiales")

    return render(request, "orders/order_form.html", {
        "form": form,
        "equipos_fs": equipos_fs,
        "materiales_fs": materiales_fs,
    })
