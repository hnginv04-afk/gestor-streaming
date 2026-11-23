from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from suscripciones.models import Cliente, CuentaMaestra, Suscripcion, MetodoPago, Pago


class IntegrationWorkflowTestCase(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            nombre="Maria Rodriguez",
            telefono="+584241112233"
        )
        self.cuenta_maestra = CuentaMaestra.objects.create(
            plataforma="Netflix",
            correo="netflix.master2@example.com",
            fecha_facturacion=timezone.now().date(),
            max_perfiles=5
        )
        self.metodo_pago = MetodoPago.objects.create(
            nombre="Zelle",
            datos_pago="pagos@streaming.com",
            activo=True
        )

    def test_flujo_completo_reporte_cliente_y_aprobacion_admin(self):
        # 1. Suscripción inicial que venció hoy
        hoy = timezone.now().date()
        suscripcion = Suscripcion.objects.create(
            cliente=self.cliente,
            cuenta_maestra=self.cuenta_maestra,
            perfil_pin="Perfil 2 - PIN 4321",
            precio=Decimal("4.00"),
            fecha_inicio=hoy - timedelta(days=30),
            fecha_vencimiento=hoy,
            estado="Por vencer"
        )
        self.assertEqual(suscripcion.fecha_vencimiento, hoy)

        # 2. Cliente reporta pago
        pago = Pago.objects.create(
            suscripcion=suscripcion,
            metodo_pago=self.metodo_pago,
            monto=Decimal("4.00"),
            fecha_pago=hoy,
            referencia="ZELLE-TX-554433",
            origen="Cliente",
            estado="Pendiente"
        )
        self.assertEqual(pago.estado, "Pendiente")

        # 3. Administrador aprueba el pago
        pago.aprobar()
        pago.refresh_from_db()
        suscripcion.refresh_from_db()

        # 4. Validar que el pago está Aprobado y la suscripción sumó 30 días y está Al día
        self.assertEqual(pago.estado, "Aprobado")
        self.assertEqual(suscripcion.fecha_vencimiento, hoy + timedelta(days=30))
        self.assertEqual(suscripcion.estado, "Al día")

    def test_pago_manual_registrado_por_admin(self):
        hoy = timezone.now().date()
        suscripcion = Suscripcion.objects.create(
            cliente=self.cliente,
            cuenta_maestra=self.cuenta_maestra,
            perfil_pin="Perfil 3",
            precio=Decimal("4.00"),
            fecha_inicio=hoy - timedelta(days=35),
            fecha_vencimiento=hoy - timedelta(days=5),
            estado="Vencido"
        )
        # Admin registra pago manual (por ejemplo, efectivo o cobro externo)
        pago_admin = Pago.objects.create(
            suscripcion=suscripcion,
            metodo_pago=None,
            monto=Decimal("4.00"),
            fecha_pago=hoy,
            referencia="",
            origen="Admin",
            estado="Aprobado"
        )
        # La suscripción al registrar pago aprobado debe extender vigencia +30 días desde hoy
        suscripcion.renovar_30_dias()
        suscripcion.refresh_from_db()

        self.assertEqual(pago_admin.estado, "Aprobado")
        self.assertEqual(suscripcion.fecha_vencimiento, hoy + timedelta(days=30))
        self.assertEqual(suscripcion.estado, "Al día")
