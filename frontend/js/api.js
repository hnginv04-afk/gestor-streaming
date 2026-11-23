// Módulo de peticiones HTTP hacia la API de Django

const API = {
  // 1. Consulta pública por teléfono
  async consultarCliente(telefono) {
    const res = await fetch(`${window.API_BASE_URL}/public/consulta/?telefono=${encodeURIComponent(telefono)}`);
    const data = await res.json();
    return { status: res.status, ok: res.ok, data };
  },

  // 2. Reporte público de pago
  async reportarPago(payload) {
    let body;
    let headers = {};

    if (payload instanceof FormData) {
      body = payload;
    } else {
      body = JSON.stringify(payload);
      headers['Content-Type'] = 'application/json';
    }

    const res = await fetch(`${window.API_BASE_URL}/public/reportar-pago/`, {
      method: 'POST',
      headers,
      body
    });
    const data = await res.json();
    return { status: res.status, ok: res.ok, data };
  },

  // 3. Panel de cobros (admin)
  async getPanelCobros(estado = '', q = '') {
    let url = `${window.API_BASE_URL}/admin/panel-cobros/?`;
    if (estado) url += `estado=${encodeURIComponent(estado)}&`;
    if (q) url += `q=${encodeURIComponent(q)}&`;

    const res = await fetch(url);
    const data = await res.json();
    return { status: res.status, ok: res.ok, data };
  },

  // 4. Pagos pendientes (admin)
  async getPagosPendientes() {
    const res = await fetch(`${window.API_BASE_URL}/admin/pagos-pendientes/`);
    const data = await res.json();
    return { status: res.status, ok: res.ok, data };
  },

  // 5. Aprobar pago
  async aprobarPago(pagoId) {
    const res = await fetch(`${window.API_BASE_URL}/admin/pagos/${pagoId}/aprobar/`, {
      method: 'POST'
    });
    const data = await res.json();
    return { status: res.status, ok: res.ok, data };
  },

  // 6. Rechazar pago
  async rechazarPago(pagoId, motivo = '') {
    const res = await fetch(`${window.API_BASE_URL}/admin/pagos/${pagoId}/rechazar/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ motivo })
    });
    const data = await res.json();
    return { status: res.status, ok: res.ok, data };
  },

  // 7. Registro de pago manual (+30 días)
  async registrarPagoManual(payload) {
    const res = await fetch(`${window.API_BASE_URL}/admin/pago-manual/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    return { status: res.status, ok: res.ok, data };
  },

  // 8. Resumen y métricas
  async getResumen() {
    const res = await fetch(`${window.API_BASE_URL}/admin/resumen/`);
    const data = await res.json();
    return { status: res.status, ok: res.ok, data };
  },

  // 9. Cuentas maestras
  async getCuentasMaestras() {
    const res = await fetch(`${window.API_BASE_URL}/admin/cuentas-maestras/`);
    const data = await res.json();
    return { status: res.status, ok: res.ok, data };
  }
};

window.API = API;
