from django.db import models
from django.utils import timezone
import uuid

SERVICE_TYPES = [
    ("instalacion", "Instalación"),
    ("configuracion", "Configuración"),
    ("mantenimiento", "Mantenimiento"),
    ("garantia", "Garantía"),
    ("revision", "Falla/Revisión"),
    ("capacitacion", "Capacitación"),
]


# En orders/models.py

# En orders/models.py

class ServiceOrder(models.Model):
    folio = models.CharField(max_length=32, unique=True, editable=False, blank=True)
    
    # ... tus otros campos ...

    def save(self, *args, **kwargs):
        if not self.folio:
            # 1. Base: OS-YYYYMMDD
            today = timezone.now().strftime("%Y%m%d")
            prefix = f"OS-{today}"
            
            # 2. Inicial del ingeniero (C, A, etc.)
            if self.ingeniero_nombre:
                initial = self.ingeniero_nombre[0].upper()
            else:
                initial = "X"

            # 3. Buscar la última orden DE HOY (sin importar la letra del ingeniero)
            last_order = ServiceOrder.objects.filter(folio__startswith=prefix).order_by("-creado").first()

            if last_order:
                try:
                    # El folio anterior es tipo: OS-20251120-A005
                    last_suffix = last_order.folio.split("-")[-1] # Toma "A005"
                    
                    # Quitamos la letra (primer caracter) y convertimos el resto a número
                    last_num = int(last_suffix[1:]) 
                    new_num = last_num + 1
                except (IndexError, ValueError):
                    # Por si hay basura en la BD
                    new_num = 1
            else:
                # Primera orden del día
                new_num = 1

            # 4. Construir folio: OS-20251120-C001
            # {initial} pone la letra (C)
            # {new_num:03d} pone el número con 3 dígitos (001, 010, 100)
            self.folio = f"{prefix}-{initial}{new_num:03d}"

        super().save(*args, **kwargs)


    # 1) Información general
    # Cliente (empresa)
    cliente_nombre = models.CharField(max_length=200)

    # Nuevo: persona de contacto del cliente
    cliente_contacto = models.CharField(
        max_length=200,
        blank=True,
        help_text="Nombre de la persona de contacto del cliente.",
    )

    # Correo del cliente
    cliente_email = models.EmailField(blank=True)

    # Nuevo: teléfono del cliente
    cliente_telefono = models.CharField(
        max_length=50,
        blank=True,
        help_text="Número de teléfono del cliente.",
    )

    ubicacion = models.CharField(max_length=300, blank=True)
    fecha_servicio = models.DateField(default=timezone.now)

    # Ahora será “Contacto interno”
    contacto_nombre = models.CharField(max_length=200, blank=True)

    # Campo antiguo (compatibilidad). Ya no se usa en el form, lo dejamos opcional:
    tipo_servicio = models.CharField(max_length=20, choices=SERVICE_TYPES, blank=True)

    # Nuevos campos
    tipos_servicio = models.JSONField(default=list, blank=True)   # p.ej. ["instalacion","mantenimiento"]
    tipo_servicio_otro = models.CharField(max_length=200, blank=True)

    ingeniero_nombre = models.CharField(max_length=200)

    ticket_id = models.CharField("ID Ticket", max_length=50, blank=True)

    # 2) Equipo (resumen opcional)
    equipo_marca = models.CharField(max_length=100, blank=True)
    equipo_modelo = models.CharField(max_length=100, blank=True)
    equipo_serie = models.CharField(max_length=100, blank=True)
    equipo_descripcion = models.TextField(blank=True)

    # 3) Datos técnicos
    titulo = models.CharField(max_length=250)
    actividades = models.TextField(blank=True)
    comentarios = models.TextField(blank=True)

    # Resguardo: lo mantenemos para compatibilidad, pero NO se muestra en el form
    resguardo = models.CharField(max_length=200, blank=True)

    horas = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    costo_mxn = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    costo_no_aplica = models.BooleanField(default=False)
    costo_se_cotizara = models.BooleanField(default=False)

    reagenda = models.BooleanField(default=False)
    reagenda_fecha = models.DateField(null=True, blank=True)
    reagenda_hora = models.TimeField(null=True, blank=True)
    reagenda_motivo = models.TextField(blank=True)

    firma = models.ImageField(upload_to="signatures/", null=True, blank=True)

    # Nuevo: indicaciones internas (no se imprimen)
    indicaciones_especiales = models.TextField(
        blank=True,
        help_text="Indicaciones internas (EPP, credencial, pruebas, etc.). No se imprime.",
    )

    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    email_enviado = models.BooleanField(default=False)

    # Helpers
    def tipos_servicio_labels(self):
        mapa = dict(SERVICE_TYPES)
        return [mapa.get(code, code) for code in (self.tipos_servicio or [])]

    def __str__(self):
        return f"{self.folio} - {self.cliente_nombre}"


class Equipment(models.Model):
    order = models.ForeignKey("ServiceOrder", related_name="equipos", on_delete=models.CASCADE)
    marca = models.CharField("Marca", max_length=100, blank=True)
    modelo = models.CharField("Modelo", max_length=100, blank=True)
    serie = models.CharField("Serie", max_length=100, blank=True)
    descripcion = models.TextField("Descripción", blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Equipo"
        verbose_name_plural = "Equipos"
        ordering = ["id"]

    def __str__(self):
        base = f"{self.marca or ''} {self.modelo or ''}".strip()
        if self.serie:
            base += f" ({self.serie})"
        return base or "Equipo"


class ServiceMaterial(models.Model):
    order = models.ForeignKey(ServiceOrder, on_delete=models.CASCADE, related_name="materiales")
    cantidad = models.PositiveIntegerField(default=1)
    descripcion = models.CharField(max_length=200)
    comentarios = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.cantidad}x {self.descripcion} ({self.order.folio})"

#Firma del ingeniero
from django.contrib.auth.models import User

class EngineerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    firma = models.ImageField(upload_to="engineer_signatures/", null=True, blank=True)

    def __str__(self):
        return f"Perfil de {self.user.username}"