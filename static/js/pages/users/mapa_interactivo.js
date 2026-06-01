document.addEventListener('DOMContentLoaded', function () {
  if (typeof ZONAS_DATA === 'undefined') return;

  var SERVICE_FEE = 5;
  var EVENTO_ID = ZONAS_DATA.length > 0 ? window.EVENTO_ID : null;
  var cart = [];
  var selectedZonaId = null;
  var selectedSeats = [];
  var GLOBAL_ASIENTOS_DATA = [];

  var el = {
    svgContainer: document.getElementById('svg-theater'),
    seatPanel: document.getElementById('seat-panel'),
    seatContainer: document.getElementById('seat-container'),
    seatTitle: document.getElementById('seat-panel-title'),
    seatClose: document.getElementById('seat-panel-close'),
    legend: document.getElementById('seat-legend'),
    cartItems: document.getElementById('cart-items'),
    cartEmpty: document.getElementById('cart-empty'),
    subtotalEl: document.getElementById('cart-subtotal'),
    serviceEl: document.getElementById('cart-service'),
    totalEl: document.getElementById('cart-total'),
    continueBtn: document.getElementById('btn-continuar'),
    cartCount: document.getElementById('cart-count'),
  };

  function init() {
    buildSvgMap(ZONAS_DATA);
    attachLegendClick();
    el.seatClose.addEventListener('click', closeSeatPanel);
    el.continueBtn.addEventListener('click', submitCart);
  }

  // ── Build SVG theater map ────────────────────────────────────────
  function buildSvgMap(zonas) {
    var sorted = zonas.slice().sort(function (a, b) { return (a.orden_visual || 0) - (b.orden_visual || 0); });
    var total = sorted.length;
    var W = 600, H = 480;
    var cx = W / 2, cy = H - 20;
    var minR = 55, maxR = cy - 60;
    var bandH = total > 0 ? (maxR - minR) / total : 100;
    var angleL = 200, angleR = 340;

    var svgNS = 'http://www.w3.org/2000/svg';
    var svg = document.createElementNS(svgNS, 'svg');
    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);

    // Stage
    var stage = document.createElementNS(svgNS, 'rect');
    stage.setAttribute('x', (W/2 - 140).toFixed(1));
    stage.setAttribute('y', (H - 48).toFixed(1));
    stage.setAttribute('width', '280');
    stage.setAttribute('height', '36');
    stage.setAttribute('rx', '18');
    stage.setAttribute('fill', '#d946ef');
    stage.setAttribute('opacity', '0.5');
    var stageText = document.createElementNS(svgNS, 'text');
    stageText.setAttribute('x', (W/2).toFixed(1));
    stageText.setAttribute('y', (H - 27).toFixed(1));
    stageText.setAttribute('text-anchor', 'middle');
    stageText.setAttribute('fill', 'white');
    stageText.setAttribute('font-size', '11');
    stageText.setAttribute('font-weight', '600');
    stageText.setAttribute('opacity', '0.6');
    stageText.setAttribute('letter-spacing', '3');
    stageText.textContent = 'ESCENARIO';
    svg.appendChild(stage);
    svg.appendChild(stageText);

    // Zone arcs
    sorted.forEach(function (zona, i) {
      var rI = minR + i * bandH;
      var rO = rI + bandH - 1;
      var color = zona.color || '#1E293B';

      var path = buildArcPath(cx, cy, rI, rO, angleL, angleR);
      var elPath = document.createElementNS(svgNS, 'path');
      elPath.setAttribute('d', path);
      elPath.setAttribute('fill', color);
      elPath.setAttribute('fill-opacity', '0.35');
      elPath.setAttribute('class', 'zone-arc');
      elPath.setAttribute('data-zona-id', zona.id);
      elPath.setAttribute('data-index', i);
      elPath.addEventListener('click', function () { onZoneClick(zona); });
      elPath.addEventListener('mouseenter', function () { highlightLegend(i); });
      elPath.addEventListener('mouseleave', function () { unhighlightLegend(); });
      svg.appendChild(elPath);

      // Label
      var labelR = (rI + rO) / 2;
      var labelAngle = 270;
      var lx = cx + labelR * Math.cos((labelAngle - 90) * Math.PI / 180);
      var ly = cy + labelR * Math.sin((labelAngle - 90) * Math.PI / 180);

      var txtEl = document.createElementNS(svgNS, 'text');
      txtEl.setAttribute('x', lx.toFixed(1));
      txtEl.setAttribute('y', ly.toFixed(1));
      txtEl.setAttribute('text-anchor', 'middle');
      txtEl.setAttribute('dominant-baseline', 'middle');
      txtEl.setAttribute('fill', 'white');
      txtEl.setAttribute('font-size', '12');
      txtEl.setAttribute('font-weight', '700');
      txtEl.setAttribute('class', 'zone-label');
      txtEl.setAttribute('data-index', i);
      txtEl.textContent = zona.nombre.charAt(0) + zona.nombre.slice(1).toLowerCase();

      // Glow filter
      var filter = document.createElementNS(svgNS, 'filter');
      filter.setAttribute('id', 'glow-' + i);
      var blur = document.createElementNS(svgNS, 'feGaussianBlur');
      blur.setAttribute('stdDeviation', '1.5');
      blur.setAttribute('result', 'coloredBlur');
      filter.appendChild(blur);
      var merge = document.createElementNS(svgNS, 'feMerge');
      var mn1 = document.createElementNS(svgNS, 'feMergeNode');
      mn1.setAttribute('in', 'coloredBlur');
      var mn2 = document.createElementNS(svgNS, 'feMergeNode');
      mn2.setAttribute('in', 'SourceGraphic');
      merge.appendChild(mn1);
      merge.appendChild(mn2);
      filter.appendChild(merge);
      svg.appendChild(filter);

      var txtBg = document.createElementNS(svgNS, 'rect');
      var tbbox = txtEl.getBBox ? null : { width: 80, height: 20 };
      txtBg.setAttribute('x', (lx - 35).toFixed(1));
      txtBg.setAttribute('y', (ly - 10).toFixed(1));
      txtBg.setAttribute('width', '70');
      txtBg.setAttribute('height', '20');
      txtBg.setAttribute('rx', '4');
      txtBg.setAttribute('fill', 'rgba(0,0,0,0.55)');
      txtBg.setAttribute('class', 'zone-label');
      txtBg.setAttribute('data-index', i);
      svg.appendChild(txtBg);
      svg.appendChild(txtEl);

      // Price label
      var priceEl = document.createElementNS(svgNS, 'text');
      var priceAngle = 270;
      var pR = rO + 5;
      var px = cx + pR * Math.cos((priceAngle - 90) * Math.PI / 180);
      var py = cy + pR * Math.sin((priceAngle - 90) * Math.PI / 180) + 12;
      priceEl.setAttribute('x', (W/2).toFixed(1));
      priceEl.setAttribute('y', (minR + (i+1)*bandH - bandH/2 + 14).toFixed(1));
      priceEl.setAttribute('text-anchor', 'middle');
      priceEl.setAttribute('fill', '#9CA3AF');
      priceEl.setAttribute('font-size', '10');
      priceEl.setAttribute('class', 'zone-label');
      priceEl.setAttribute('data-index', i);
      priceEl.textContent = 'Bs. ' + zona.precio;
      svg.appendChild(priceEl);
    });

    // Availability labels on right side
    sorted.forEach(function (zona, i) {
      var availEl = document.createElementNS(svgNS, 'text');
      availEl.setAttribute('x', (W - 10).toFixed(1));
      availEl.setAttribute('y', (minR + (i+0.5)*bandH + 4).toFixed(1));
      availEl.setAttribute('text-anchor', 'end');
      availEl.setAttribute('fill', zona.disponibles > 10 ? '#34D399' : zona.disponibles > 0 ? '#FBBF24' : '#EF4444');
      availEl.setAttribute('font-size', '9');
      availEl.setAttribute('class', 'zone-label');
      availEl.setAttribute('data-index', i);
      availEl.textContent = zona.disponibles + ' disp.';
      svg.appendChild(availEl);
    });

    el.svgContainer.appendChild(svg);
  }

  function buildArcPath(cx, cy, rI, rO, aL, aR) {
    function pp(angle, r) {
      var rad = (angle - 90) * Math.PI / 180;
      return (cx + r * Math.cos(rad)).toFixed(1) + ',' + (cy + r * Math.sin(rad)).toFixed(1);
    }
    return 'M ' + pp(aR, rI) +
           ' A ' + rI.toFixed(1) + ' ' + rI.toFixed(1) + ' 0 0 0 ' + pp(aL, rI) +
           ' L ' + pp(aL, rO) +
           ' A ' + rO.toFixed(1) + ' ' + rO.toFixed(1) + ' 0 0 1 ' + pp(aR, rO) + ' Z';
  }

  // ── Zone click ────────────────────────────────────────────────────
  function onZoneClick(zona) {
    selectedZonaId = zona.id;
    highlightZone(zona.id);
    openSeatPanel(zona);
  }

  function highlightZone(zonaId) {
    document.querySelectorAll('.zone-arc').forEach(function (p) {
      p.classList.toggle('active', parseInt(p.getAttribute('data-zona-id')) === zonaId);
    });
    document.querySelectorAll('.zone-legend-item').forEach(function (li) {
      li.classList.toggle('active', parseInt(li.dataset.zonaId) === zonaId);
    });
  }

  // ── Seat panel ────────────────────────────────────────────────────
  function openSeatPanel(zona) {
    el.seatTitle.innerHTML = zona.nombre_display + ' <small>Bs. ' + zona.precio + ' c/u</small>';
    el.seatPanel.classList.add('visible');
    el.seatContainer.innerHTML =
      '<div class="seat-loading"><div class="spinner"></div>Cargando mapa de asientos...</div>';
    el.legend.querySelectorAll('.legend-seat-swatch.selected').forEach(function (s) { s.style.background = '#00AEEF'; });

    fetchSeats(zona.id, zona);
  }

  function closeSeatPanel() {
    el.seatPanel.classList.remove('visible');
    selectedZonaId = null;
    document.querySelectorAll('.zone-arc').forEach(function (p) { p.classList.remove('active'); });
    document.querySelectorAll('.zone-legend-item').forEach(function (li) { li.classList.remove('active'); });
  }

  function fetchSeats(zonaId, zona) {
    if (!window.USER_LOGGED_IN) {
      el.seatContainer.innerHTML =
        '<div class="seat-loading" style="flex-direction:column;gap:0.75rem;">' +
          '<i class="fas fa-lock" style="font-size:1.5rem;color:#00AEEF;"></i>' +
          '<span>Inicia sesión para ver los asientos disponibles</span>' +
          '<button class="btn-continuar" style="width:auto;padding:0.5rem 1.5rem;font-size:0.85rem;" ' +
            'onclick="var m=new bootstrap.Modal(document.getElementById(\'authModal\'));m.show();if(window.switchAuthTab)switchAuthTab(\'login\');">' +
            'Iniciar Sesión</button>' +
        '</div>';
      return;
    }
    var url = '/api/asientos/' + EVENTO_ID + '/' + zonaId + '/';
    fetch(url)
      .then(function (r) {
        if (!r.ok) throw new Error('API error');
        return r.json();
      })
      .then(function (data) {
        GLOBAL_ASIENTOS_DATA = data.asientos || [];
        renderSeats(GLOBAL_ASIENTOS_DATA, zona);
      })
      .catch(function () {
        el.seatContainer.innerHTML = '<div class="seat-loading" style="color:#EF4444;">Error al cargar asientos</div>';
      });
  }

  function renderSeats(asientos, zona) {
    el.seatContainer.innerHTML = '';
    var filas = {};
    var maxCols = 0;
    asientos.forEach(function (a) {
      if (!filas[a.fila]) filas[a.fila] = [];
      filas[a.fila].push(a);
      if (filas[a.fila].length > maxCols) maxCols = filas[a.fila].length;
    });
    var filaKeys = Object.keys(filas).sort();

    if (filaKeys.length === 0) {
      el.seatContainer.innerHTML = '<div class="seat-loading">No hay asientos en esta zona</div>';
      return;
    }

    var SW, SH, RGAP;
    if (maxCols > 80) { SW = 9; SH = 9; RGAP = 14; }
    else if (maxCols > 50) { SW = 11; SH = 11; RGAP = 16; }
    else if (maxCols > 30) { SW = 14; SH = 14; RGAP = 20; }
    else if (maxCols > 20) { SW = 18; SH = 18; RGAP = 26; }
    else { SW = 22; SH = 22; RGAP = 30; }

    var ARC_DEG = 160;
    var ARC_RAD = ARC_DEG * Math.PI / 180;
    var a0 = 190;
    var a1 = 350;
    var R0 = Math.max(140, Math.ceil(maxCols * (SW + 2) / ARC_RAD) + 8);
    var totalFilas = filaKeys.length;
    var PAD = 30;
    var Rlast = R0 + (totalFilas - 1) * RGAP;
    var CANVAS_W = Rlast * 2 + PAD * 2 + 40;
    var arcHeight = Rlast + SH / 2;
    var stageBelow = 50;
    var CANVAS_H = arcHeight + stageBelow + PAD * 2;
    var centerX = CANVAS_W / 2;
    var centerY = PAD + arcHeight;

    var svgNS = 'http://www.w3.org/2000/svg';
    var svg = document.createElementNS(svgNS, 'svg');
    svg.setAttribute('viewBox', '0 0 ' + CANVAS_W + ' ' + CANVAS_H);
    svg.setAttribute('width', '100%');
    svg.setAttribute('height', (CANVAS_H * 1.2).toFixed(0));

    // Stage
    var stg = document.createElementNS(svgNS, 'rect');
    stg.setAttribute('x', (centerX - 80).toFixed(1));
    stg.setAttribute('y', (centerY + Rlast + 15).toFixed(1));
    stg.setAttribute('width', '160');
    stg.setAttribute('height', '24');
    stg.setAttribute('rx', '12');
    stg.setAttribute('fill', '#d946ef');
    stg.setAttribute('opacity', '0.4');
    var stgT = document.createElementNS(svgNS, 'text');
    stgT.setAttribute('x', centerX.toFixed(1));
    stgT.setAttribute('y', (centerY + Rlast + 30).toFixed(1));
    stgT.setAttribute('text-anchor', 'middle');
    stgT.setAttribute('fill', 'white');
    stgT.setAttribute('font-size', '10');
    stgT.setAttribute('opacity', '0.5');
    stgT.textContent = 'ESCENARIO';
    svg.appendChild(stg);
    svg.appendChild(stgT);

    var zoneColor = zona.color || '#00AEEF';

    filaKeys.forEach(function (fila, fi) {
      var seats = filas[fila];
      var R = R0 + fi * RGAP;
      var count = seats.length;

      // Row label left
      var lblL = document.createElementNS(svgNS, 'text');
      lblL.setAttribute('x', (centerX - R - 14).toFixed(1));
      lblL.setAttribute('y', (centerY).toFixed(1));
      lblL.setAttribute('text-anchor', 'middle');
      lblL.setAttribute('dominant-baseline', 'middle');
      lblL.setAttribute('fill', '#9CA3AF');
      lblL.setAttribute('font-size', '9');
      lblL.textContent = fila;
      svg.appendChild(lblL);

      // Row label right
      var lblR = document.createElementNS(svgNS, 'text');
      lblR.setAttribute('x', (centerX + R + 14).toFixed(1));
      lblR.setAttribute('y', (centerY).toFixed(1));
      lblR.setAttribute('text-anchor', 'middle');
      lblR.setAttribute('dominant-baseline', 'middle');
      lblR.setAttribute('fill', '#9CA3AF');
      lblR.setAttribute('font-size', '9');
      lblR.textContent = fila;
      svg.appendChild(lblR);

      seats.forEach(function (seat, si) {
        var frac = (count > 1) ? si / (count - 1) : 0.5;
        var angle = a0 + (a1 - a0) * frac;
        var rad = (angle - 90) * Math.PI / 180;
        var sx = centerX + R * Math.cos(rad);
        var sy = centerY + R * Math.sin(rad);
        var rot = angle - 90;

        var g = document.createElementNS(svgNS, 'g');
        g.setAttribute('transform', 'translate(' + sx.toFixed(1) + ',' + sy.toFixed(1) + ') rotate(' + rot.toFixed(1) + ')');

        var rect = document.createElementNS(svgNS, 'rect');
        rect.setAttribute('x', (-SW/2).toFixed(1));
        rect.setAttribute('y', (-SH/2).toFixed(1));
        rect.setAttribute('width', SW.toFixed(1));
        rect.setAttribute('height', SH.toFixed(1));
        rect.setAttribute('rx', '2');
        rect.setAttribute('data-seat-id', seat.id);
        rect.setAttribute('data-fila', seat.fila);
        rect.setAttribute('data-numero', seat.numero);

        if (seat.disponible === false || (seat.estado !== 'DISPONIBLE' && seat.estado !== undefined)) {
          rect.setAttribute('fill', '#1a1f2a');
          rect.setAttribute('opacity', '0.35');
        } else {
          rect.setAttribute('fill', '#1e293b');
          rect.setAttribute('cursor', 'pointer');
          rect.addEventListener('click', function () {
            toggleSeat(seat.id, seat.fila, seat.numero, zona);
          });
        }
        g.appendChild(rect);

        // Seat number
        var num = document.createElementNS(svgNS, 'text');
        num.setAttribute('text-anchor', 'middle');
        num.setAttribute('dominant-baseline', 'central');
        num.setAttribute('fill', seat.disponible === false ? '#374151' : '#6B7280');
        num.setAttribute('font-size', Math.max(5, SW * 0.45).toFixed(1));
        num.textContent = seat.numero;
        g.appendChild(num);

        svg.appendChild(g);
      });
    });

    el.seatContainer.appendChild(svg);

    // Restore selected seats
    restoreSeatSelection(zoneColor);
    initZoomPan(svg, CANVAS_W, CANVAS_H);
  }

  function toggleSeat(seatId, fila, numero, zona) {
    var idx = -1;
    for (var i = 0; i < selectedSeats.length; i++) {
      if (selectedSeats[i].id === seatId) { idx = i; break; }
    }
    if (idx >= 0) {
      selectedSeats.splice(idx, 1);
    } else {
      var limite = zona.limite || 4;
      var currentCount = selectedSeats.length;
      var cartCount = 0;
      for (var j = 0; j < cart.length; j++) {
        if (cart[j].zonaId === zona.id) { cartCount += cart[j].qty; }
      }
      if (currentCount + cartCount >= limite) {
        alert('Límite de ' + limite + ' asientos por zona');
        return;
      }
      selectedSeats.push({ id: seatId, fila: fila, numero: numero });
    }
    updateSeatVisuals();
    syncCartWithSelected(zona);
  }

  function updateSeatVisuals() {
    var color = '#00AEEF';
    for (var i = 0; i < ZONAS_DATA.length; i++) {
      if (ZONAS_DATA[i].id === selectedZonaId) { color = ZONAS_DATA[i].color || '#00AEEF'; break; }
    }
    el.seatContainer.querySelectorAll('rect[data-seat-id]').forEach(function (r) {
      var sid = parseInt(r.getAttribute('data-seat-id'));
      var isSelected = false;
      for (var j = 0; j < selectedSeats.length; j++) {
        if (selectedSeats[j].id === sid) { isSelected = true; break; }
      }
      if (isSelected) {
        r.setAttribute('fill', color);
        r.setAttribute('opacity', '1');
      } else if (r.getAttribute('cursor') === 'pointer') {
        r.setAttribute('fill', '#1e293b');
        r.setAttribute('opacity', '1');
      }
    });
  }

  function restoreSeatSelection(zoneColor) {
    el.seatContainer.querySelectorAll('rect[data-seat-id]').forEach(function (r) {
      var sid = parseInt(r.getAttribute('data-seat-id'));
      var selected = false;
      for (var j = 0; j < selectedSeats.length; j++) {
        if (selectedSeats[j].id === sid) { selected = true; break; }
      }
      if (selected) {
        r.setAttribute('fill', zoneColor);
        r.setAttribute('opacity', '1');
      }
    });
  }

  function syncCartWithSelected(zona) {
    cart = [];
    if (selectedSeats.length > 0) {
      cart.push({
        zonaId: zona.id,
        zone: zona.nombre,
        price: zona.precio,
        qty: selectedSeats.length,
        asiento_ids: selectedSeats.map(function (s) { return s.id; }),
        asientos_info: selectedSeats.map(function (s) { return 'F ' + s.fila + '-' + s.numero; }),
      });
    }
    renderCart();
  }

  // ── Cart ──────────────────────────────────────────────────────────
  function renderCart() {
    var subtotal = 0;
    var totalItems = 0;
    el.cartItems.innerHTML = '';

    cart.forEach(function (item) {
      var subt = item.price * item.qty;
      subtotal += subt;
      totalItems += item.qty;
      var div = document.createElement('div');
      div.className = 'cart-item';
      div.innerHTML =
        '<div class="cart-item-info">' +
          '<div class="cart-item-name">' + item.zone + '</div>' +
          '<div class="cart-item-detail">' + (item.asientos_info ? item.asientos_info.join(', ') : item.qty + ' entrada(s)') + '</div>' +
        '</div>' +
        '<div class="cart-item-price">Bs. ' + subt + '</div>' +
        '<button class="cart-item-remove" data-zone="' + item.zonaId + '"><i class="fas fa-times"></i></button>';
      div.querySelector('.cart-item-remove').addEventListener('click', function () {
        clearZoneSelection(item.zonaId);
      });
      el.cartItems.appendChild(div);
    });

    if (cart.length === 0) {
      el.cartEmpty.style.display = 'block';
    } else {
      el.cartEmpty.style.display = 'none';
    }

    var service = totalItems > 0 ? SERVICE_FEE : 0;
    var total = subtotal + service;
    el.subtotalEl.textContent = 'Bs. ' + subtotal;
    el.serviceEl.textContent = 'Bs. ' + service;
    el.totalEl.textContent = 'Bs. ' + total;
    el.continueBtn.disabled = cart.length === 0;
    el.cartCount.textContent = totalItems;
  }

  function clearZoneSelection(zonaId) {
    if (zonaId === selectedZonaId) {
      selectedSeats = [];
      updateSeatVisuals();
    }
    cart = [];
    renderCart();
  }

  function submitCart() {
    if (cart.length === 0) return;

    if (!window.USER_LOGGED_IN) {
      var modal = new bootstrap.Modal(document.getElementById('authModal'));
      if (modal) modal.show();
      if (window.switchAuthTab) switchAuthTab('login');
      return;
    }

    var carritoPayload = [];
    cart.forEach(function (item) {
      carritoPayload.push({
        zona_id: item.zonaId,
        qty: item.qty,
        asiento_ids: item.asiento_ids || [],
      });
    });

    var form = document.createElement('form');
    form.method = 'POST';
    form.action = '/comprar-entrada/' + EVENTO_ID + '/finalizar/';
    form.style.display = 'none';

    var csrfInp = document.createElement('input');
    csrfInp.type = 'hidden'; csrfInp.name = 'csrfmiddlewaretoken'; csrfInp.value = window.CSRF_TOKEN;
    form.appendChild(csrfInp);

    var jsonInp = document.createElement('input');
    jsonInp.type = 'hidden'; jsonInp.name = 'carrito_json'; jsonInp.value = JSON.stringify(carritoPayload);
    form.appendChild(jsonInp);

    document.body.appendChild(form);
    form.submit();
  }

  // ── Legend click ──────────────────────────────────────────────────
  function attachLegendClick() {
    document.querySelectorAll('.zone-legend-item').forEach(function (li) {
      li.addEventListener('click', function () {
        var zonaId = parseInt(this.dataset.zonaId);
        for (var i = 0; i < ZONAS_DATA.length; i++) {
          if (ZONAS_DATA[i].id === zonaId) {
            onZoneClick(ZONAS_DATA[i]);
            break;
          }
        }
      });
    });
  }

  function highlightLegend(index) {
    document.querySelectorAll('.zone-legend-item').forEach(function (li, i) {
      li.style.opacity = i === index ? '1' : '0.5';
    });
  }

  function unhighlightLegend() {
    document.querySelectorAll('.zone-legend-item').forEach(function (li) {
      li.style.opacity = '1';
    });
  }

  // ── Zoom & Pan ────────────────────────────────────────────────────
  var zoomState = { scale: 1, tx: 0, ty: 0, isPanning: false, startX: 0, startY: 0 };

  function initZoomPan(svg, cw, ch) {
    var container = el.seatContainer;

    container.addEventListener('wheel', function (e) {
      e.preventDefault();
      var delta = e.deltaY > 0 ? -0.1 : 0.1;
      zoomState.scale = Math.max(0.3, Math.min(3, zoomState.scale + delta));
      applyZoom(svg);
    });

    container.addEventListener('mousedown', function (e) {
      if (e.target.tagName === 'rect' || e.target.tagName === 'text') return;
      zoomState.isPanning = true;
      zoomState.startX = e.clientX - zoomState.tx;
      zoomState.startY = e.clientY - zoomState.ty;
    });

    document.addEventListener('mousemove', function (e) {
      if (!zoomState.isPanning) return;
      zoomState.tx = e.clientX - zoomState.startX;
      zoomState.ty = e.clientY - zoomState.startY;
      applyZoom(svg);
    });

    document.addEventListener('mouseup', function () {
      zoomState.isPanning = false;
    });

    container.addEventListener('dblclick', function () {
      zoomState.scale = 1; zoomState.tx = 0; zoomState.ty = 0;
      applyZoom(svg);
    });
  }

  function applyZoom(svg) {
    var s = zoomState.scale;
    var tx = zoomState.tx;
    var ty = zoomState.ty;
    svg.style.transform = 'translate(' + tx + 'px, ' + ty + 'px) scale(' + s + ')';
    svg.style.transformOrigin = 'center center';
  }

  init();
});
