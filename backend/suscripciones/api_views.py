import json
import re
from decimal import Decimal
from urllib.parse import quote
from datetime import date
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Sum
from django.core.exceptions import ValidationError
from .models import Cliente, CuentaMaestra, Suscripcion, MetodoPago, Pago


def limpiar_telefono(tel):
    """Elimina caracteres no numéricos excepto el prefijo '+' inicial si existe."""
    if not tel:
        return ""
    tel = tel.strip()
    tiene_plus = tel.startswith("+")
    numeros = re.sub(r"\D", "", tel)
    return ("+" + numeros) if tiene_plus else numeros


def serialize_suscripcion(sub):
    sub.actualizar_estado()
    hoy = timezone.now().date()
    dias_restantes = (sub.fecha_vencimiento - hoy).days
    tel_limpio = re.sub(r"\D", "", sub.cliente.telefono)

    # Mensaje predeterminado de WhatsApp para el vendedor
    texto_whatsapp = (
        f"Hola {sub.cliente.nombre}! 👋 Te saludamos de tu servicio de streaming. "
        f"Te recordamos que tu pantalla de *{sub.cuenta_maestra.plataforma}* ({sub.perfil_pin}) "
        f"vence el *{sub.fecha_vencimiento.strftime('%d/%m/%Y')}* (Monto: ${sub.precio}).\n\n"
        f"Puedes consultar tus datos y reportar tu pago aquí: {settings.FRONTEND_URL}/\n"
        f"¡Gracias por tu preferencia!"
    )
    whatsapp_url = f"https://wa.me/{tel_limpio}?text={quote(texto_whatsapp)}"

    tiene_pendiente = sub.pagos.filter(estado="Pendiente").exists()

    return {
        "id": sub.id,
        "cliente_id": sub.cliente.id,
        "cliente_nombre": sub.cliente.nombre,
        "cliente_telefono": sub.cliente.telefono,
        "plataforma": sub.cuenta_maestra.plataforma,
        "cuenta_maestra_correo": sub.cuenta_maestra.correo,
        "perfil_pin": sub.perfil_pin,
        "precio": str(sub.precio),
        "fecha_inicio": sub.fecha_inicio.isoformat(),
        "fecha_vencimiento": sub.fecha_vencimiento.isoformat(),
        "dias_restantes": dias_restantes,
        "estado": sub.estado,
        "activa": sub.activa,
        "whatsapp_url": whatsapp_url,
        "tiene_pago_pendiente": tiene_pendiente,
    }


def serialize_metodo_pago(m):
    return {
        "id": m.id,
        "nombre": m.nombre,
        "datos_pago": m.datos_pago,
        "activo": m.activo,
    }


# ==============================================================================
# ENDPOINTS PÚBLICOS (CLIENTE)
# ==============================================================================

@require_http_methods(["GET"])
def api_consulta_cliente(request):
    """Consulta pública por teléfono: devuelve suscripciones y métodos de pago."""
    telefono_raw = request.GET.get("telefono", "").strip()
    if not telefono_raw:
        return JsonResponse({"encontrado": False, "error": "Debe proporcionar un número de teléfono."}, status=400)

    tel_limpio = limpiar_telefono(telefono_raw)
    solo_digitos = re.sub(r"\D", "", telefono_raw)

    cliente = (
        Cliente.objects.filter(telefono=telefono_raw).first()
        or Cliente.objects.filter(telefono=tel_limpio).first()
        or Cliente.objects.filter(telefono__endswith=solo_digitos[-8:] if len(solo_digitos) >= 8 else solo_digitos).first()
    )

    if not cliente:
        return JsonResponse({
            "encontrado": False,
            "mensaje": f"No se encontraron suscripciones registradas para el teléfono {telefono_raw}."
        }, status=404)

    suscripciones = cliente.suscripciones.filter(activa=True).select_related("cuenta_maestra")
    metodos = MetodoPago.objects.filter(activo=True)

    return JsonResponse({
        "encontrado": True,
        "cliente": {
            "id": cliente.id,
            "nombre": cliente.nombre,
            "telefono": cliente.telefono,
        },
        "suscripciones": [serialize_suscripcion(s) for s in suscripciones],
        "metodos_pago": [serialize_metodo_pago(m) for m in metodos],
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_reportar_pago(request):
    """Reporte público de pago realizado por el cliente."""
    try:
        if request.content_type == "application/json":
            data = json.loads(request.body.decode("utf-8"))
        else:
            data = request.POST

        sub_id = data.get("suscripcion_id")
        metodo_id = data.get("metodo_pago_id")
        monto_str = data.get("monto", "0")
        referencia = str(data.get("referencia", "")).strip()
        notas = str(data.get("notas", "")).strip()

        if not sub_id:
            return JsonResponse({"ok": False, "error": "Debe especificar la suscripción a renovar."}, status=400)

        suscripcion = Suscripcion.objects.filter(id=sub_id).first()
        if not suscripcion:
            return JsonResponse({"ok": False, "error": "Suscripción no encontrada."}, status=404)

        try:
            monto = Decimal(str(monto_str))
            if monto <= 0:
                raise ValueError()
        except Exception:
            return JsonResponse({"ok": False, "error": "El monto debe ser un número mayor a cero."}, status=400)

        if not referencia:
            return JsonResponse({"ok": False, "error": "El número de referencia o comprobante es obligatorio."}, status=400)

        if Pago.objects.filter(referencia=referencia).exists():
            return JsonResponse({"ok": False, "error": f"Ya existe un pago registrado con la referencia '{referencia}'."}, status=400)

        metodo = MetodoPago.objects.filter(id=metodo_id).first() if metodo_id else None

        comprobante = request.FILES.get("comprobante_imagen")

        pago = Pago(
            suscripcion=suscripcion,
            metodo_pago=metodo,
            monto=monto,
            referencia=referencia,
            origen="Cliente",
            estado="Pendiente",
            comprobante_imagen=comprobante,
            notas=notas,
        )
        pago.full_clean()
        pago.save()

        return JsonResponse({
            "ok": True,
            "mensaje": "¡Pago reportado con éxito! El administrador verificará tu comprobante a la brevedad.",
            "pago": {
                "id": pago.id,
                "referencia": pago.referencia,
                "monto": str(pago.monto),
                "estado": pago.estado,
                "fecha_pago": pago.fecha_pago.isoformat(),
            }
        }, status=201)

    except ValidationError as ve:
        return JsonResponse({"ok": False, "error": str(ve)}, status=400)
    except Exception as e:
        return JsonResponse({"ok": False, "error": f"Error interno: {str(e)}"}, status=500)


# ==============================================================================
# ENDPOINTS ADMINISTRATIVOS (VENDEDOR)
# ==============================================================================

@require_http_methods(["GET"])
def api_panel_cobros(request):
    """Panel principal de cobros con filtros (Vencido, Por vencer, Al día) y búsqueda."""
    estado_filtro = request.GET.get("estado", "").strip()
    busqueda = request.GET.get("q", "").strip()

    qs = Suscripcion.objects.filter(activa=True).select_related("cliente", "cuenta_maestra")

    if busqueda:
        qs = qs.filter(cliente__nombre__icontains=busqueda) | qs.filter(cliente__telefono__icontains=busqueda)

    # Actualizar estados dinámicos al vuelo
    for s in qs:
        s.actualizar_estado()

    if estado_filtro:
        qs = qs.filter(estado=estado_filtro)

    # Ordenar: primero los vencidos, luego por vencer, luego al día
    lista = [serialize_suscripcion(s) for s in qs]
    orden_prioridad = {"Vencido": 0, "Por vencer": 1, "Al día": 2}
    lista.sort(key=lambda x: (orden_prioridad.get(x["estado"], 3), x["dias_restantes"]))

    return JsonResponse({
        "total": len(lista),
        "suscripciones": lista
    })


@require_http_methods(["GET"])
def api_pagos_pendientes(request):
    """Listado de comprobantes reportados por clientes pendientes de verificación."""
    pagos = Pago.objects.filter(estado="Pendiente").select_related(
        "suscripcion__cliente", "suscripcion__cuenta_maestra", "metodo_pago"
    ).order_by("-creado_el")

    resultado = []
    for p in pagos:
        resultado.append({
            "id": p.id,
            "suscripcion_id": p.suscripcion.id,
            "cliente_nombre": p.suscripcion.cliente.nombre,
            "cliente_telefono": p.suscripcion.cliente.telefono,
            "plataforma": p.suscripcion.cuenta_maestra.plataforma,
            "perfil_pin": p.suscripcion.perfil_pin,
            "metodo_pago": p.metodo_pago.nombre if p.metodo_pago else "No especificado",
            "monto": str(p.monto),
            "referencia": p.referencia,
            "fecha_pago": p.fecha_pago.isoformat(),
            "comprobante_url": p.comprobante_imagen.url if p.comprobante_imagen else None,
            "notas": p.notas,
            "creado_el": p.creado_el.isoformat(),
            "estado": p.estado,
        })

    return JsonResponse({"total": len(resultado), "pagos": resultado})


@csrf_exempt
@require_http_methods(["POST"])
def api_aprobar_pago(request, pago_id):
    """Aprueba un pago pendiente y suma 30 días automáticamente a la fecha de vencimiento."""
    pago = Pago.objects.filter(id=pago_id).first()
    if not pago:
        return JsonResponse({"ok": False, "error": "Pago no encontrado."}, status=404)

    pago.aprobar()
    return JsonResponse({
        "ok": True,
        "mensaje": f"Pago con referencia '{pago.referencia or 'Manual'}' aprobado con éxito.",
        "nueva_fecha_vencimiento": pago.suscripcion.fecha_vencimiento.isoformat(),
        "nuevo_estado_suscripcion": pago.suscripcion.estado,
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_rechazar_pago(request, pago_id):
    """Rechaza un pago pendiente con motivo opcional."""
    pago = Pago.objects.filter(id=pago_id).first()
    if not pago:
        return JsonResponse({"ok": False, "error": "Pago no encontrado."}, status=404)

    try:
        data = json.loads(request.body.decode("utf-8")) if request.body else {}
    except Exception:
        data = {}

    motivo = data.get("motivo", "")
    if motivo:
        pago.notas = f"Motivo de rechazo: {motivo}"
    pago.rechazar()

    return JsonResponse({
        "ok": True,
        "mensaje": f"Pago '{pago.referencia}' rechazado.",
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_pago_manual(request):
    """Registra un cobro externo/manual directo por el vendedor (+30 días inmediatos)."""
    try:
        data = json.loads(request.body.decode("utf-8")) if request.content_type == "application/json" else request.POST
        sub_id = data.get("suscripcion_id")
        monto_str = data.get("monto")
        metodo_id = data.get("metodo_pago_id")
        referencia = str(data.get("referencia", "")).strip()
        notas = str(data.get("notas", "Pago manual registrado por vendedor")).strip()

        suscripcion = Suscripcion.objects.filter(id=sub_id).first()
        if not suscripcion:
            return JsonResponse({"ok": False, "error": "Suscripción no encontrada."}, status=404)

        monto = Decimal(str(monto_str)) if monto_str else suscripcion.precio
        if monto <= 0:
            return JsonResponse({"ok": False, "error": "El monto debe ser mayor a cero."}, status=400)

        metodo = MetodoPago.objects.filter(id=metodo_id).first() if metodo_id else None

        pago = Pago(
            suscripcion=suscripcion,
            metodo_pago=metodo,
            monto=monto,
            referencia=referencia,
            origen="Admin",
            estado="Aprobado",
            notas=notas,
        )
        pago.save(skip_clean=True)
        suscripcion.renovar_30_dias()

        return JsonResponse({
            "ok": True,
            "mensaje": f"Pago manual registrado con éxito. Suscripción renovada hasta el {suscripcion.fecha_vencimiento.strftime('%d/%m/%Y')}.",
            "suscripcion": serialize_suscripcion(suscripcion)
        }, status=201)

    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)


@require_http_methods(["GET"])
def api_resumen_metricas(request):
    """Resumen para dashboard: ingresos del mes y desglose de suscripciones."""
    hoy = timezone.now().date()
    ingresos_mes = Pago.objects.filter(
        estado="Aprobado",
        fecha_pago__year=hoy.year,
        fecha_pago__month=hoy.month
    ).aggregate(total=Sum("monto"))["total"] or Decimal("0.00")

    # Actualizar estados
    for s in Suscripcion.objects.filter(activa=True):
        s.actualizar_estado()

    al_dia = Suscripcion.objects.filter(activa=True, estado="Al día").count()
    por_vencer = Suscripcion.objects.filter(activa=True, estado="Por vencer").count()
    vencidos = Suscripcion.objects.filter(activa=True, estado="Vencido").count()
    total_subs = al_dia + por_vencer + vencidos

    pagos_pendientes_count = Pago.objects.filter(estado="Pendiente").count()

    return JsonResponse({
        "total_cobrado_mes": str(ingresos_mes),
        "total_suscripciones": total_subs,
        "conteo_estados": {
            "al_dia": al_dia,
            "por_vencer": por_vencer,
            "vencidos": vencidos,
        },
        "pagos_pendientes_count": pagos_pendientes_count,
    })


# ==============================================================================
# CRUD RAPIDO DE CATALOGOS (ADMIN)
# ==============================================================================

@require_http_methods(["GET"])
def api_catalogo_cuentas_maestras(request):
    cuentas = CuentaMaestra.objects.all()
    return JsonResponse({
        "cuentas": [
            {
                "id": c.id,
                "plataforma": c.plataforma,
                "correo": c.correo,
                "fecha_facturacion": c.fecha_facturacion.isoformat(),
                "max_perfiles": c.max_perfiles,
                "perfiles_ocupados": c.perfiles_ocupados,
                "perfiles_disponibles": c.perfiles_disponibles,
                "activa": c.activa,
            }
            for c in cuentas
        ]
    })


@require_http_methods(["GET"])
def api_catalogo_metodos_pago(request):
    metodos = MetodoPago.objects.all()
    return JsonResponse({
        "metodos": [serialize_metodo_pago(m) for m in metodos]
    })
