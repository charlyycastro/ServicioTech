from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import uuid
# Librerías para compresión de imágenes
from PIL import Image
from io import BytesIO
import os
from django.core.files.base import ContentFile

SERVICE_TYPES = [
    ("instalacion", "Instalación"),
    ("configuracion", "Configuración"),
    ("mantenimiento", "Mantenimiento"),
    ("garantia", "Garantía"),
    ("revision", "Falla/Revisión"),
    ("capacitacion", "Capacitación"),
]

# --- PERFIL DE USUARIO (Para firma de Ingenieros y Visores) ---
class EngineerProfile(models.Model):
    # CORRECCIÓN: Usamos CASCADE. Si se borra el usuario, se borra el perfil.
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    firma = models.ImageField(upload_to="engineer_signatures/", null=True, blank=True)

    def __str__(self):
        return f"Perfil de {self.user.username}"


class ServiceOrder(models.Model):
    STATUS_CHOICES = [
        ('borrador', 'En Pausa (Borrador)'),
        ('finalizado', 'Finalizado'),
    ]

    folio = models.CharField(max_length=32, unique=True, editable=False, blank=True)
    
    # 1) Información general
    cliente_nombre = models.CharField(max_length=200) 
    
    cliente_contacto = models.CharField(max_length=200, blank=True, null=True)
    cliente_email = models.EmailField(blank=True, null=True)
    cliente_telefono = models.CharField(max_length=50, blank=True, null=True)
    ubicacion = models.CharField(max_length=300, blank=True, null=True)
    fecha_servicio = models.DateField(default=timezone.now, blank=True, null=True)
    
    # Campo de texto antiguo
    contacto_nombre = models.CharField("Contacto Interno (Texto)", max_length=200, blank=True, null=True)

    # --- VISOR / CONTACTO VENTAS ---
    # Aquí usamos SET_NULL para que si borras al vendedor, la orden NO se rompa, 
    # solo se pone el campo en blanco.
    visor = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="ordenes_visor",
        verbose_name="Contacto Ventas (Visor)"
    )
    # --------------------------------------------

    tipos_servicio = models.JSONField(default=list, blank=True, null=True)
    tipo_servicio_otro = models.CharField(max_length=200, blank=True, null=True)

    # Ingeniero (Nombre texto)
    ingeniero_nombre = models.CharField(max_length=200, blank=True, null=True)

    ticket_id = models.CharField("ID Ticket", max_length=50, blank=True, null=True)

    # 2) Datos técnicos
    titulo = models.CharField(max_length=250, blank=True, null=True)
    actividades = models.TextField(blank=True)
    comentarios = models.TextField(blank=True)

    # D) Costos y programación
    horas = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    costo_mxn = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    costo_no_aplica = models.BooleanField(default=False)
    costo_se_cotizara = models.BooleanField(default=False)

    reagenda = models.BooleanField(default=False)
    reagenda_fecha = models.DateField(null=True, blank=True)
    reagenda_hora = models.TimeField(null=True, blank=True)
    reagenda_motivo = models.TextField(blank=True)

    # Firmas y Estado
    firma = models.ImageField(upload_to="signatures/", null=True, blank=True)
    indicaciones_especiales = models.TextField(blank=True, help_text="Indicaciones internas. No se imprime.")
    
    estatus = models.CharField(max_length=20, choices=STATUS_CHOICES, default='borrador')

    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    email_enviado = models.BooleanField(default=False)

    # Métodos auxiliares
    def save(self, *args, **kwargs):
        if not self.folio:
            today = timezone.now().strftime("%Y%m%d")
            prefix = f"OS-{today}"
            initial = self.ingeniero_nombre[0].upper() if self.ingeniero_nombre else "X"
            
            last_order = ServiceOrder.objects.filter(folio__startswith=prefix).order_by("-creado").first()
            if last_order:
                try:
                    last_suffix = last_order.folio.split("-")[-1]
                    last_num = int(last_suffix[1:]) 
                    new_num = last_num + 1
                except (IndexError, ValueError):
                    new_num = 1
            else:
                new_num = 1
            self.folio = f"{prefix}-{initial}{new_num:03d}"
        super().save(*args, **kwargs)

    @property
    def tipos_servicio_labels(self):
        mapa = dict(SERVICE_TYPES)
        return [mapa.get(code, code) for code in (self.tipos_servicio or [])]

    def __str__(self):
        return f"{self.folio} - {self.cliente_nombre}"


# --- TABLAS RELACIONADAS ---

class Equipment(models.Model): 
    order = models.ForeignKey("ServiceOrder", related_name="equipos", on_delete=models.CASCADE)
    marca = models.CharField("Marca", max_length=100, blank=True)
    modelo = models.CharField("Modelo", max_length=100, blank=True)
    serie = models.CharField("Serie", max_length=100, blank=True)
    descripcion = models.TextField("Descripción", blank=True)

class ServiceMaterial(models.Model): 
    order = models.ForeignKey(ServiceOrder, on_delete=models.CASCADE, related_name="materiales")
    cantidad = models.PositiveIntegerField(default=1)
    descripcion = models.CharField(max_length=200)
    comentarios = models.CharField(max_length=200, blank=True)

class ShelterEquipment(models.Model):
    order = models.ForeignKey(ServiceOrder, on_delete=models.CASCADE, related_name="resguardos")
    cantidad = models.PositiveIntegerField(default=1, null=True, blank=True)
    descripcion = models.CharField(max_length=200, blank=True)
    comentarios = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Resguardo: {self.descripcion}"

class ServiceEvidence(models.Model):
    order = models.ForeignKey(ServiceOrder, on_delete=models.CASCADE, related_name="evidencias")
    archivo = models.FileField(upload_to="evidencias/%Y/%m/")
    comentario = models.CharField(max_length=255, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.archivo and not self.pk:
            try:
                img = Image.open(self.archivo)
                if img.height > 1080 or img.width > 1920:
                    output_size = (1920, 1080)
                    img.thumbnail(output_size)
                
                buffer = BytesIO()
                if img.mode in ("RGBA", "P"): 
                    img = img.convert("RGB")
                
                img.save(buffer, format='JPEG', quality=70, optimize=True)
                buffer.seek(0)
                
                nombre_archivo = os.path.splitext(self.archivo.name)[0] + ".jpg"
                self.archivo = ContentFile(buffer.read(), name=nombre_archivo)
            except Exception as e:
                print(f"No se pudo comprimir imagen (posiblemente es PDF/Video): {e}")

        super().save(*args, **kwargs)


# orders/models.py

class TechnicalMemory(models.Model):
    # Relación con las órdenes seleccionadas
    orders = models.ManyToManyField(ServiceOrder, related_name="memories")
    cliente_nombre = models.CharField(max_length=255)
    
    # v1: Generada por IA (Original)
    contenido_v1_ia = models.TextField()
    
    # v2: Editada por el usuario (Versión Activa)
    contenido_v2_user = models.TextField(blank=True, null=True)
    
    creado_por = models.ForeignKey(User, on_delete=models.CASCADE)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Memoria {self.cliente_nombre} - {self.creado.date()}"