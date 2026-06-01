/**
 * compra_flujo.js
 * Maneja la selección de zonas en el mapa SVG.
 */
document.addEventListener('DOMContentLoaded', function () {

  // ── Variables de estado (declaradas al inicio del scope) ──────────
  var serviceFee = 5;
  var cart = [];
  var modalQty = 1;
  var selectedZoneId = null;
  var selectedZoneName = '';
  var selectedPrice = 0;
  var selectedLimite = 4;

  // ── Detectar página ───────────────────────────────────────────────
  var page = document.querySelector('[data-purchase-step]');
  if (!page) return;

  var step = page.dataset.purchaseStep;

  if (step === 'zones') {
    if (typeof USER_LOGGED_IN !== 'undefined' && USER_LOGGED_IN) {
      initTimer();
    }
    initZoneMap();
  }

  // ── Timer ─────────────────────────────────────────────────────────
  function initTimer() {
    var countdownEl = document.getElementById('countdown');
    if (!countdownEl) return;

    // Leer el evento_id desde el atributo data del elemento en el DOM
    // para garantizar que esté disponible sin importar el orden de los scripts
    var eventoIdEl = document.getElementById('evento-id-data');
    var eventoId = eventoIdEl ? eventoIdEl.dataset.eventoId : 'x';
    var deadlineKey = 'purchaseDeadline_' + eventoId;

    // Solo crear el deadline si NO existe ya (no reiniciar al recargar)
    if (!localStorage.getItem(deadlineKey)) {
      localStorage.setItem(deadlineKey, String(Date.now() + 15 * 60 * 1000));
    }

    function tick() {
      var deadline = Number(localStorage.getItem(deadlineKey) || 0);
      var diff = Math.max(0, deadline - Date.now());
      var mins = Math.floor(diff / 60000);
      var secs = Math.floor((diff % 60000) / 1000);
      countdownEl.textContent = mins + ':' + (secs < 10 ? '0' : '') + secs;

      if (diff === 0) {
        localStorage.removeItem(deadlineKey);
        var banner = document.getElementById('timer-container');
        if (banner) {
          banner.style.background = 'rgba(239,68,68,0.15)';
          banner.style.borderColor = 'rgba(239,68,68,0.4)';
          var timerText = banner.querySelector('.timer-text');
          if (timerText) timerText.style.color = '#ef4444';
          countdownEl.style.color = '#ef4444';
          countdownEl.textContent = 'Expirado';
        }
        setTimeout(function() {
          window.location.href = eventoId !== 'x'
            ? '/comprar-entrada/' + eventoId + '/'
            : '/eventos/';
        }, 2000);
      }
    }

    tick();
    setInterval(tick, 1000);
  }

  // ── Mapa de zonas ─────────────────────────────────────────────────
  function initZoneMap() {
    var zones = document.querySelectorAll('.zone-path');

    if (zones.length === 0) {
      console.warn('compra_flujo: no se encontraron elementos .zone-path en el SVG');
      return;
    }

    zones.forEach(function(zone) {
      zone.style.cursor = 'pointer';
      zone.addEventListener('click', function () {
        var zonaId   = zone.dataset.zonaId  || null;
        var zoneName = zone.dataset.zone     || '';
        var precio   = Number(zone.dataset.price  || 0);
        var limite   = Number(zone.dataset.limite || 4);
        var asientosUrl = zone.dataset.asientosUrl || null;

        // Si tiene URL de asientos, redirigir directamente al mapa de asientos
        if (asientosUrl) {
          var isLoggedIn = typeof USER_LOGGED_IN !== 'undefined' ? USER_LOGGED_IN : false;
          if (!isLoggedIn) {
            var authModal = document.getElementById('authModal');
            if (authModal) {
              var modal = new bootstrap.Modal(authModal);
              if (typeof switchAuthTab === 'function') switchAuthTab('login');
              modal.show();
            }
            return;
          }
          // Animación de transición antes de redirigir
          var overlay = document.createElement('div');
          overlay.style.cssText = 'position:fixed;inset:0;background:#0A0E14;z-index:9999;opacity:0;transition:opacity .4s;pointer-events:none;display:flex;align-items:center;justify-content:center;';
          overlay.innerHTML = '<div style="text-align:center;"><div style="width:48px;height:48px;border:3px solid rgba(255,255,255,.1);border-top-color:' + (zone.style.fill || '#00AEEF') + ';border-radius:50%;animation:spin .8s linear infinite;margin:0 auto 1rem;"></div><p style="color:white;font-weight:700;">Cargando mapa de asientos...</p></div>';
          var style = document.createElement('style');
          style.textContent = '@keyframes spin{to{transform:rotate(360deg)}}';
          document.head.appendChild(style);
          document.body.appendChild(overlay);
          requestAnimationFrame(function() {
            overlay.style.opacity = '1';
            setTimeout(function() { window.location.href = asientosUrl; }, 400);
          });
          return;
        }

        // Fallback: modal de cantidad (para zonas sin asientos numerados)
        selectedZoneId   = zonaId;
        selectedZoneName = zoneName;
        selectedPrice    = precio;
        selectedLimite   = limite;
        modalQty = 1;
        actualizarModal();
        var modal = document.getElementById('quantity-modal');
        if (modal) modal.classList.remove('hidden');
      });
    });

    renderResumen();
    initModal();
    initBotonContinuar();
  }

  // ── Modal de cantidad ─────────────────────────────────────────────
  function initModal() {
    // Botones cerrar
    var closeBtns = document.querySelectorAll('[data-close-modal]');
    for (var i = 0; i < closeBtns.length; i++) {
      closeBtns[i].addEventListener('click', cerrarModal);
    }

    // Botones +/-
    var qtyBtns = document.querySelectorAll('[data-qty-change]');
    for (var i = 0; i < qtyBtns.length; i++) {
      (function (btn) {
        btn.addEventListener('click', function () {
          var delta = Number(btn.dataset.qtyChange || 0);
          modalQty = Math.max(1, Math.min(selectedLimite, modalQty + delta));
          actualizarModal();
        });
      })(qtyBtns[i]);
    }

    // Botón agregar
    var addBtn = document.getElementById('modal-add-btn');
    if (addBtn) {
      addBtn.addEventListener('click', function () {
        if (!selectedZoneId) return;

        var existing = null;
        for (var i = 0; i < cart.length; i++) {
          if (cart[i].zona_id === selectedZoneId) { existing = cart[i]; break; }
        }

        if (existing) {
          existing.qty = Math.min(selectedLimite, existing.qty + modalQty);
        } else {
          cart.push({
            zona_id: selectedZoneId,
            zone:    selectedZoneName,
            price:   selectedPrice,
            qty:     modalQty,
          });
        }

        renderResumen();
        cerrarModal();
      });
    }
  }

  function actualizarModal() {
    var elNombre = document.getElementById('modal-zone-name');
    var elPrecio = document.getElementById('modal-zone-price');
    var elQty    = document.getElementById('modal-qty');
    if (elNombre) elNombre.textContent = selectedZoneName;
    if (elPrecio) elPrecio.textContent = 'Bs. ' + selectedPrice + ' por entrada';
    if (elQty)    elQty.textContent    = String(modalQty);
  }

  function cerrarModal() {
    var modal = document.getElementById('quantity-modal');
    if (modal) modal.classList.add('hidden');
  }

  // ── Resumen de compra ─────────────────────────────────────────────
  function getTotals() {
    var subtotal = 0;
    for (var i = 0; i < cart.length; i++) {
      subtotal += cart[i].price * cart[i].qty;
    }
    var service = subtotal > 0 ? serviceFee : 0;
    return { subtotal: subtotal, service: service, total: subtotal + service };
  }

  function renderResumen() {
    var container = document.getElementById('cart-items');
    var btnContinuar = document.getElementById('btn-continue-payment');
    if (!container) return;

    var totals = getTotals();
    container.innerHTML = '';

    if (cart.length === 0) {
      container.innerHTML = '<p class="text-center text-gray-500 py-4">No has seleccionado zonas aún</p>';
      if (btnContinuar) btnContinuar.disabled = true;
    } else {
      if (btnContinuar) btnContinuar.disabled = false;

      for (var i = 0; i < cart.length; i++) {
        (function (item, idx) {
          var row = document.createElement('div');
          row.className = 'selected-item';
          row.innerHTML =
            '<div>' +
              '<p class="font-bold text-sm">' + item.zone + '</p>' +
              '<p class="text-xs text-gray-500">' + item.qty + ' entrada' + (item.qty > 1 ? 's' : '') + ' × Bs. ' + item.price + '</p>' +
            '</div>' +
            '<div class="flex items-center gap-4">' +
              '<span class="font-bold">Bs. ' + (item.price * item.qty) + '</span>' +
              '<button type="button" class="btn-remove-item" aria-label="Eliminar"><i class="fas fa-trash-alt"></i></button>' +
            '</div>';

          row.querySelector('.btn-remove-item').addEventListener('click', function () {
            cart.splice(idx, 1);
            renderResumen();
          });

          container.appendChild(row);
        })(cart[i], i);
      }
    }

    setText('subtotal-val', 'Bs. ' + totals.subtotal);
    setText('service-val',  'Bs. ' + totals.service);
    setText('total-val',    'Bs. ' + totals.total);
  }

  // ── Botón Continuar ───────────────────────────────────────────────
  function initBotonContinuar() {
    var btn = document.getElementById('btn-continue-payment');
    if (!btn) return;

    btn.addEventListener('click', function () {
      if (cart.length === 0) return;

      var carritoServidor = [];
      for (var i = 0; i < cart.length; i++) {
        carritoServidor.push({ zona_id: cart[i].zona_id, qty: cart[i].qty });
      }

      var form = document.createElement('form');
      form.method = 'POST';
      form.action = (typeof FINALIZAR_URL !== 'undefined') ? FINALIZAR_URL : '/';

      var csrfInput = document.createElement('input');
      csrfInput.type  = 'hidden';
      csrfInput.name  = 'csrfmiddlewaretoken';
      csrfInput.value = (typeof CSRF_TOKEN !== 'undefined') ? CSRF_TOKEN : getCookie('csrftoken');
      form.appendChild(csrfInput);

      var carritoInput = document.createElement('input');
      carritoInput.type  = 'hidden';
      carritoInput.name  = 'carrito_json';
      carritoInput.value = JSON.stringify(carritoServidor);
      form.appendChild(carritoInput);

      document.body.appendChild(form);
      form.submit();
    });
  }

  // ── Utilidades ────────────────────────────────────────────────────
  function setText(id, value) {
    var el = document.getElementById(id);
    if (el) el.textContent = value;
  }

  function getCookie(name) {
    var value = '; ' + document.cookie;
    var parts = value.split('; ' + name + '=');
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
  }

});
