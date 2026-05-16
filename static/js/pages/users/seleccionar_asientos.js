
/**
 * seleccionar_asientos.js  v5
 * Mapa de asientos en arco SVG + zoom/pan.
 * Globals: EVENTO_ID, EVENTO_ZONA_ID, ZONA_COLOR,
 *          PRECIO_UNIT, LIMITE, ASIENTOS_DATA, CSRF_TOKEN
 */
(function () {
  'use strict';

  var selectedIds  = [];
  var selectedMeta = [];
  var lastSelected = null;
  var SERVICE_FEE  = 5;

  /* ── Polyfill roundRect ──────────────────────────────────────── */
  if (!CanvasRenderingContext2D.prototype.roundRect) {
    CanvasRenderingContext2D.prototype.roundRect = function (x, y, w, h, r) {
      r = Math.min(r, w / 2, h / 2);
      this.beginPath();
      this.moveTo(x + r, y); this.lineTo(x + w - r, y);
      this.quadraticCurveTo(x + w, y, x + w, y + r);
      this.lineTo(x + w, y + h - r);
      this.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
      this.lineTo(x + r, y + h);
      this.quadraticCurveTo(x, y + h, x, y + h - r);
      this.lineTo(x, y + r);
      this.quadraticCurveTo(x, y, x + r, y);
      this.closePath();
    };
  }

  document.addEventListener('DOMContentLoaded', function () {
    initTimer();
    buildCurvedMap();
    initContinueBtn();
    draw3DStage(null);
  });

  /* ── Timer ───────────────────────────────────────────────────── */
  function initTimer() {
    var el = document.getElementById('countdown');
    if (!el) return;
    var key = 'purchaseDeadline_' + EVENTO_ID;
    if (!localStorage.getItem(key))
      localStorage.setItem(key, String(Date.now() + 15 * 60 * 1000));
    function tick() {
      var diff = Math.max(0, Number(localStorage.getItem(key) || 0) - Date.now());
      var m = Math.floor(diff / 60000), s = Math.floor((diff % 60000) / 1000);
      el.textContent = m + ':' + (s < 10 ? '0' : '') + s;
      if (diff === 0) {
        localStorage.removeItem(key);
        var b = document.getElementById('timer-container');
        if (b) { b.style.background = 'rgba(239,68,68,.15)'; b.style.borderColor = 'rgba(239,68,68,.4)'; }
        el.style.color = '#ef4444'; el.textContent = 'Expirado';
        setTimeout(function () { window.location.href = '/comprar-entrada/' + EVENTO_ID + '/'; }, 2000);
      }
    }
    tick(); setInterval(tick, 1000);
  }

  /* ══════════════════════════════════════════════════════════════
     MAPA SVG
     ─────────────────────────────────────────────────────────────
     GEOMETRÍA:
       • CX, CY = centro polar (donde está el escenario)
       • El arco usa ángulos a0..a1 que producen la media luna
         con los asientos ENCIMA del escenario (y < CY)
       • El viewBox inicial se calcula para mostrar exactamente
         el bounding-box del contenido, centrado en el contenedor
  ══════════════════════════════════════════════════════════════ */
  function buildCurvedMap() {
    var container = document.getElementById('curved-map-container');
    if (!container) return;

    /* 1. Agrupar filas */
    var filas = {};
    ASIENTOS_DATA.forEach(function (a) {
      if (!filas[a.fila]) filas[a.fila] = [];
      filas[a.fila].push(a);
    });
    var filaKeys   = Object.keys(filas).sort();
    var totalFilas = filaKeys.length;
    var maxCols    = 0;
    filaKeys.forEach(function (f) { maxCols = Math.max(maxCols, filas[f].length); });

    /* 2. Tamaño adaptativo */
    var SW = 22, SH = 22, RGAP = 30;
    if      (maxCols > 80) { SW = 11; SH = 11; RGAP = 16; }
    else if (maxCols > 50) { SW = 14; SH = 14; RGAP = 20; }
    else if (maxCols > 30) { SW = 17; SH = 17; RGAP = 24; }

    /* 3. Geometría del arco
         Ángulos medidos desde eje X positivo (sentido antihorario):
           a0 = PI + ARC/2  → extremo izquierdo  (arriba-izquierda)
           a1 = -ARC/2      → extremo derecho     (arriba-derecha)
         Con CY en la parte INFERIOR del canvas SVG, los puntos
         del arco tienen y < CY (están ENCIMA del escenario). ✓
    */
    var ARC_DEG = 160;
    var ARC_RAD = (ARC_DEG * Math.PI) / 180;
    // Arco centrado en 270° (= -PI/2 = apunta hacia ARRIBA en SVG donde Y crece hacia abajo)
    // a0 = 270° - 80° = 190°  (extremo izquierdo)
    // a1 = 270° + 80° = 350°  (extremo derecho)
    // Ambos en el mismo rango [0, 2PI] → la interpolación t∈[0,1] produce el arco correcto
    var BASE_ANG = 3 * Math.PI / 2;          // 270° en radianes
    var a0 = BASE_ANG - ARC_RAD / 2;        // ≈ 190° → extremo izquierdo
    var a1 = BASE_ANG + ARC_RAD / 2;        // ≈ 350° → extremo derecho

    /* Radio mínimo para que los asientos no se solapen */
    var R0    = Math.max(140, Math.ceil((maxCols * (SW + 2)) / ARC_RAD) + 8);
    var Rlast = R0 + (totalFilas - 1) * RGAP;

    /* 4. Bounding-box del contenido
         Con a0=190°, a1=350°, centro en 270° (arriba):
           - Punto más alto: ángulo 270° → y = CY - Rlast  (tope del arco)
           - Puntos laterales: ángulos 190° y 350° → x = CX ± Rlast·|cos(80°)|
           - El arco NO baja por debajo de CY (todos los ángulos tienen sin < 0 en SVG)
             excepto los extremos que tienen sin(190°) = sin(350°) ≈ -0.17 (ligeramente)
         Usamos Rlast como radio máximo para el ancho, y Rlast para la altura del arco.
    */
    var PAD       = 32;
    var STAGE_H   = 44;
    var STAGE_GAP = 10;

    var CANVAS_W = Rlast * 2 + PAD * 2 + 40;
    var arcHeight  = Rlast + SH / 2;
    var stageBelow = STAGE_GAP + STAGE_H;
    var CANVAS_H   = arcHeight + stageBelow + PAD * 2;

    var CX = CANVAS_W / 2;
    var CY = PAD + arcHeight;

    /* 5. Crear SVG — viewBox = todo el canvas */
    var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox',
      '0 0 ' + CANVAS_W.toFixed(1) + ' ' + CANVAS_H.toFixed(1));
    svg.setAttribute('width',  '100%');
    svg.setAttribute('height', '100%');
    svg.style.display  = 'block';
    svg.style.overflow = 'visible';
    svg.style.cursor   = 'grab';

    /* 6. Escenario */
    var stW = Math.min(260, R0 * 0.8), stH = 36;
    var stX = CX - stW / 2, stY = CY + STAGE_GAP;
    var stG = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    var stR = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    stR.setAttribute('x', stX.toFixed(1)); stR.setAttribute('y', stY.toFixed(1));
    stR.setAttribute('width', stW.toFixed(1)); stR.setAttribute('height', stH);
    stR.setAttribute('rx', stH / 2);
    stR.setAttribute('fill', 'rgba(217,70,239,.18)');
    stR.setAttribute('stroke', 'rgba(217,70,239,.65)');
    stR.setAttribute('stroke-width', '1.5');
    stG.appendChild(stR);
    var stT = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    stT.setAttribute('x', CX.toFixed(1));
    stT.setAttribute('y', (stY + stH / 2 + 5).toFixed(1));
    stT.setAttribute('text-anchor', 'middle');
    stT.setAttribute('fill', '#e879f9');
    stT.setAttribute('font-size', '13');
    stT.setAttribute('font-weight', '800');
    stT.setAttribute('font-family', 'Inter, sans-serif');
    stT.setAttribute('letter-spacing', '3');
    stT.style.pointerEvents = 'none';
    stT.textContent = '★  ESCENARIO  ★';
    stG.appendChild(stT);
    svg.appendChild(stG);

    /* 7. Filas de asientos */
    var seatElements = {};

    filaKeys.forEach(function (fila, rowIdx) {
      var asientos = filas[fila].sort(function (a, b) { return a.numero - b.numero; });
      var N = asientos.length;
      var R = R0 + rowIdx * RGAP;
      var g = document.createElementNS('http://www.w3.org/2000/svg', 'g');

      /* Etiquetas de fila */
      function makeLabel(ang, anchor) {
        var lx = CX + (R + SW + 4) * Math.cos(ang);
        var ly = CY + (R + SW + 4) * Math.sin(ang);
        var t  = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        t.setAttribute('x', lx.toFixed(1));
        t.setAttribute('y', (ly + 4).toFixed(1));
        t.setAttribute('text-anchor', anchor);
        t.setAttribute('fill', '#6b7280');
        t.setAttribute('font-size', '11');
        t.setAttribute('font-weight', '700');
        t.setAttribute('font-family', 'Inter, sans-serif');
        t.style.pointerEvents = 'none';
        t.textContent = fila;
        return t;
      }
      g.appendChild(makeLabel(a0 - 0.04, 'end'));
      g.appendChild(makeLabel(a1 + 0.04, 'start'));

      /* Asientos */
      asientos.forEach(function (a, colIdx) {
        var t   = N > 1 ? colIdx / (N - 1) : 0.5;
        var ang = a0 + t * (a1 - a0);
        var ax  = CX + R * Math.cos(ang);
        var ay  = CY + R * Math.sin(ang);
        var rotDeg = (ang * 180 / Math.PI) + 90;

        var sg = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        sg.setAttribute('transform',
          'translate(' + ax.toFixed(2) + ',' + ay.toFixed(2) + ')' +
          ' rotate(' + rotDeg.toFixed(2) + ')');

        var rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', (-SW / 2).toFixed(1));
        rect.setAttribute('y', (-SH / 2).toFixed(1));
        rect.setAttribute('width', SW); rect.setAttribute('height', SH);
        rect.setAttribute('rx', '4');

        var isOcc = a.estado !== 'DISPONIBLE';
        if (isOcc) {
          rect.setAttribute('fill', '#1a1f2a');
          rect.setAttribute('stroke', 'rgba(255,255,255,.06)');
          rect.setAttribute('stroke-width', '1');
          rect.style.cursor = 'not-allowed';
          rect.style.opacity = '0.4';
        } else {
          rect.setAttribute('fill', '#1e293b');
          rect.setAttribute('stroke', 'rgba(255,255,255,.22)');
          rect.setAttribute('stroke-width', '1.5');
          rect.style.cursor = 'pointer';
        }

        var txt = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        txt.setAttribute('x', '0'); txt.setAttribute('y', '4');
        txt.setAttribute('text-anchor', 'middle');
        txt.setAttribute('font-size', SW > 15 ? '8' : '6');
        txt.setAttribute('font-weight', '700');
        txt.setAttribute('font-family', 'Inter, sans-serif');
        txt.setAttribute('fill', isOcc ? 'rgba(255,255,255,.12)' : 'rgba(255,255,255,.5)');
        txt.setAttribute('transform', 'rotate(' + (-rotDeg).toFixed(2) + ')');
        txt.style.pointerEvents = 'none';
        txt.textContent = a.numero;

        sg.appendChild(rect); sg.appendChild(txt);
        g.appendChild(sg);
        seatElements[a.id] = { rect: rect, txt: txt, occupied: isOcc };

        if (!isOcc) {
          rect.addEventListener('mouseenter', function () {
            if (selectedIds.indexOf(a.id) === -1) {
              rect.setAttribute('fill', '#2d3f55');
              rect.setAttribute('stroke', 'rgba(255,255,255,.65)');
              txt.setAttribute('fill', 'rgba(255,255,255,.9)');
            }
          });
          rect.addEventListener('mouseleave', function () {
            if (selectedIds.indexOf(a.id) === -1) {
              rect.setAttribute('fill', '#1e293b');
              rect.setAttribute('stroke', 'rgba(255,255,255,.22)');
              txt.setAttribute('fill', 'rgba(255,255,255,.5)');
            }
          });
          rect.addEventListener('click', function (e) {
            e.stopPropagation();
            toggleSeat(a.id, a.fila, a.numero, seatElements[a.id]);
          });
        }
      });

      svg.appendChild(g);
    });

    /* 8. Montar */
    container.innerHTML = '';
    container.appendChild(svg);
    window._seatElements = seatElements;

    /* 9. Zoom + Pan */
    initZoomPan(svg, CANVAS_W, CANVAS_H);
  }

  /* ══════════════════════════════════════════════════════════════
     ZOOM + PAN
     El viewBox inicial ya muestra TODO el contenido (0 0 W H).
     Al hacer zoom, el clamp garantiza que nunca se salga del
     bounding-box del contenido + un margen pequeño.
  ══════════════════════════════════════════════════════════════ */
  function initZoomPan(svg, CW, CH) {
    var vx = 0, vy = 0, vw = CW, vh = CH;
    var MIN_VW = CW / 10;
    var MAX_VW = CW;

    /* Sin clamp de posición — el usuario puede moverse libremente
       para alcanzar cualquier asiento. Solo limitamos el zoom. */
    function apply() {
      svg.setAttribute('viewBox',
        vx.toFixed(2) + ' ' + vy.toFixed(2) + ' ' +
        vw.toFixed(2) + ' ' + vh.toFixed(2));
    }

    function zoomAt(svgX, svgY, factor) {
      var newW  = Math.max(MIN_VW, Math.min(MAX_VW, vw * factor));
      var scale = newW / vw;
      vx = svgX - (svgX - vx) * scale;
      vy = svgY - (svgY - vy) * scale;
      vw = newW;
      vh = CH * (vw / CW);
      apply();
    }

    function toSVG(ex, ey) {
      var r = svg.getBoundingClientRect();
      return {
        x: vx + (ex - r.left) / r.width  * vw,
        y: vy + (ey - r.top)  / r.height * vh
      };
    }

    svg.addEventListener('wheel', function (e) {
      e.preventDefault();
      var pt = toSVG(e.clientX, e.clientY);
      zoomAt(pt.x, pt.y, e.deltaY < 0 ? 0.75 : 1.33);
    }, { passive: false });

    /* Drag */
    var drag = false, dx0, dy0, vx0, vy0;
    svg.addEventListener('mousedown', function (e) {
      if (e.button !== 0) return;
      drag = true; dx0 = e.clientX; dy0 = e.clientY; vx0 = vx; vy0 = vy;
      svg.style.cursor = 'grabbing'; e.preventDefault();
    });
    window.addEventListener('mousemove', function (e) {
      if (!drag) return;
      var r = svg.getBoundingClientRect();
      vx = vx0 - (e.clientX - dx0) / r.width  * vw;
      vy = vy0 - (e.clientY - dy0) / r.height * vh;
      apply();
    });
    window.addEventListener('mouseup', function () {
      if (!drag) return; drag = false; svg.style.cursor = 'grab';
    });

    /* Touch */
    var lt = null;
    svg.addEventListener('touchstart',  function (e) { lt = e.touches; }, { passive: true });
    svg.addEventListener('touchmove', function (e) {
      e.preventDefault(); if (!lt) return;
      if (e.touches.length === 1 && lt.length === 1) {
        var r = svg.getBoundingClientRect();
        vx -= (e.touches[0].clientX - lt[0].clientX) / r.width  * vw;
        vy -= (e.touches[0].clientY - lt[0].clientY) / r.height * vh;
        apply();
      } else if (e.touches.length === 2 && lt.length === 2) {
        var d0 = Math.hypot(lt[0].clientX - lt[1].clientX, lt[0].clientY - lt[1].clientY);
        var d1 = Math.hypot(e.touches[0].clientX - e.touches[1].clientX, e.touches[0].clientY - e.touches[1].clientY);
        var mx = (e.touches[0].clientX + e.touches[1].clientX) / 2;
        var my = (e.touches[0].clientY + e.touches[1].clientY) / 2;
        var pt = toSVG(mx, my); zoomAt(pt.x, pt.y, d0 / d1);
      }
      lt = e.touches;
    }, { passive: false });
    svg.addEventListener('touchend', function (e) { lt = e.touches; }, { passive: true });

    /* Doble clic → reset */
    svg.addEventListener('dblclick', function () {
      vx = 0; vy = 0; vw = CW; vh = CH; apply();
    });

    /* Botones UI */
    var bi = document.getElementById('btn-zoom-in');
    var bo = document.getElementById('btn-zoom-out');
    var br = document.getElementById('btn-zoom-reset');
    if (bi) bi.addEventListener('click', function () { zoomAt(vx + vw / 2, vy + vh / 2, 0.65); });
    if (bo) bo.addEventListener('click', function () { zoomAt(vx + vw / 2, vy + vh / 2, 1.55); });
    if (br) br.addEventListener('click', function () { vx = 0; vy = 0; vw = CW; vh = CH; apply(); });
  }

  /* ── Visual asiento ──────────────────────────────────────────── */
  function setSeatVisual(el, sel) {
    if (!el || el.occupied) return;
    if (sel) {
      el.rect.setAttribute('fill',   ZONA_COLOR || '#00AEEF');
      el.rect.setAttribute('stroke', ZONA_COLOR || '#00AEEF');
      el.txt.setAttribute('fill',    'white');
    } else {
      el.rect.setAttribute('fill',   '#1e293b');
      el.rect.setAttribute('stroke', 'rgba(255,255,255,.22)');
      el.txt.setAttribute('fill',    'rgba(255,255,255,.5)');
    }
  }

  /* ── Toggle ──────────────────────────────────────────────────── */
  function toggleSeat(id, fila, numero, el) {
    var idx = selectedIds.indexOf(id);
    if (idx !== -1) {
      selectedIds.splice(idx, 1); selectedMeta.splice(idx, 1);
      setSeatVisual(el, false);
      if (lastSelected && lastSelected.id === id)
        lastSelected = selectedMeta.length ? selectedMeta[selectedMeta.length - 1] : null;
    } else {
      if (selectedIds.length >= LIMITE) {
        showToast('Máximo ' + LIMITE + ' asientos por compra.');
        return;
      }
      selectedIds.push(id);
      selectedMeta.push({ id: id, fila: fila, numero: numero });
      setSeatVisual(el, true);
      lastSelected = { id: id, fila: fila, numero: numero };
    }
    updateSidebar(); draw3DStage(lastSelected);
  }

  /* ── Sidebar ─────────────────────────────────────────────────── */
  function updateSidebar() {
    var listEl = document.getElementById('selected-seats-list');
    var btnC   = document.getElementById('btn-continue-payment');
    if (!listEl) return;
    if (selectedMeta.length === 0) {
      listEl.innerHTML = '<p class="text-center text-gray-500 text-sm py-3">No has seleccionado asientos aún</p>';
      if (btnC) btnC.disabled = true;
    } else {
      var h = '<div style="display:flex;flex-wrap:wrap;gap:.25rem;padding:.25rem 0;">';
      selectedMeta.forEach(function (s) {
        h += '<span class="seat-chip"><i class="fas fa-chair" style="font-size:.65rem;"></i>F' +
          s.fila + '-' + s.numero +
          '<button class="seat-chip-remove" data-id="' + s.id + '">' +
          '<i class="fas fa-times" style="font-size:.6rem;"></i></button></span>';
      });
      h += '</div>';
      listEl.innerHTML = h;
      listEl.querySelectorAll('.seat-chip-remove').forEach(function (b) {
        b.addEventListener('click', function () { removeSeatById(Number(b.dataset.id)); });
      });
      if (btnC) btnC.disabled = false;
    }
    var sub = selectedMeta.length * PRECIO_UNIT, svc = sub > 0 ? SERVICE_FEE : 0;
    setText('subtotal-val', 'Bs. ' + sub.toFixed(2));
    setText('service-val',  'Bs. ' + svc.toFixed(2));
    setText('total-val',    'Bs. ' + (sub + svc).toFixed(2));
  }

  function removeSeatById(sid) {
    var idx = selectedIds.indexOf(sid); if (idx === -1) return;
    selectedIds.splice(idx, 1); selectedMeta.splice(idx, 1);
    var el = window._seatElements && window._seatElements[sid];
    if (el) setSeatVisual(el, false);
    lastSelected = selectedMeta.length ? selectedMeta[selectedMeta.length - 1] : null;
    updateSidebar(); draw3DStage(lastSelected);
  }

  function setText(id, v) { var e = document.getElementById(id); if (e) e.textContent = v; }

  /* ── Botón continuar ─────────────────────────────────────────── */
  function initContinueBtn() {
    var btn = document.getElementById('btn-continue-payment');
    if (!btn) return;
    btn.addEventListener('click', function () {
      if (!selectedIds.length) return;
      var c = [{ zona_id: EVENTO_ZONA_ID, asiento_ids: selectedIds.slice(), qty: selectedIds.length }];
      var f = document.getElementById('seats-form');
      var i = document.getElementById('hidden-carrito-json');
      if (i) i.value = JSON.stringify(c);
      if (f) f.submit();
    });
  }

  /* ── Vista 3D ────────────────────────────────────────────────── */
  function draw3DStage(seat) {
    var canvas = document.getElementById('stage3d');
    var overlay = document.getElementById('stage3d-overlay');
    var hint    = document.getElementById('preview-hint');
    if (!canvas) return;
    var ctx = canvas.getContext('2d'), W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);
    if (!seat) {
      if (overlay) overlay.classList.remove('hidden');
      if (hint) hint.textContent = 'Selecciona un asiento para ver la perspectiva';
      return;
    }
    if (overlay) overlay.classList.add('hidden');

    var filas = {};
    ASIENTOS_DATA.forEach(function (a) { if (!filas[a.fila]) filas[a.fila] = []; filas[a.fila].push(a); });
    var fk = Object.keys(filas).sort(), tf = fk.length;
    var ri = fk.indexOf(String(seat.fila));
    var ra = (filas[seat.fila] || []).sort(function (a, b) { return a.numero - b.numero; });
    var tc = ra.length, ci = ra.findIndex(function (a) { return a.id === seat.id; });
    var nx = tc > 1 ? ci / (tc - 1) : 0.5, ny = tf > 1 ? ri / (tf - 1) : 0.5;
    var df = 1 - ny * 0.55;

    var bg = ctx.createLinearGradient(0, 0, 0, H);
    bg.addColorStop(0, '#060a10'); bg.addColorStop(1, '#0d1520');
    ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);
    ctx.fillStyle = 'rgba(255,255,255,.6)';
    [[40,20],[80,35],[130,15],[200,28],[270,12],[340,30],[390,18],[450,25],[520,10],[570,35],
     [60,55],[150,48],[230,60],[310,42],[420,52],[500,45],[550,58]].forEach(function (s) {
      ctx.beginPath(); ctx.arc(s[0], s[1], .8, 0, Math.PI * 2); ctx.fill();
    });
    var fy = H * 0.72;
    var fg = ctx.createLinearGradient(0, fy, 0, H);
    fg.addColorStop(0, '#0a1018'); fg.addColorStop(1, '#060a0e');
    ctx.fillStyle = fg; ctx.fillRect(0, fy, W, H - fy);
    var ox = (nx - 0.5) * W * 0.35, sw = W * 0.55 * df, sh = H * 0.22 * df;
    var scx = W / 2 + ox, sy = fy - sh * 0.3;
    var sL = scx - sw / 2, sR = scx + sw / 2, sT = sy - sh, sB = sy;
    ctx.shadowColor = 'rgba(217,70,239,.5)'; ctx.shadowBlur = 30;
    var sg = ctx.createLinearGradient(sL, sT, sR, sB);
    sg.addColorStop(0, '#1a0a2e'); sg.addColorStop(.5, '#2d1060'); sg.addColorStop(1, '#1a0a2e');
    ctx.fillStyle = sg;
    ctx.beginPath(); ctx.moveTo(sL, sB); ctx.lineTo(sR, sB);
    ctx.lineTo(sR + sw * .06, sT); ctx.lineTo(sL - sw * .06, sT); ctx.closePath(); ctx.fill();
    ctx.shadowBlur = 0;
    ctx.strokeStyle = 'rgba(217,70,239,.8)'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(sL - sw * .06, sT); ctx.lineTo(sR + sw * .06, sT); ctx.stroke();
    var nl = Math.round(5 * df) + 2;
    for (var i = 0; i < nl; i++) {
      var lx = sL - sw * .06 + (sR - sL + sw * .12) * (i / (nl - 1)), ly = sT - 2;
      var cg = ctx.createRadialGradient(lx, ly, 0, lx, ly + sh * 1.5, sh * 1.5);
      cg.addColorStop(0, 'rgba(255,240,180,.18)'); cg.addColorStop(.5, 'rgba(255,220,100,.06)'); cg.addColorStop(1, 'rgba(255,200,50,0)');
      ctx.fillStyle = cg; ctx.beginPath(); ctx.moveTo(lx, ly);
      ctx.lineTo(lx - sw * .08, sB + sh * .5); ctx.lineTo(lx + sw * .08, sB + sh * .5); ctx.closePath(); ctx.fill();
      ctx.fillStyle = 'rgba(255,240,180,.9)'; ctx.beginPath(); ctx.arc(lx, ly, 3 * df, 0, Math.PI * 2); ctx.fill();
    }
    ctx.font = 'bold ' + Math.round(11 * df) + 'px Inter,sans-serif';
    ctx.fillStyle = 'rgba(232,121,249,.7)'; ctx.textAlign = 'center';
    ctx.fillText('ESCENARIO', scx, sT + sh * .55);
    if (ri > 0) {
      var nfr = Math.min(ri, 4);
      for (var r = 0; r < nfr; r++) {
        var rf = 1 - (r / nfr) * .4, ry = fy + H * .04 + r * H * .055;
        var rw = W * .7 * rf, rcx = W / 2 + ox * .3, ns = Math.round(8 * rf);
        var sw2 = Math.max(6, rw / ns * .6), sh2 = sw2 * .8;
        for (var s = 0; s < ns; s++) {
          var sx = rcx - rw / 2 + (rw / (ns - 1)) * s;
          ctx.fillStyle = 'rgba(30,41,59,.8)';
          ctx.beginPath(); ctx.roundRect(sx - sw2 / 2, ry, sw2, sh2, 2); ctx.fill();
          ctx.strokeStyle = 'rgba(255,255,255,.1)'; ctx.lineWidth = .5; ctx.stroke();
        }
      }
    }
    var mx = W / 2 + ox * .1, my = H - 18;
    ctx.fillStyle = ZONA_COLOR || '#00AEEF';
    ctx.beginPath(); ctx.roundRect(mx - 28, my - 14, 56, 14, 4); ctx.fill();
    ctx.font = 'bold 9px Inter,sans-serif'; ctx.fillStyle = 'white'; ctx.textAlign = 'center';
    ctx.fillText('F' + seat.fila + '-' + seat.numero, mx, my - 4);
    if (hint) hint.textContent = 'Vista desde Fila ' + seat.fila + ', Asiento ' + seat.numero;
  }

  /* ── Toast ───────────────────────────────────────────────────── */
  function showToast(msg) {
    var ex = document.getElementById('seat-toast'); if (ex) ex.remove();
    var t = document.createElement('div'); t.id = 'seat-toast';
    t.style.cssText = 'position:fixed;bottom:1.5rem;left:50%;transform:translateX(-50%);' +
      'background:#92400e;color:white;padding:.65rem 1.25rem;border-radius:.75rem;' +
      'font-size:.85rem;font-weight:600;z-index:9999;box-shadow:0 8px 24px rgba(0,0,0,.4);transition:opacity .3s;';
    t.textContent = msg; document.body.appendChild(t);
    setTimeout(function () { t.style.opacity = '0'; setTimeout(function () { t.remove(); }, 300); }, 2500);
  }

})();
