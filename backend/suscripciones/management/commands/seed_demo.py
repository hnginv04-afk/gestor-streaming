from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from suscripciones.models import Cliente, CuentaMaestra, Suscripcion, MetodoPago


class Command(BaseCommand):
    help = "Carga datos iniciales de demostración de forma idempotente si la base de datos está vacía."

    def handle(self, *args, **options):
        if Cliente.objects.exists() or MetodoPago.objects.exists():
            self.stdout.write("La base de datos ya contiene registros; se omite seed_demo.")
            return

        hoy = timezone.now().date()

        # Métodos de pago de demostración (datos ficticios)
        MetodoPago.objects.create(
            nombre="Pago Móvil Banesco",
            datos_pago="CI: 19263109, Tel: 04121234567, Banco: Banesco (0134)",
        )
        MetodoPago.objects.create(
            nombre="Binance USDT",
            datos_pago="Pay ID: 123456789 (Red BEP20)",
        )
        MetodoPago.objects.create(
            nombre="Zelle",
            datos_pago="Correo: pagos@streamingvzla.com",
        )

        # Cuentas maestras de demostración
        c_netflix = CuentaMaestra.objects.create(
            plataforma="Netflix",
            correo="netflix.premium@gmail.com",
            fecha_facturacion=hoy,
            max_perfiles=5,
        )
        c_crunchy = CuentaMaestra.objects.create(
            plataforma="Crunchyroll",
            correo="crunchy.vip@gmail.com",
            fecha_facturacion=hoy,
            max_perfiles=4,
        )

        # Clientes de demostración
        cli_1 = Cliente.objects.create(
            nombre="Carlos Mendoza",
            telefono="+584121112233",
            notas="Cliente puntual",
        )
        cli_2 = Cliente.objects.create(
            nombre="Maria Valentina",
            telefono="+584149998877",
            notas="Paga por Binance",
        )

        # Suscripciones de ejemplo cubriendo estados 'Por vencer' y 'Vencido'
        Suscripcion.objects.create(
            cliente=cli_1,
            cuenta_maestra=c_netflix,
            perfil_pin="Perfil 1 - PIN 1234",
            precio=Decimal("4.00"),
            fecha_inicio=hoy - timedelta(days=28),
            fecha_vencimiento=hoy + timedelta(days=2),
        )
        Suscripcion.objects.create(
            cliente=cli_2,
            cuenta_maestra=c_crunchy,
            perfil_pin="Perfil 2 - Otaku",
            precio=Decimal("3.50"),
            fecha_inicio=hoy - timedelta(days=35),
            fecha_vencimiento=hoy - timedelta(days=5),
        )

        self.stdout.write(self.style.SUCCESS("Datos iniciales de demostración cargados con éxito."))
