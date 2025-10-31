from django.db import models
from django.utils import timezone
import uuid


SERVICE_TYPES = [
("instalacion","Instalación"),("configuracion","Configuración"),
("mantenimiento","Mantenimiento"),("garantia","Garantía"),
("revision","Falla/Revisión"),("capacitacion","Capacitación"),
]


class ServiceOrder(models.Model):
def folio_default():
today = timezone.now().strftime('%Y%m%d')
short = uuid.uuid4().hex[:6].upper()
return f"SRV-{today}-{short}"


folio = models.CharField(max_length=32, unique=True, default=folio_default, editable=False)


# 1. Información general
cliente_nombre = models.CharField(max_length=200)
cliente_email = models.EmailField(blank=True)
ubicacion = models.CharField(max_length=300, blank=True)
fecha_servicio = models.DateField(default=timezone.now)
contacto_nombre = models.CharField(max_length=200, blank=True)
tipo_servicio = models.CharField(max_length=20, choices=SERVICE_TYPES)
ingeniero_nombre = models.CharField(max_length=200)


# 7. Equipo
equipo_marca = models.CharField(max_length=100, blank=True)
equipo_modelo = models.CharField(max_length=100, blank=True)
equipo_serie = models.CharField(max_length=100, blank=True)
equipo_descripcion = models.TextField(blank=True)


# 2. Datos técnicos
titulo = models.CharField(max_length=250)
actividades = models.TextField(blank=True)
comentarios = models.TextField(blank=True)


resguardo = models.CharField(max_length=200, blank=True, help_text="Ej. Ninguno / Adaptador / etc.")


horas = models.DecimalField(max_digits=5, decimal_places=2, default=0)
costo_mxn = models.DecimalField(max_digits=10, decimal_places=2, default=0)
costo_no_aplica = models.BooleanField(default=False)
costo_se_cotizara = models.BooleanField(default=False)


reagenda = models.BooleanField(default=False)
reagenda_fecha = models.DateField(null=True, blank=True)
reagenda_hora = models.TimeField(null=True, blank=True)
reagenda_motivo = models.TextField(blank=True)


firma = models.ImageField(upload_to='signatures/', null=True, blank=True)


creado = models.DateTimeField(auto_now_add=True)
actualizado = models.DateTimeField(auto_now=True)


email_enviado = models.BooleanField(default=False)


def __str__(self):
return f"{self.folio} - {self.cliente_nombre}"


class ServiceMaterial(models.Model):
order = models.ForeignKey(ServiceOrder, on_delete=models.CASCADE, related_name='materiales')
cantidad = models.PositiveIntegerField(default=1)
descripcion = models.CharField(max_length=200)
comentarios = models.CharField(max_length=200, blank=True)


def __str__(self):
return f"{self.cantidad}x {self.descripcion} ({self.order.folio})"