import json
from decimal import Decimal
from datetime import timedelta
from django.test import TestCase, Client
from django.utils import timezone
from suscripciones.models import Cliente, CuentaMaestra, Suscripcion, MetodoPago, Pago


class PublicAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.cliente = Cliente.objects.create(
            nombre="Pedro Perez",
            telefono="+584125556677",
            notas="Cliente VIP"
        )
        self.cuenta_maestra = CuentaMaestra.objects.create(
            plataforma="Netflix",
            correo="netflix.master.api@example.com",
            fecha_facturacion=timezone.now().date(),
            max_perfiles=5
        )
        self.suscripcion = Suscripcion.objects.create(
            cliente=self.cliente,
            cuenta_maestra=self.cuenta_maestra,
            perfil_pin="Perfil 1 - PIN 1111",
            precio=Decimal("4.00"),
            fecha_inicio=timezone.now().date() - timedelta(days=20),
            fecha_vencimiento=timezone.now().date() + timedelta(days=10),
            estado="Al día"
        )
        self.metodo_pago = MetodoPago.objects.create(
            nombre="Pago Móvil Banesco",
            datos_pago="CI: 12345678, Tel: 04121234567",
            activo=True
        )

    def test_consulta_suscripcion_por_telefono_exitoso(self):
        response = self.client.get('/api/public/consulta/', {'telefono': '+584125556677'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('encontrado'))
        self.assertEqual(data['cliente']['nombre'], "Pedro Perez")
        self.assertEqual(len(data['suscripciones']), 1)
        self.assertEqual(data['suscripciones'][0]['plataforma'], "Netflix")
        self.assertEqual(data['suscripciones'][0]['estado'], "Al día")
        self.assertTrue(len(data['metodos_pago']) >= 1)

    def test_consulta_telefono_inexistente(self):
        response = self.client.get('/api/public/consulta/', {'telefono': '+584120000000'})
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertFalse(data.get('encontrado'))

    def test_reportar_pago_exitoso(self):
        payload = {
            'suscripcion_id': self.suscripcion.id,
            'metodo_pago_id': self.metodo_pago.id,
            'monto': "4.00",
            'referencia': "REF-API-998811",
            'notas': "Reportado desde web"
        }
        response = self.client.post(
            '/api/public/reportar-pago/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data.get('ok'))
        self.assertEqual(data['pago']['estado'], "Pendiente")
        self.assertEqual(data['pago']['referencia'], "REF-API-998811")
        # Verificar en base de datos
        pago_db = Pago.objects.get(referencia="REF-API-998811")
        self.assertEqual(pago_db.estado, "Pendiente")
        self.assertEqual(pago_db.origen, "Cliente")

    def test_reportar_pago_sin_referencia_falla(self):
        payload = {
            'suscripcion_id': self.suscripcion.id,
            'metodo_pago_id': self.metodo_pago.id,
            'monto': "4.00",
            'referencia': ""
        }
        response = self.client.post(
            '/api/public/reportar-pago/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_reportar_pago_monto_cero_falla(self):
        payload = {
            'suscripcion_id': self.suscripcion.id,
            'monto': "0.00",
            'referencia': "REF-ZERO"
        }
        response = self.client.post(
            '/api/public/reportar-pago/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
