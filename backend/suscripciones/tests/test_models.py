from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from django.utils import timezone
from suscripciones.models import Cliente, CuentaMaestra, Suscripcion, MetodoPago, Pago


class ModelCreationTestCase(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            nombre="Carlos Gomez",
            telefono="+584121234567",
            notas="Cliente frecuente"
        )
        self.cuenta_maestra = CuentaMaestra.objects.create(
            plataforma="Netflix",
            correo="netflix.master1@example.com",
            fecha_facturacion=date(2026, 12, 1),
            max_perfiles=5
        )
        self.metodo_pago = MetodoPago.objects.create(
            nombre="Pago Móvil Banesco",
            datos_pago="CI: 12345678, Tel: 04121234567, Banco: Banesco",
            activo=True
        )

    def test_cliente_str(self):
        self.assertEqual(str(self.cliente), "Carlos Gomez (+584121234567)")

    def test_cuenta_maestra_str_and_properties(self):
        self.assertIn("Netflix", str(self.cuenta_maestra))
        self.assertEqual(self.cuenta_maestra.perfiles_ocupados, 0)
        self.assertEqual(self.cuenta_maestra.perfiles_disponibles, 5)

    def test_suscripcion_creation_and_str(self):
        hoy = timezone.now().date()
        suscripcion = Suscripcion.objects.create(
            cliente=self.cliente,
            cuenta_maestra=self.cuenta_maestra,
            perfil_pin="Perfil 1 - PIN 1234",
            precio=Decimal("4.50"),
            fecha_inicio=hoy,
            fecha_vencimiento=hoy + timedelta(days=30),
            estado="Al día"
        )
        self.assertEqual(suscripcion.cliente, self.cliente)
        self.assertEqual(suscripcion.cuenta_maestra, self.cuenta_maestra)
        self.assertEqual(self.cuenta_maestra.perfiles_ocupados, 1)
        self.assertEqual(self.cuenta_maestra.perfiles_disponibles, 4)
        self.assertIn("Carlos Gomez", str(suscripcion))

    def test_metodo_pago_str(self):
        self.assertEqual(str(self.metodo_pago), "Pago Móvil Banesco")

    def test_pago_creation_and_str(self):
        hoy = timezone.now().date()
        suscripcion = Suscripcion.objects.create(
            cliente=self.cliente,
            cuenta_maestra=self.cuenta_maestra,
            perfil_pin="Perfil 1 - PIN 1234",
            precio=Decimal("4.50"),
            fecha_inicio=hoy,
            fecha_vencimiento=hoy + timedelta(days=30)
        )
        pago = Pago.objects.create(
            suscripcion=suscripcion,
            metodo_pago=self.metodo_pago,
            monto=Decimal("4.50"),
            fecha_pago=hoy,
            referencia="REF-998877",
            origen="Cliente",
            estado="Pendiente"
        )
        self.assertEqual(pago.suscripcion, suscripcion)
        self.assertEqual(pago.referencia, "REF-998877")
        self.assertIn("REF-998877", str(pago))
