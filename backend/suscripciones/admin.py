from django.contrib import admin
from django.utils.html import format_html
from .models import Cliente, CuentaMaestra, Suscripcion, MetodoPago, Pago


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "telefono", "suscripciones_activas_count", "creado_el")
    search_fields = ("nombre", "telefono")
    list_per_page = 25

    def suscripciones_activas_count(self, obj):
        return obj.suscripciones.filter(activa=True).count()
    suscripciones_activas_count.short_description = "Suscripciones Activas"


@admin.register(CuentaMaestra)
class CuentaMaestraAdmin(admin.ModelAdmin):
    list_display = ("plataforma", "correo", "cupos_display", "fecha_facturacion", "activa")
    list_filter = ("plataforma", "activa")
    search_fields = ("correo",)
    list_per_page = 25

    def cupos_display(self, obj):
        ocupados = obj.perfiles_ocupados
        total = obj.max_perfiles
        color = "green" if ocupados < total else "red"
        return format_html(
            '<span style="font-weight: bold; color: {};">{}/{} perfiles</span>',
            color, ocupados, total
        )
    cupos_display.short_description = "Ocupación"


@admin.register(Suscripcion)
class SuscripcionAdmin(admin.ModelAdmin):
    list_display = ("cliente", "plataforma_display", "perfil_pin", "precio", "fecha_vencimiento", "estado_badge", "activa")
    list_filter = ("estado", "activa", "cuenta_maestra__plataforma")
    search_fields = ("cliente__nombre", "cliente__telefono", "perfil_pin", "cuenta_maestra__correo")
    date_hierarchy = "fecha_vencimiento"
    list_per_page = 25
    actions = ["renovar_30_dias_action"]

    def plataforma_display(self, obj):
        return obj.cuenta_maestra.plataforma
    plataforma_display.short_description = "Servicio"

    def estado_badge(self, obj):
        colores = {
            "Al día": "#10B981",       # Verde esmeralda
            "Por vencer": "#F59E0B",   # Ámbar/Naranja
            "Vencido": "#EF4444",      # Rojo
        }
        color = colores.get(obj.estado, "#6B7280")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 9999px; font-size: 0.8em; font-weight: 600;">{}</span>',
            color, obj.estado
        )
    estado_badge.short_description = "Estado"

    def renovar_30_dias_action(self, request, queryset):
        for sub in queryset:
            sub.renovar_30_dias()
        self.message_user(request, f"Se extendieron +30 días a {queryset.count()} suscripciones.")
    renovar_30_dias_action.short_description = "Renovar suscripciones seleccionadas (+30 días)"


@admin.register(MetodoPago)
class MetodoPagoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo", "creado_el")
    list_filter = ("activo",)
    search_fields = ("nombre", "datos_pago")


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ("id", "suscripcion", "monto", "metodo_pago", "referencia", "origen", "estado_badge", "fecha_pago")
    list_filter = ("estado", "origen", "metodo_pago")
    search_fields = ("referencia", "suscripcion__cliente__nombre", "suscripcion__cliente__telefono")
    actions = ["aprobar_pagos_action", "rechazar_pagos_action"]
    list_per_page = 25

    def estado_badge(self, obj):
        colores = {
            "Aprobado": "#10B981",
            "Pendiente": "#F59E0B",
            "Rechazado": "#EF4444",
        }
        color = colores.get(obj.estado, "#6B7280")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 9999px; font-size: 0.8em; font-weight: 600;">{}</span>',
            color, obj.estado
        )
    estado_badge.short_description = "Estado"

    def aprobar_pagos_action(self, request, queryset):
        count = 0
        for pago in queryset:
            if pago.estado != "Aprobado":
                pago.aprobar()
                count += 1
        self.message_user(request, f"Se aprobaron {count} pagos exitosamente y se extendieron las suscripciones.")
    aprobar_pagos_action.short_description = "Aprobar pagos seleccionados (+30 días)"

    def rechazar_pagos_action(self, request, queryset):
        count = queryset.update(estado="Rechazado")
        self.message_user(request, f"Se rechazaron {count} pagos.")
    rechazar_pagos_action.short_description = "Rechazar pagos seleccionados"
