// Lógica interactiva del Panel Administrativo

document.addEventListener('DOMContentLoaded', () => {
  const btnDjangoAdmin = document.getElementById('btnDjangoAdmin');
  if (btnDjangoAdmin && window.DJANGO_ADMIN_URL) {
    btnDjangoAdmin.href = window.DJANGO_ADMIN_URL;
  }

  // Elementos de métricas
  const metricTotalMes = document.getElementById('metricTotalMes');
  const metricAlDia = document.getElementById('metricAlDia');
  const metricPorVencer = document.getElementById('metricPorVencer');
  const metricVencidas = document.getElementById('metricVencidas');
  const badgePendingCount = document.getElementById('badgePendingCount');

  // Tabla y filtros de cobros
  const cobrosTableBody = document.getElementById('cobrosTableBody');
  const filterSearch = document.getElementById('filterSearch');
  const filterButtons = document.querySelectorAll('.btn-filter');
  const btnRefreshCobros = document.getElementById('btnRefreshCobros');

  // Pagos pendientes y Cuentas maestras
  const pagosPendientesContainer = document.getElementById('pagosPendientesContainer');
  const btnRefreshPagos = document.getElementById('btnRefreshPagos');
  const cuentasMaestrasContainer = document.getElementById('cuentasMaestrasContainer');

  // Modal pago manual
  const manualPayModal = new bootstrap.Modal(document.getElementById('manualPayModal'));
  const manualPayForm = document.getElementById('manualPayForm');
  const manualSubId = document.getElementById('manualSubId');
  const manualSubDisplay = document.getElementById('manualSubDisplay');
  const manualMonto = document.getElementById('manualMonto');
  const manualReferencia = document.getElementById('manualReferencia');
  const manualNotas = document.getElementById('manualNotas');
  const btnConfirmManualPay = document.getElementById('btnConfirmManualPay');

  let currentEstadoFilter = '';
  let searchDebounceTimeout = null;

  // 1. Inicialización
  loadDashboardData();

  async function loadDashboardData() {
    await Promise.all([
      cargarMetricas(),
      cargarPanelCobros(),
      cargarPagosPendientes(),
      cargarCuentasMaestras()
    ]);
  }

  // 2. Cargar Métricas
  async function cargarMetricas() {
    try {
      const { ok, data } = await window.API.getResumen();
      if (ok) {
        metricTotalMes.textContent = `$${parseFloat(data.total_cobrado_mes).toFixed(2)}`;
        metricAlDia.textContent = data.conteo_estados.al_dia;
        metricPorVencer.textContent = data.conteo_estados.por_vencer;
        metricVencidas.textContent = data.conteo_estados.vencidos;
        badgePendingCount.textContent = data.pagos_pendientes_count;
      }
    } catch (err) {
      console.error('Error al cargar métricas:', err);
    }
  }

  // 3. Cargar Panel de Cobros
  async function cargarPanelCobros() {
    cobrosTableBody.innerHTML = `
      <tr>
        <td colspan="5" class="text-center py-4 text-muted">
          <div class="spinner-border spinner-border-sm text-primary me-2"></div> Cargando suscripciones...
        </td>
      </tr>
    `;

    try {
      const q = filterSearch.value.trim();
      const { ok, data } = await window.API.getPanelCobros(currentEstadoFilter, q);

      if (!ok || data.suscripciones.length === 0) {
        cobrosTableBody.innerHTML = `
          <tr>
            <td colspan="5" class="text-center py-4 text-muted">
              <i class="bi bi-info-circle me-1"></i> No se encontraron suscripciones para este filtro.
            </td>
          </tr>
        `;
        return;
      }

      cobrosTableBody.innerHTML = '';
      data.suscripciones.forEach(sub => {
        const badgeClass = sub.estado === 'Al día' 
          ? 'badge-al-dia' 
          : sub.estado === 'Por vencer' 
            ? 'badge-por-vencer' 
            : 'badge-vencido';

        const brandClass = sub.plataforma.toLowerCase() === 'netflix' ? 'brand-netflix' : 'brand-crunchyroll';

        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td class="ps-4">
            <div class="fw-bold text-dark">${sub.cliente_nombre}</div>
            <div class="small text-muted"><i class="bi bi-whatsapp text-success me-1"></i>${sub.cliente_telefono}</div>
          </td>
          <td>
            <span class="brand-badge ${brandClass}">${sub.plataforma}</span>
            <div class="fw-semibold small mt-1">${sub.perfil_pin}</div>
          </td>
          <td>
            <div class="fw-semibold text-dark">${sub.fecha_vencimiento}</div>
            <div class="small text-muted">${sub.dias_restantes < 0 ? `Venció hace ${Math.abs(sub.dias_restantes)} días` : `Faltan ${sub.dias_restantes} días`}</div>
          </td>
          <td>
            <span class="${badgeClass}">${sub.estado}</span>
            ${sub.tiene_pago_pendiente ? '<span class="badge bg-warning text-dark ms-1">Pago pendiente</span>' : ''}
          </td>
          <td class="text-end pe-4">
            <div class="d-inline-flex gap-2">
              <a href="${sub.whatsapp_url}" target="_blank" class="btn btn-sm btn-whatsapp" title="Enviar recordatorio por WhatsApp">
                <i class="bi bi-whatsapp"></i> Recordar
              </a>
              <button class="btn btn-sm btn-outline-success btn-mark-paid" data-sub='${JSON.stringify(sub)}' title="Registrar cobro manual">
                <i class="bi bi-check2-circle"></i> Pagado
              </button>
            </div>
          </td>
        `;
        cobrosTableBody.appendChild(tr);
      });

      // Eventos de botones Marcar como Pagado
      document.querySelectorAll('.btn-mark-paid').forEach(btn => {
        btn.addEventListener('click', () => {
          const sub = JSON.parse(btn.getAttribute('data-sub'));
          openManualPayModal(sub);
        });
      });

    } catch (err) {
      cobrosTableBody.innerHTML = `
        <tr>
          <td colspan="5" class="text-center py-4 text-danger">
            <i class="bi bi-x-circle me-1"></i> Error al conectar con el servidor.
          </td>
        </tr>
      `;
    }
  }

  // 4. Cargar Pagos por Verificar
  async function cargarPagosPendientes() {
    pagosPendientesContainer.innerHTML = `
      <div class="col-12 text-center py-4 text-muted">
        <div class="spinner-border spinner-border-sm text-primary me-2"></div> Cargando pagos pendientes...
      </div>
    `;

    try {
      const { ok, data } = await window.API.getPagosPendientes();
      badgePendingCount.textContent = data.total;

      if (!ok || data.pagos.length === 0) {
        pagosPendientesContainer.innerHTML = `
          <div class="col-12 text-center py-5">
            <div class="bg-success-subtle text-success p-3 rounded-circle d-inline-block mb-3">
              <i class="bi bi-check2-all fs-2"></i>
            </div>
            <h5 class="fw-bold">¡Todo al día!</h5>
            <p class="text-muted small">No hay pagos pendientes de verificación en este momento.</p>
          </div>
        `;
        return;
      }

      pagosPendientesContainer.innerHTML = '';
      data.pagos.forEach(p => {
        const col = document.createElement('div');
        col.className = 'col-md-6 col-lg-4';
        col.innerHTML = `
          <div class="custom-card p-4 h-100 d-flex flex-column justify-content-between">
            <div>
              <div class="d-flex justify-content-between align-items-start mb-2">
                <span class="badge bg-warning-subtle text-warning-emphasis border border-warning-subtle rounded-pill px-3 py-1">
                  <i class="bi bi-clock me-1"></i> Pendiente
                </span>
                <span class="fw-bold text-success fs-5">$${p.monto}</span>
              </div>

              <h6 class="fw-bold mb-1">${p.cliente_nombre}</h6>
              <p class="small text-muted mb-2"><i class="bi bi-whatsapp text-success me-1"></i>${p.cliente_telefono}</p>

              <div class="bg-light p-2 rounded-3 small mb-3">
                <div><strong>Servicio:</strong> ${p.plataforma} (${p.perfil_pin})</div>
                <div><strong>Método:</strong> ${p.metodo_pago}</div>
                <div><strong>Referencia:</strong> <code class="text-primary fw-bold">${p.referencia}</code></div>
                ${p.notas ? `<div class="mt-1 text-muted"><em>"${p.notas}"</em></div>` : ''}
              </div>
            </div>

            <div class="d-flex gap-2">
              <button class="btn btn-sm btn-success w-100 fw-semibold btn-approve-pay" data-pago-id="${p.id}">
                <i class="bi bi-check2"></i> Aprobar (+30d)
              </button>
              <button class="btn btn-sm btn-outline-danger w-100 btn-reject-pay" data-pago-id="${p.id}">
                <i class="bi bi-x"></i> Rechazar
              </button>
            </div>
          </div>
        `;
        pagosPendientesContainer.appendChild(col);
      });

      // Eventos Aprobar / Rechazar
      document.querySelectorAll('.btn-approve-pay').forEach(btn => {
        btn.addEventListener('click', async () => {
          const pagoId = btn.getAttribute('data-pago-id');
          btn.disabled = true;
          btn.innerHTML = `<span class="spinner-border spinner-border-sm"></span>`;
          const res = await window.API.aprobarPago(pagoId);
          if (res.ok) {
            await loadDashboardData();
          } else {
            alert(res.data.error || 'Error al aprobar pago');
            btn.disabled = false;
          }
        });
      });

      document.querySelectorAll('.btn-reject-pay').forEach(btn => {
        btn.addEventListener('click', async () => {
          const pagoId = btn.getAttribute('data-pago-id');
          const motivo = prompt('Ingresa el motivo del rechazo (opcional):');
          if (motivo !== null) {
            btn.disabled = true;
            btn.innerHTML = `<span class="spinner-border spinner-border-sm"></span>`;
            const res = await window.API.rechazarPago(pagoId, motivo);
            if (res.ok) {
              await loadDashboardData();
            } else {
              alert(res.data.error || 'Error al rechazar pago');
              btn.disabled = false;
            }
          }
        });
      });

    } catch (err) {
      pagosPendientesContainer.innerHTML = `
        <div class="col-12 text-center py-4 text-danger">Error al cargar pagos pendientes.</div>
      `;
    }
  }

  // 5. Cuentas Maestras
  async function cargarCuentasMaestras() {
    cuentasMaestrasContainer.innerHTML = '';
    try {
      const { ok, data } = await window.API.getCuentasMaestras();
      if (!ok || data.cuentas.length === 0) return;

      data.cuentas.forEach(c => {
        const pct = Math.round((c.perfiles_ocupados / c.max_perfiles) * 100);
        const progressColor = pct >= 100 ? 'bg-danger' : pct >= 75 ? 'bg-warning' : 'bg-success';

        const col = document.createElement('div');
        col.className = 'col-md-6 col-lg-4';
        col.innerHTML = `
          <div class="custom-card p-3 h-100">
            <div class="d-flex justify-content-between align-items-center mb-2">
              <span class="brand-badge ${c.plataforma.toLowerCase() === 'netflix' ? 'brand-netflix' : 'brand-crunchyroll'}">${c.plataforma}</span>
              <span class="small fw-bold ${c.perfiles_disponibles > 0 ? 'text-success' : 'text-danger'}">
                ${c.perfiles_disponibles} cupos libres
              </span>
            </div>
            <h6 class="fw-bold mb-1">${c.correo}</h6>
            <div class="small text-muted mb-2">Renovación de cuenta: ${c.fecha_facturacion}</div>

            <div class="progress mb-2" style="height: 8px;">
              <div class="progress-bar ${progressColor}" role="progressbar" style="width: ${pct}%"></div>
            </div>
            <div class="d-flex justify-content-between small text-muted">
              <span>Ocupación: ${c.perfiles_ocupados}/${c.max_perfiles} perfiles</span>
              <span>${pct}%</span>
            </div>
          </div>
        `;
        cuentasMaestrasContainer.appendChild(col);
      });
    } catch (err) {
      console.error(err);
    }
  }

  // 6. Modal Pago Manual
  function openManualPayModal(sub) {
    manualSubId.value = sub.id;
    manualSubDisplay.value = `${sub.cliente_nombre} — ${sub.plataforma} (${sub.perfil_pin})`;
    manualMonto.value = sub.precio || '4.00';
    manualReferencia.value = '';
    manualNotas.value = 'Pago manual registrado en tienda / WhatsApp';
    manualPayModal.show();
  }

  manualPayForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    btnConfirmManualPay.disabled = true;
    btnConfirmManualPay.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Renovando...`;

    const payload = {
      suscripcion_id: manualSubId.value,
      monto: manualMonto.value,
      referencia: manualReferencia.value.trim(),
      notas: manualNotas.value.trim()
    };

    try {
      const { ok, data } = await window.API.registrarPagoManual(payload);
      if (ok) {
        manualPayModal.hide();
        await loadDashboardData();
      } else {
        alert(data.error || 'Error al registrar el pago');
      }
    } catch (err) {
      alert('Error de conexión con el servidor.');
    } finally {
      btnConfirmManualPay.disabled = false;
      btnConfirmManualPay.innerHTML = `Confirmar Renovación (+30 días)`;
    }
  });

  // 7. Filtros y Búsqueda
  filterButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      filterButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentEstadoFilter = btn.getAttribute('data-estado');
      cargarPanelCobros();
    });
  });

  filterSearch.addEventListener('input', () => {
    clearTimeout(searchDebounceTimeout);
    searchDebounceTimeout = setTimeout(() => {
      cargarPanelCobros();
    }, 300);
  });

  btnRefreshCobros.addEventListener('click', () => cargarPanelCobros());
  btnRefreshPagos.addEventListener('click', () => cargarPagosPendientes());

});
