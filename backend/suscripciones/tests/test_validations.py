from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from suscripciones.models import Cliente, CuentaMaestra, Suscripcion, MetodoPago, Pago


class BusinessValidationTestCase(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            nombre="Ana Lopez",
            telefono="+584149876543"
        )
        # Cuenta con capacidad máxima de 2 perfiles
        self.cuenta_maestra = CuentaMaestra.objects.create(
            plataforma="Crunchyroll",
            correo="crunchy.master1@example.com",
            fecha_facturacion=date(2026, 12, 15),
            max_perfiles=2
        )
        self.metodo_pago = MetodoPago.objects.create(
            nombre="Binance USDT",
            datos_pago="Pay ID: 987654321",
            activo=True
        )

    def test_limite_maximo_perfiles_por_cuenta_maestra(self):
        hoy = timezone.now().date()
        # Perfil 1 (OK)
        s1 = Suscripcion(
            cliente=self.cliente,
            cuenta_maestra=self.cuenta_maestra,
            perfil_pin="Perfil 1",
            precio=Decimal("3.00"),
            fecha_inicio=hoy,
            fecha_vencimiento=hoy + timedelta(days=30)
        )
        s1.full_clean()
        s1.save()

        # Perfil 2 (OK)
        s2 = Suscripcion(
            cliente=self.cliente,
            cuenta_maestra=self.cuenta_maestra,
            perfil_pin="Perfil 2",
            precio=Decimal("3.00"),
            fecha_inicio=hoy,
            fecha_vencimiento=hoy + timedelta(days=30)
        )
        s2.full_clean()
        s2.save()

        # Perfil 3 debe fallar por exceder max_perfiles=2
        s3 = Suscripcion(
            cliente=self.cliente,
            cuenta_maestra=self.cuenta_maestra,
            perfil_pin="Perfil 3",
            precio=Decimal("3.00"),
            fecha_inicio=hoy,
            fecha_vencimiento=hoy + timedelta(days=30)
        )
        with self.assertRaises(ValidationError):
            s3.full_clean()

    def test_monto_pago_debe_ser_mayor_a_cero(self):
        hoy = timezone.now().date()
        suscripcion = Suscripcion.objects.create(
            cliente=self.cliente,
            cuenta_maestra=self.cuenta_maestra,
            perfil_pin="Perfil 1",
            precio=Decimal("3.00"),
            fecha_inicio=hoy,
            fecha_vencimiento=hoy + timedelta(days=30)
        )
        # Pago con monto 0 debe fallar
        pago_cero = Pago(
            suscripcion=suscripcion,
            metodo_pago=self.metodo_pago,
            monto=Decimal("0.00"),
            fecha_pago=hoy,
            referencia="REF-ZERO",
            origen="Cliente"
        )
        with self.assertRaises(ValidationError):
            pago_cero.full_clean()

        # Pago con monto negativo debe fallar
        pago_negativo = Pago(
            suscripcion=suscripcion,
            metodo_pago=self.metodo_pago,
            monto=Decimal("-5.00"),
            fecha_pago=hoy,
            referencia="REF-NEG",
            origen="Cliente"
        )
        with self.assertRaises(ValidationError):
            pago_negativo.full_clean()

    def test_referencia_de_pago_debe_ser_unica(self):
        hoy = timezone.now().date()
        suscripcion = Suscripcion.objects.create(
            cliente=self.cliente,
            cuenta_maestra=self.cuenta_maestra,
            perfil_pin="Perfil 1",
            precio=Decimal("3.00"),
            fecha_inicio=hoy,
            fecha_vencimiento=hoy + timedelta(days=30)
        )
        pago1 = Pago(
            suscripcion=suscripcion,
            metodo_pago=self.metodo_pago,
            monto=Decimal("3.00"),
            fecha_pago=hoy,
            referencia="REF-112233",
            origen="Cliente",
            estado="Pendiente"
        )
        pago1.full_clean()
        pago1.save()

        # Segundo pago con la misma referencia debe lanzar ValidationError
        pago2 = Pago(
            suscripcion=suscripcion,
            metodo_pago=self.metodo_pago,
            monto=Decimal("3.00"),
            fecha_pago=hoy,
            referencia="REF-112233",
            origen="Cliente",
            estado="Pendiente"
        )
        with self.assertRaises(ValidationError):
            pago2.full_clean()

    def test_calculo_dinamico_de_estado_suscripcion(self):
        hoy = timezone.now().date()
        
        # 1. Al día (vence en 10 días)
        sub_al_dia = Suscripcion(
            cliente=self.cliente,
            cuenta_maestra=self.cuenta_maestra,
            perfil_pin="P1",
            precio=Decimal("3.00"),
            fecha_inicio=hoy - timedelta(days=20),
            fecha_vencimiento=hoy + timedelta(days=10)
        )
        self.assertEqual(sub_al_dia.calcular_estado(), "Al día")

        # 2. Por vencer (vence en 2 días)
        sub_por_vencer = Suscripcion(
            cliente=self.cliente,
            cuenta_maestra=self.cuenta_maestra,
            perfil_pin="P2",
            precio=Decimal("3.00"),
            fecha_inicio=hoy - timedelta(days=28),
            fecha_vencimiento=hoy + timedelta(days=2)
        )
        self.assertEqual(sub_por_vencer.calcular_estado(), "Por vencer")

        # 3. Vencido (venció hace 1 día)
        sub_vencido = Suscripcion(
            cliente=self.cliente,
            cuenta_maestra=self.cuenta_maestra,
            perfil_pin="P3",
            precio=Decimal("3.00"),
            fecha_inicio=hoy - timedelta(days=31),
            fecha_vencimiento=hoy - timedelta(days=1)
        )
        self.assertEqual(sub_vencido.calcular_estado(), "Vencido")
