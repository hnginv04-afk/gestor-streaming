from html import escape
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def home_status(request):
    """Ruta raíz informativa y de salud para el Back-End en producción."""
    accept = request.headers.get("Accept", "")
    frontend_url = settings.FRONTEND_URL

    if "application/json" in accept and "text/html" not in accept:
        return JsonResponse({
            "status": "ok",
            "servicio": "Gestor Streaming API",
            "frontend_url": frontend_url,
            "endpoints": {
                "admin": "/admin/",
                "resumen": "/api/admin/resumen/",
                "panel_cobros": "/api/admin/panel-cobros/",
                "consulta_publica": "/api/public/consulta/?telefono=+584121112233",
            },
        })

    safe_front = escape(frontend_url)
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Gestor Streaming — Back-End API Activo</title>
  <style>
    body {{ font-family: Inter, system-ui, -apple-system, sans-serif; background: #F8FAFC; color: #0F172A; margin: 0; padding: 32px 16px; display: flex; justify-content: center; }}
    .card {{ max-width: 640px; width: 100%; background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; padding: 32px; box-shadow: 0 4px 16px rgba(15, 23, 42, 0.06); }}
    .badge {{ display: inline-block; background: #DCFCE7; color: #15803D; font-weight: 600; font-size: 13px; padding: 6px 12px; border-radius: 999px; margin-bottom: 16px; }}
    h1 {{ font-size: 22px; margin: 0 0 8px; }}
    p {{ color: #475569; line-height: 1.5; margin: 0 0 24px; }}
    .links {{ display: flex; flex-direction: column; gap: 10px; }}
    a.btn {{ display: block; text-decoration: none; padding: 12px 16px; border-radius: 10px; font-weight: 600; font-size: 14px; text-align: center; }}
    .btn-primary {{ background: #2563EB; color: #FFFFFF; }}
    .btn-secondary {{ background: #F1F5F9; color: #0F172A; border: 1px solid #CBD5E1; }}
  </style>
</head>
<body>
  <main class="card">
    <span class="badge">● Servidor Back-End Activo (Django REST)</span>
    <h1>Gestor Streaming — Motor API y Base de Datos</h1>
    <p>El servidor Back-End y la base de datos PostgreSQL están funcionando correctamente. Desde aquí se atienden las consultas y cobros de la aplicación web.</p>
    <div class="links">
      <a class="btn btn-primary" href="{safe_front}/">Abrir Aplicación Web (Front-End Cliente)</a>
      <a class="btn btn-secondary" href="{safe_front}/admin.html">Abrir Panel de Cobros (Front-End Admin)</a>
      <a class="btn btn-secondary" href="/admin/">Panel Nativo de Django (/admin/)</a>
      <a class="btn btn-secondary" href="/api/admin/resumen/">Ver Métricas JSON (/api/admin/resumen/)</a>
      <a class="btn btn-secondary" href="/api/public/consulta/?telefono=%2B584121112233">Probar Consulta API Cliente Demo (/api/public/consulta/)</a>
    </div>
  </main>
</body>
</html>"""
    return HttpResponse(html_content, content_type="text/html; charset=utf-8")
