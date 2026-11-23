// Lógica interactiva del portal público para clientes

document.addEventListener('DOMContentLoaded', () => {
  const searchForm = document.getElementById('searchForm');
  const phoneInput = document.getElementById('phoneInput');
  const btnSearch = document.getElementById('btnSearch');
  const searchFeedback = document.getElementById('searchFeedback');

  const resultsContainer = document.getElementById('resultsContainer');
  const clientName = document.getElementById('clientName');
  const clientPhone = document.getElementById('clientPhone');
  const subscriptionsList = document.getElementById('subscriptionsList');
  const paymentMethodsList = document.getElementById('paymentMethodsList');

  const paymentReportModal = new bootstrap.Modal(document.getElementById('reportPaymentModal'));
  const paymentReportForm = document.getElementById('paymentReportForm');
  const reportSubSelect = document.getElementById('reportSubSelect');
  const reportMethodSelect = document.getElementById('reportMethodSelect');
  const reportMonto = document.getElementById('reportMonto');
  const reportReferencia = document.getElementById('reportReferencia');
  const reportNotas = document.getElementById('reportNotas');
  const modalAlert = document.getElementById('modalAlert');
  const btnSubmitReport = document.getElementById('btnSubmitReport');

  let currentClientData = null;

  // 1. Manejo del formulario de búsqueda
  searchForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const phone = phoneInput.value.trim();
    if (!phone) return;

    // Estado visual de carga
    btnSearch.disabled = true;
    btnSearch.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Buscando...`;
    searchFeedback.innerHTML = '';
    resultsContainer.classList.add('d-none');

    try {
      const { ok, status, data } = await window.API.consultarCliente(phone);

      if (ok && data.encontrado) {
        currentClientData = data;
        renderClientView(data);
      } else {
        searchFeedback.innerHTML = `
          <div class="alert alert-warning py-2 px-3 small border-0 shadow-sm d-inline-block rounded-pill text-dark">
            <i class="bi bi-exclamation-triangle-fill text-warning me-1"></i>
            ${data.mensaje || 'No se encontraron suscripciones activas asociadas a este número de teléfono.'}
          </div>
        `;
      }
    } catch (err) {
      searchFeedback.innerHTML = `
        <div class="alert alert-danger py-2 px-3 small border-0 shadow-sm d-inline-block rounded-pill text-dark">
          <i class="bi bi-x-circle-fill text-danger me-1"></i>
          Error de conexión al servidor. Asegúrate de que el backend esté en ejecución.
        </div>
      `;
    } finally {
      btnSearch.disabled = false;
      btnSearch.innerHTML = `<span>Consultar</span> <i class="bi bi-search"></i>`;
    }
  });

  // 2. Renderizado de la vista de cliente
  function renderClientView(data) {
    clientName.textContent = `Hola, ${data.cliente.nombre}! 👋`;
    clientPhone.textContent = `Teléfono: ${data.cliente.telefono}`;

    // Renderizar suscripciones
    subscriptionsList.innerHTML = '';
    data.suscripciones.forEach((sub) => {
      const badgeClass = sub.estado === 'Al día' 
        ? 'badge-al-dia' 
        : sub.estado === 'Por vencer' 
          ? 'badge-por-vencer' 
          : 'badge-vencido';

      const brandBadgeClass = sub.plataforma.toLowerCase() === 'netflix' 
        ? 'brand-netflix' 
        : 'brand-crunchyroll';

      const fechaCorte = new Date(sub.fecha_vencimiento + 'T00:00:00').toLocaleDateString('es-ES', {
        day: '2-digit', month: 'long', year: 'numeric'
      });

      const col = document.createElement('div');
      col.className = 'col-md-6 col-lg-4';
      col.innerHTML = `
        <div class="custom-card p-4 h-100 d-flex flex-column justify-content-between">
          <div>
            <div class="d-flex justify-content-between align-items-start mb-3">
              <span class="brand-badge ${brandBadgeClass}">${sub.plataforma}</span>
              <span class="${badgeClass}">${sub.estado}</span>
            </div>
            <h5 class="fw-bold mb-1">${sub.perfil_pin}</h5>
            <p class="text-muted small mb-3">Cuenta: ${sub.cuenta_maestra_correo}</p>
            
            <div class="bg-light p-2 rounded-3 mb-3">
              <div class="d-flex justify-content-between small text-muted">
                <span>Fecha de corte:</span>
                <span class="fw-semibold text-dark">${fechaCorte}</span>
              </div>
              <div class="d-flex justify-content-between small text-muted mt-1">
                <span>Precio mensual:</span>
                <span class="fw-bold text-dark">$${sub.precio}</span>
              </div>
            </div>
          </div>

          <button class="btn btn-primary-custom w-100 btn-report-pay" data-sub-id="${sub.id}" data-precio="${sub.precio}">
            <i class="bi bi-receipt me-1"></i> Reportar Pago
          </button>
        </div>
      `;
      subscriptionsList.appendChild(col);
    });

    // Renderizar métodos de pago
    paymentMethodsList.innerHTML = '';
    data.metodos_pago.forEach((m) => {
      const col = document.createElement('div');
      col.className = 'col-md-6 col-lg-4';
      col.innerHTML = `
        <div class="custom-card p-3 h-100">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <span class="fw-bold text-primary">${m.nombre}</span>
            <button class="btn btn-sm btn-outline-primary border-0 rounded-pill btn-copy" data-text="${m.datos_pago}">
              <i class="bi bi-clipboard"></i> Copiar
            </button>
          </div>
          <div class="payment-code small text-secondary text-break">${m.datos_pago}</div>
        </div>
      `;
      paymentMethodsList.appendChild(col);
    });

    // Eventos de botones copiar
    document.querySelectorAll('.btn-copy').forEach(btn => {
      btn.addEventListener('click', () => {
        const text = btn.getAttribute('data-text');
        navigator.clipboard.writeText(text).then(() => {
          const original = btn.innerHTML;
          btn.innerHTML = `<i class="bi bi-check2"></i> ¡Copiado!`;
          btn.classList.replace('btn-outline-primary', 'btn-success');
          setTimeout(() => {
            btn.innerHTML = original;
            btn.classList.replace('btn-success', 'btn-outline-primary');
          }, 2000);
        });
      });
    });

    // Eventos de botones Reportar Pago
    document.querySelectorAll('.btn-report-pay').forEach(btn => {
      btn.addEventListener('click', () => {
        const subId = btn.getAttribute('data-sub-id');
        const precio = btn.getAttribute('data-precio');
        openReportModal(subId, precio);
      });
    });

    resultsContainer.classList.remove('d-none');
    resultsContainer.scrollIntoView({ behavior: 'smooth' });
  }

  // 3. Abrir modal de reporte de pago
  function openReportModal(subId, precio) {
    reportSubSelect.innerHTML = '';
    currentClientData.suscripciones.forEach(s => {
      const opt = document.createElement('option');
      opt.value = s.id;
      opt.textContent = `${s.plataforma} - ${s.perfil_pin} ($${s.precio})`;
      if (s.id == subId) opt.selected = true;
      reportSubSelect.appendChild(opt);
    });

    reportMethodSelect.innerHTML = '';
    currentClientData.metodos_pago.forEach(m => {
      const opt = document.createElement('option');
      opt.value = m.id;
      opt.textContent = m.nombre;
      reportMethodSelect.appendChild(opt);
    });

    reportMonto.value = precio || '4.00';
    reportReferencia.value = '';
    reportNotas.value = '';
    modalAlert.classList.add('d-none');
    paymentReportModal.show();
  }

  // 4. Envío del reporte de pago
  paymentReportForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    btnSubmitReport.disabled = true;
    btnSubmitReport.innerHTML = `<span class="spinner-border spinner-border-sm" role="status"></span> Enviando...`;
    modalAlert.classList.add('d-none');

    const payload = {
      suscripcion_id: reportSubSelect.value,
      metodo_pago_id: reportMethodSelect.value,
      monto: reportMonto.value,
      referencia: reportReferencia.value.trim(),
      notas: reportNotas.value.trim()
    };

    try {
      const { ok, status, data } = await window.API.reportarPago(payload);
      if (ok && data.ok) {
        modalAlert.className = 'alert alert-success small mb-3';
        modalAlert.innerHTML = `<i class="bi bi-check-circle-fill me-1"></i> ${data.mensaje}`;
        modalAlert.classList.remove('d-none');
        paymentReportForm.reset();
        setTimeout(() => {
          paymentReportModal.hide();
        }, 2200);
      } else {
        modalAlert.className = 'alert alert-danger small mb-3';
        modalAlert.innerHTML = `<i class="bi bi-exclamation-octagon-fill me-1"></i> ${data.error || 'No se pudo registrar el pago.'}`;
        modalAlert.classList.remove('d-none');
      }
    } catch (err) {
      modalAlert.className = 'alert alert-danger small mb-3';
      modalAlert.innerHTML = `<i class="bi bi-exclamation-octagon-fill me-1"></i> Error al conectar con el servidor.`;
      modalAlert.classList.remove('d-none');
    } finally {
      btnSubmitReport.disabled = false;
      btnSubmitReport.innerHTML = `<span>Enviar Reporte</span> <i class="bi bi-send ms-1"></i>`;
    }
  });

});
