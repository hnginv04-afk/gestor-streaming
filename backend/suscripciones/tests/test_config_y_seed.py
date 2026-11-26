from pathlib import Path
from decimal import Decimal
from datetime import timedelta
from urllib.parse import unquote
from django.conf import settings
from django.core.management import call_command
from django.test import TestCase, Client, override_settings
from django.utils import timezone
from suscripciones.models import Cliente, CuentaMaestra, Suscripcion, MetodoPago


class ConfigYSeedTestCase(TestCase):
    def test_settings_sin_secret_key_fijo_y_con_frontend_url(self):
        settings_path = Path(settings.BASE_DIR) / "config" / "settings.py"
        content = settings_path.read_text(encoding="utf-8")
        self.assertNotIn("django-insecure-", content)
        self.assertIn("load_dotenv", content)
        self.assertTrue(hasattr(settings, "FRONTEND_URL"))
        self.assertIn("gestor-streaming-j1e6.netlify.app", settings.FRONTEND_URL)

    def test_whatsapp_url_usa_frontend_url_configurada(self):
        cliente = Cliente.objects.create(nombre="Ana Perez", telefono="+584129990011")
        cuenta = CuentaMaestra.objects.create(
            plataforma="Netflix",
            correo="net.test@example.com",
            fecha_facturacion=timezone.now().date(),
            max_perfiles=5,
        )
        Suscripcion.objects.create(
            cliente=cliente,
            cuenta_maestra=cuenta,
            perfil_pin="Perfil 1",
            precio=Decimal("4.00"),
            fecha_inicio=timezone.now().date(),
            fecha_vencimiento=timezone.now().date() + timedelta(days=2),
        )

        client = Client()
        resp = client.get("/api/admin/panel-cobros/")
        self.assertEqual(resp.status_code, 200)
        wa_url = unquote(resp.json()["suscripciones"][0]["whatsapp_url"])
        self.assertIn("https://gestor-streaming-j1e6.netlify.app", wa_url)
        self.assertNotIn("gestorstreaming.netlify.app", wa_url)

        with override_settings(FRONTEND_URL="https://mi-dominio-custom.netlify.app"):
            resp_custom = client.get("/api/admin/panel-cobros/")
            self.assertEqual(resp_custom.status_code, 200)
            wa_custom = unquote(resp_custom.json()["suscripciones"][0]["whatsapp_url"])
            self.assertIn("https://mi-dominio-custom.netlify.app", wa_custom)

    def test_seed_demo_es_idempotente_y_funciona_e2e(self):
        self.assertEqual(Cliente.objects.count(), 0)
        call_command("seed_demo")
        self.assertEqual(MetodoPago.objects.count(), 3)
        self.assertEqual(CuentaMaestra.objects.count(), 2)
        self.assertEqual(Cliente.objects.count(), 2)
        self.assertEqual(Suscripcion.objects.count(), 2)

        # Segunda ejecución no debe duplicar registros
        call_command("seed_demo")
        self.assertEqual(MetodoPago.objects.count(), 3)
        self.assertEqual(CuentaMaestra.objects.count(), 2)
        self.assertEqual(Cliente.objects.count(), 2)
        self.assertEqual(Suscripcion.objects.count(), 2)

        # Flujo E2E con los datos sembrados
        client = Client()
        consulta = client.get("/api/public/consulta/", {"telefono": "+584121112233"})
        self.assertEqual(consulta.status_code, 200)
        self.assertTrue(consulta.json()["encontrado"])
        self.assertEqual(len(consulta.json()["metodos_pago"]), 3)

        resumen = client.get("/api/admin/resumen/")
        self.assertEqual(resumen.status_code, 200)
        self.assertEqual(resumen.json()["total_suscripciones"], 2)
