from decimal import Decimal
from datetime import timedelta
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class Cliente(models.Model):
    nombre = models.CharField(max_length=150, verbose_name="Nombre Completo")
    telefono = models.CharField(
        max_length=30,
        unique=True,
        verbose_name="Teléfono (WhatsApp)",
        help_text="Formato internacional recomendado: +584121234567"
    )
    notas = models.TextField(blank=True, default="", verbose_name="Notas adicionales")
    creado_el = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.telefono})"


class CuentaMaestra(models.Model):
    PLATAFORMAS = [
        ("Netflix", "Netflix"),
        ("Crunchyroll", "Crunchyroll"),
    ]

    plataforma = models.CharField(max_length=20, choices=PLATAFORMAS, verbose_name="Plataforma")
    correo = models.EmailField(unique=True, verbose_name="Correo Electrónico")
    fecha_facturacion = models.DateField(
        verbose_name="Fecha de Facturación",
        help_text="Día del mes en que la plataforma renueva el cobro de la cuenta maestra"
    )
    max_perfiles = models.PositiveIntegerField(
        default=5,
        verbose_name="Límite Máximo de Perfiles",
        help_text="Capacidad de perfiles comercializables (ej. Netflix: 5, Crunchyroll: 4)"
    )
    activa = models.BooleanField(default=True, verbose_name="Cuenta Activa")
    creado_el = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")

    class Meta:
        verbose_name = "Cuenta Maestra"
        verbose_name_plural = "Cuentas Maestras"
        ordering = ["plataforma", "correo"]

    @property
    def perfiles_ocupados(self):
        return self.suscripciones.filter(activa=True).count()

    @property
    def perfiles_disponibles(self):
        return max(0, self.max_perfiles - self.perfiles_ocupados)

    def __str__(self):
        return f"{self.plataforma} - {self.correo} ({self.perfiles_ocupados}/{self.max_perfiles})"


class Suscripcion(models.Model):
    ESTADOS = [
        ("Al día", "Al día"),
        ("Por vencer", "Por vencer"),
        ("Vencido", "Vencido"),
    ]

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name="suscripciones",
        verbose_name="Cliente"
    )
    cuenta_maestra = models.ForeignKey(
        CuentaMaestra,
        on_delete=models.CASCADE,
        related_name="suscripciones",
        verbose_name="Cuenta Maestra"
    )
    perfil_pin = models.CharField(
        max_length=100,
        verbose_name="Perfil / PIN",
        help_text="Identificador de pantalla y clave de perfil (ej. Perfil 2 - PIN 1234)"
    )
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Precio Mensual ($)"
    )
    fecha_inicio = models.DateField(default=timezone.now, verbose_name="Fecha de Inicio")
    fecha_vencimiento = models.DateField(verbose_name="Fecha de Vencimiento / Corte")
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="Al día",
        verbose_name="Estado de Suscripción"
    )
    activa = models.BooleanField(default=True, verbose_name="Suscripción Activa")
    creado_el = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Asignación")

    class Meta:
        verbose_name = "Suscripción"
        verbose_name_plural = "Suscripciones"
        ordering = ["fecha_vencimiento"]

    def clean(self):
        super().clean()
        if self.precio is not None and self.precio < 0:
            raise ValidationError({"precio": "El precio mensual no puede ser negativo."})

        # Validación de cupo máximo de perfiles por cuenta maestra
        if self.cuenta_maestra_id and self.activa:
            ocupados = self.cuenta_maestra.suscripciones.filter(activa=True)
            if self.pk:
                ocupados = ocupados.exclude(pk=self.pk)
            if ocupados.count() >= self.cuenta_maestra.max_perfiles:
                raise ValidationError({
                    "cuenta_maestra": f"La cuenta maestra {self.cuenta_maestra.correo} ha alcanzado su límite máximo de {self.cuenta_maestra.max_perfiles} perfiles."
                })

    def calcular_estado(self):
        hoy = timezone.now().date()
        if self.fecha_vencimiento < hoy:
            return "Vencido"
        elif self.fecha_vencimiento <= hoy + timedelta(days=3):
            return "Por vencer"
        else:
            return "Al día"

    def actualizar_estado(self):
        nuevo_estado = self.calcular_estado()
        if self.estado != nuevo_estado:
            self.estado = nuevo_estado
            self.save(update_fields=["estado"])
        return self.estado

    def renovar_30_dias(self):
        hoy = timezone.now().date()
        base = max(self.fecha_vencimiento, hoy)
        self.fecha_vencimiento = base + timedelta(days=30)
        self.estado = "Al día"
        self.save(update_fields=["fecha_vencimiento", "estado"])

    def save(self, *args, **kwargs):
        if not kwargs.pop("skip_clean", False):
            self.full_clean()
        if not self.estado:
            self.estado = self.calcular_estado()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cliente.nombre} - {self.cuenta_maestra.plataforma} ({self.perfil_pin})"


class MetodoPago(models.Model):
    nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre del Método",
        help_text="Ej: Pago Móvil Banesco, Binance USDT, Zelle"
    )
    datos_pago = models.TextField(
        verbose_name="Datos para Pago",
        help_text="Datos bancarios o de billetera que verá el cliente para transferir"
    )
    activo = models.BooleanField(default=True, verbose_name="Método Activo")
    creado_el = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")

    class Meta:
        verbose_name = "Método de Pago"
        verbose_name_plural = "Métodos de Pago"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Pago(models.Model):
    ORIGENES = [
        ("Cliente", "Cliente"),
        ("Admin", "Admin"),
    ]
    ESTADOS = [
        ("Pendiente", "Pendiente"),
        ("Aprobado", "Aprobado"),
        ("Rechazado", "Rechazado"),
    ]

    suscripcion = models.ForeignKey(
        Suscripcion,
        on_delete=models.CASCADE,
        related_name="pagos",
        verbose_name="Suscripción Asociada"
    )
    metodo_pago = models.ForeignKey(
        MetodoPago,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pagos",
        verbose_name="Método de Pago"
    )
    monto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto Pagado ($)")
    fecha_pago = models.DateField(default=timezone.now, verbose_name="Fecha del Pago")
    referencia = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="Número de Referencia",
        help_text="Código o referencia bancaria del comprobante"
    )
    origen = models.CharField(
        max_length=20,
        choices=ORIGENES,
        default="Cliente",
        verbose_name="Origen del Registro"
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="Pendiente",
        verbose_name="Estado de Verificación"
    )
    comprobante_imagen = models.ImageField(
        upload_to="comprobantes/",
        blank=True,
        null=True,
        verbose_name="Comprobante Adjunto"
    )
    notas = models.TextField(blank=True, default="", verbose_name="Notas de Verificación")
    creado_el = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")

    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ["-creado_el"]

    def clean(self):
        super().clean()
        if self.monto is None or self.monto <= Decimal("0.00"):
            raise ValidationError({"monto": "El monto del pago debe ser mayor a 0."})

        ref = (self.referencia or "").strip()
        if self.origen == "Cliente" and not ref:
            raise ValidationError({"referencia": "La referencia es obligatoria para reportes enviados por clientes."})

        # Validación de unicidad de referencia (cuando no es vacía)
        if ref:
            existente = Pago.objects.filter(referencia=ref)
            if self.pk:
                existente = existente.exclude(pk=self.pk)
            if existente.exists():
                raise ValidationError({"referencia": f"Ya existe un pago registrado con la referencia '{ref}'."})

    def save(self, *args, **kwargs):
        if not kwargs.pop("skip_clean", False):
            self.full_clean()
        super().save(*args, **kwargs)

    def aprobar(self):
        self.estado = "Aprobado"
        self.save(update_fields=["estado"], skip_clean=True)
        self.suscripcion.renovar_30_dias()

    def rechazar(self):
        self.estado = "Rechazado"
        self.save(update_fields=["estado"], skip_clean=True)

    def __str__(self):
        ref_text = self.referencia if self.referencia else "Manual"
        return f"Pago {ref_text} - {self.suscripcion.cliente.nombre} (${self.monto}) [{self.estado}]"
