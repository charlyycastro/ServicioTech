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

from .models import ServiceOrder
from .forms import ServiceOrderForm, EquipmentFormSet, ServiceMaterialFormSet

# para firma base64 -> ImageField
import base64, uuid
from django.core.files.base import ContentFile
from django.utils.dateparse import parse_date


# ===== LISTA =====
@login_required
def order_list(request):
    qs = ServiceOrder.objects.all()

    # Parámetros de filtro (coinciden con los <input name="..."> del template)
    q = (request.GET.get("q") or "").strip()
    cliente = (request.GET.get("cliente") or "").strip()
    ingeniero = (request.GET.get("ingeniero") or "").strip()
    desde = parse_date(request.GET.get("desde") or "")
    hasta = parse_date(request.GET.get("hasta") or "")

    # Búsqueda general
    if q:
        qs = qs.filter(
            Q(folio__icontains=q) |
            Q(titulo__icontains=q) |
            Q(cliente_nombre__icontains=q) |
            Q(ingeniero_nombre__icontains=q)
        )

    # Filtros específicos
    if cliente:
        qs = qs.filter(cliente_nombre__icontains=cliente)
    if ingeniero:
        qs = qs.filter(ingeniero_nombre__icontains=ingeniero)
    if desde:
        qs = qs.filter(fecha_servicio__gte=desde)
    if hasta:
        qs = qs.filter(fecha_servicio__lte=hasta)

    # Orden: más recientes primero
    qs = qs.order_by("-fecha_servicio", "-id")

    context = {
        "orders": qs,
        "ordenes": qs,  # alias por si tu template usa 'ordenes'
    }
    return render(request, "orders/order_list.html", context)


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

            # --- Firma en base64 desde el input hidden ---
            firma_b64 = request.POST.get("firma") or ""
            try:
                if firma_b64.startswith("data:image"):
                    # DEBUG visible en consola del servidor
                    print("DEBUG firma_b64 head:", firma_b64[:30], "len=", len(firma_b64))

                    header, data = firma_b64.split(",", 1)
                    ext = "png"
                    if "jpeg" in header.lower() or "jpg" in header.lower():
                        ext = "jpg"

                    file_data = ContentFile(base64.b64decode(data), name=f"firma_{uuid.uuid4().hex}.{ext}")
                    order.firma = file_data
                else:
                    # Aviso útil si llega vacío o sin prefijo
                    from django.contrib import messages
                    msg = "No recibí la firma (input hidden vacío o formato no reconocido)."
                    print("DEBUG:", msg, "valor:", firma_b64[:30])
                    messages.warning(request, msg)
            except Exception as e:
                from django.contrib import messages
                print("ERROR decodificando firma:", e)
                messages.error(request, "No se pudo procesar la firma. Intente firmar de nuevo.")

            order.save()

            # Guardar formsets
            equipos_fs.instance = order
            materiales_fs.instance = order
            equipos_fs.save()
            materiales_fs.save()

            messages.success(request, "Orden creada correctamente.")
            return redirect(reverse("orders:detail", args=[order.pk]))
        else:
            from django.contrib import messages
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
    ids = (
        request.POST.getlist("ids")
        or request.POST.getlist("selected")
        or request.POST.getlist("order_ids")
    )
    if not ids:
        messages.warning(request, "No seleccionaste órdenes para eliminar.")
        return redirect("orders:list")

    # Asegura enteros
    ids = [int(x) for x in ids if str(x).isdigit()]
    deleted, _ = ServiceOrder.objects.filter(pk__in=ids).delete()
    messages.success(request, f"Órdenes eliminadas: {deleted}.")
    return redirect("orders:list")

# ===== LOGOUT =====
@require_POST
def logout_view(request):
    logout(request)
    return redirect("login")
