from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import logout
from django.http import HttpResponse
from django.template.loader import get_template
from django.conf import settings
from django.db.models import Q
from .models import ServiceOrder
from .forms import ServiceOrderForm, EquipmentFormSet, ServiceMaterialFormSet
from django.utils.dateparse import parse_date
from django.core.paginator import Paginator
import base64, uuid
from django.core.files.base import ContentFile

# ===== LISTA (robusta a nombres de campos) =====
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
@login_required

def order_list(request):
    qs = ServiceOrder.objects.all()

    # campos reales del modelo
    field_names = {f.name for f in ServiceOrder._meta.get_fields()}

    def q_like(field: str, value: str) -> Q:
        """Q(field__icontains=value) si el campo existe; si no, Q() vacío."""
        return Q(**{f"{field}__icontains": value}) if field in field_names and value else Q()

    # elegir el campo de fecha disponible
    date_field = next((f for f in (
        "fecha_servicio", "fecha", "fecha_visita", "created_at", "date"
    ) if f in field_names), None)

    # --- parámetros (coinciden con <input name="..."> del template) ---
    q = (request.GET.get("q") or "").strip()
    cliente = (request.GET.get("cliente") or "").strip()
    ingeniero = (request.GET.get("ingeniero") or "").strip()
    desde = parse_date(request.GET.get("desde") or "")
    hasta = parse_date(request.GET.get("hasta") or "")

    # --- búsqueda general ---
    if q:
        qs = qs.filter(
            q_like("folio", q) |
            q_like("titulo", q) |
            q_like("cliente_nombre", q) | q_like("cliente", q) |
            q_like("ingeniero_nombre", q) | q_like("ingeniero", q)
        )

    # --- filtros específicos ---
    if cliente:
        qs = qs.filter(q_like("cliente_nombre", cliente) | q_like("cliente", cliente))

    if ingeniero:
        qs = qs.filter(q_like("ingeniero_nombre", ingeniero) | q_like("ingeniero", ingeniero))

    if date_field and desde:
        qs = qs.filter(**{f"{date_field}__gte": desde})
    if date_field and hasta:
        qs = qs.filter(**{f"{date_field}__lte": hasta})

    # ordenar: por fecha si existe, si no por id
    if date_field:
        qs = qs.order_by(f"-{date_field}", "-id")
    else:
        qs = qs.order_by("-id")

    # paginación
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get("page") or 1)

    context = {
        "orders": page_obj.object_list,
        "ordenes": page_obj.object_list,
        "page_obj": page_obj,
        "paginator": paginator,
        "is_paginated": page_obj.has_other_pages(),
    }
    return render(request, "orders/order_list.html", context)

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
