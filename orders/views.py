# orders/views.py
import base64
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.db import transaction
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import ListView, DetailView
from django.template.loader import render_to_string

from .models import ServiceOrder
from .forms import ServiceOrderForm, MaterialFormSet


class OrderListView(ListView):
    model = ServiceOrder
    paginate_by = 20
    template_name = 'orders/order_list.html'

    def get_queryset(self):
        qs = ServiceOrder.objects.all().order_by('-creado')
        q = self.request.GET.get('q')
        cliente = self.request.GET.get('cliente')
        ingeniero = self.request.GET.get('ingeniero')
        fmin = self.request.GET.get('fmin')
        fmax = self.request.GET.get('fmax')
        if q:
            qs = qs.filter(titulo__icontains=q)
        if cliente:
            qs = qs.filter(cliente_nombre__icontains=cliente)
        if ingeniero:
            qs = qs.filter(ingeniero_nombre__icontains=ingeniero)
        if fmin:
            qs = qs.filter(fecha_servicio__gte=fmin)
        if fmax:
            qs = qs.filter(fecha_servicio__lte=fmax)
        return qs


class OrderDetailView(DetailView):
    model = ServiceOrder
    template_name = 'orders/order_detail.html'
    slug_field = 'folio'
    slug_url_kwarg = 'folio'


@transaction.atomic
def order_create(request):
    if request.method == 'POST':
        form = ServiceOrderForm(request.POST, request.FILES)
        formset = MaterialFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            order = form.save(commit=False)

            # Firma desde canvas (base64)
            sig_data = request.POST.get('signature_data')
            if sig_data and sig_data.startswith('data:image/png;base64,'):
                b64 = sig_data.split(',')[1]
                order.firma.save(
                    f"{order.folio}_firma.png",
                    ContentFile(base64.b64decode(b64)),
                    save=False
                )

            order.save()
            formset.instance = order
            formset.save()

            # Enviar correo al cliente (Resend vía Anymail o SMTP según settings)
            if order.cliente_email:
                html = render_to_string('orders/email_order.html', {'o': order})
                email = EmailMessage(
                    subject=f"Orden de Servicio {order.folio}",
                    body=html,
                    from_email=None,
                    to=[order.cliente_email],
                )
                email.content_subtype = 'html'
                if order.firma:
                    try:
                        email.attach_file(order.firma.path)
                    except Exception:
                        pass
                try:
                    email.send(fail_silently=True)
                    order.email_enviado = True
                    order.save(update_fields=['email_enviado'])
                except Exception:
                    pass

            return redirect(reverse('orders:detail', kwargs={'folio': order.folio}))
    else:
        form = ServiceOrderForm()
        formset = MaterialFormSet()
    return render(request, 'orders/order_form.html', {'form': form, 'formset': formset})
