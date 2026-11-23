from django.urls import path
from . import api_views

urlpatterns = [
    # Endpoints públicos para clientes
    path('public/consulta/', api_views.api_consulta_cliente, name='api_consulta_cliente'),
    path('public/reportar-pago/', api_views.api_reportar_pago, name='api_reportar_pago'),

    # Endpoints administrativos para el vendedor
    path('admin/panel-cobros/', api_views.api_panel_cobros, name='api_panel_cobros'),
    path('admin/pagos-pendientes/', api_views.api_pagos_pendientes, name='api_pagos_pendientes'),
    path('admin/pagos/<int:pago_id>/aprobar/', api_views.api_aprobar_pago, name='api_aprobar_pago'),
    path('admin/pagos/<int:pago_id>/rechazar/', api_views.api_rechazar_pago, name='api_rechazar_pago'),
    path('admin/pago-manual/', api_views.api_pago_manual, name='api_pago_manual'),
    path('admin/resumen/', api_views.api_resumen_metricas, name='api_resumen_metricas'),

    # Catálogos para formularios de administración
    path('admin/cuentas-maestras/', api_views.api_catalogo_cuentas_maestras, name='api_cuentas_maestras'),
    path('admin/metodos-pago/', api_views.api_catalogo_metodos_pago, name='api_metodos_pago'),
]
