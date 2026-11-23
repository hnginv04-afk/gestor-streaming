import json
from decimal import Decimal
from datetime import timedelta
from django.test import TestCase, Client
from django.utils import timezone
from suscripciones.models import Cliente, CuentaMaestra, Suscripcion, MetodoPago, Pago


class AdminAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.cliente = Cliente.objects.create(
            nombre="Luis Ramirez",
            telefono="+584167778899"
        )
        self.cuenta_maestra = CuentaMaestra.objects.create(
            plataforma="Crunchyroll",
            correo="crunchy.master.api@example.com",
            fecha_facturacion=timezone.now().date(),
            max_perfiles=4
        )
        self.suscripcion = Suscripcion.objects.create(
            cliente=self.cliente,
            cuenta_maestra=self.cuenta_maestra,
            perfil_pin="Perfil 2",
            precio=Decimal("3.50"),
            fecha_inicio=timezone.now().date() - timedelta(days=35),
            fecha_vencimiento=timezone.now().date() - timedelta(days=5),
            estado="Vencido"
        )
        self.metodo_pago = MetodoPago.objects.create(
            nombre="Zelle",
            datos_pago="pagos@streaming.com",
            activo=True
        )

    def test_panel_cobros_listado_y_whatsapp_url(self):
        response = self.client.get('/api/admin/panel-cobros/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(len(data['suscripciones']) >= 1)
        sub_data = data['suscripciones'][0]
        self.assertEqual(sub_data['estado'], "Vencido")
        self.assertIn("https://wa.me/", sub_data['whatsapp_url'])
        self.assertIn("584167778899", sub_data['whatsapp_url'])

    def test_panel_cobros_filtro_por_estado(self):
        response = self.client.get('/api/admin/panel-cobros/', {'estado': 'Vencido'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        for item in data['suscripciones']:
            self.assertEqual(item['estado'], "Vencido")

    def test_aprobar_pago_transiciona_y_renueva(self):
        hoy = timezone.now().date()
        pago = Pago.objects.create(
            suscripcion=self.suscripcion,
            metodo_pago=self.metodo_pago,
            monto=Decimal("3.50"),
            referencia="TX-APPROVE-1",
            origen="Cliente",
            estado="Pendiente"
        )
        response = self.client.post(f'/api/admin/pagos/{pago.id}/aprobar/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('ok'))
        pago.refresh_from_db()
        self.suscripcion.refresh_from_db()
        self.assertEqual(pago.estado, "Aprobado")
        self.assertEqual(self.suscripcion.estado, "Al día")
        self.assertEqual(self.suscripcion.fecha_vencimiento, hoy + timedelta(days=30))

    def test_rechazar_pago(self):
        pago = Pago.objects.create(
            suscripcion=self.suscripcion,
            metodo_pago=self.metodo_pago,
            monto=Decimal("3.50"),
            referencia="TX-REJECT-1",
            origen="Cliente",
            estado="Pendiente"
        )
        response = self.client.post(
            f'/api/admin/pagos/{pago.id}/rechazar/',
            data=json.dumps({'motivo': 'Referencia no encontrada en banco'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        pago.refresh_from_db()
        self.assertEqual(pago.estado, "Rechazado")

    def test_registro_pago_manual(self):
        hoy = timezone.now().date()
        payload = {
            'suscripcion_id': self.suscripcion.id,
            'monto': "3.50",
            'metodo_pago_id': None,
            'referencia': "",
            'notas': "Cobro en efectivo realizado en tienda"
        }
        response = self.client.post(
            '/api/admin/pago-manual/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.suscripcion.refresh_from_db()
        self.assertEqual(self.suscripcion.estado, "Al día")
        self.assertEqual(self.suscripcion.fecha_vencimiento, hoy + timedelta(days=30))

    def test_resumen_metricas(self):
        response = self.client.get('/api/admin/resumen/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('total_cobrado_mes', data)
        self.assertIn('total_suscripciones', data)
        self.assertIn('conteo_estados', data)
