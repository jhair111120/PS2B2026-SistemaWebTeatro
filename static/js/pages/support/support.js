let currentTicketId = null;
let activeFilterStatus = 'all';
let chatInterval = null;
let btnToLoad = null;

setInterval(refreshInboxEnVivo, 5000);

function refreshInboxEnVivo() {
  fetch('/soporte/api/tickets/')
    .then(response => response.json())
    .then(data => {
      if (data.tickets) {
        const listContainer = document.getElementById('ticketList');
        const currentCards = listContainer.querySelectorAll('.ticket-chat-card');
        const currentTotal = currentCards.length;
        let needsUpdate = false;

        if (currentTotal !== data.tickets.length) {
          needsUpdate = true;
        } else if (currentTotal > 0 && data.tickets.length > 0) {
          const firstCardId = currentCards[0].getAttribute('data-ticket-id');
          if (firstCardId != data.tickets[0].id) {
            needsUpdate = true;
          }
        }

        if (needsUpdate) {
          let htmlContenido = '';
          data.tickets.forEach(t => {
            const status = t.is_closed ? 'read' : 'unread';
            const activeClass = (currentTicketId == t.id) ? 'active' : '';
            const displayDot = (!t.is_closed) ? 'block' : 'none';
            const isClosedStr = t.is_closed ? 'true' : 'false';

            const statusBadgeHtml = t.is_closed
              ? '<span class="status-badge-mini badge-cerrado">Cerrado</span>'
              : '<span class="status-badge-mini badge-abierto">Abierto</span>';

            htmlContenido += `
                        <a href="#" class="ticket-chat-card ${activeClass}" id="card-${t.id}" data-ticket-id="${t.id}" data-status="${status}" data-is-closed="${isClosedStr}" onclick="loadTicket('${t.id}', event)">
                            <div class="user-initials">
                                ${t.inicial}
                                <span class="unread-dot" style="display: ${displayDot};"></span> 
                            </div>
                            <div class="w-100 overflow-hidden">
                                <div class="d-flex justify-content-between align-items-center mb-1">
                                    <div class="fw-bold text-white text-truncate" style="font-size: 0.95rem; max-width: 55%;">${t.nombre}</div>
                                    <div class="d-flex align-items-center gap-2">
                                        ${statusBadgeHtml}
                                        <div class="small text-gray-custom" style="font-size: 0.7rem;">${t.fecha_formateada}</div>
                                    </div>
                                </div>
                                <div class="small text-cyan fw-bold text-truncate mb-1" style="font-size: 0.8rem;">Asunto: ${t.asunto}</div>
                                <div class="small text-gray-custom text-truncate" style="font-size: 0.75rem;">${t.correo}</div>
                            </div>
                        </a>
                        `;
          });

          listContainer.innerHTML = htmlContenido;
          updateCounters();
          applyCurrentFilter();
        }
      }
    })
    .catch(error => console.error(error));
}

function updateCounters() {
  const allCards = document.querySelectorAll('.ticket-chat-card');
  let total = allCards.length;
  let unread = 0;
  let read = 0;
  allCards.forEach(card => {
    if (card.getAttribute('data-status') === 'unread') { unread++; }
    else { read++; }
  });
  document.getElementById('count-all').innerText = total;
  document.getElementById('count-unread').innerText = unread;
  document.getElementById('count-read').innerText = read;
}

document.addEventListener("DOMContentLoaded", function () {
  updateCounters();

  const confirmBtn = document.getElementById('btnConfirmClose');
  if (confirmBtn) {
    confirmBtn.addEventListener('click', function () {
      var modalEl = document.getElementById('confirmCloseModal');
      var modal = bootstrap.Modal.getInstance(modalEl);
      modal.hide();

      if (!currentTicketId || !btnToLoad) return;

      const btn = btnToLoad;
      const originalHtml = btn.innerHTML;

      btn.disabled = true;
      btn.innerHTML = '<i class="fas fa-circle-notch fa-spin me-1"></i> Cerrando...';

      const csrfToken = getCookie('csrftoken');

      fetch('/soporte/api/cerrar-ticket/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
        body: JSON.stringify({ ticket_id: currentTicketId })
      })
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            btn.style.display = 'none';

            const replyInput = document.getElementById('replyInput');
            const btnSend = document.getElementById('btnSendReply');
            replyInput.disabled = true;
            btnSend.disabled = true;
            replyInput.placeholder = "Este ticket ya ha sido cerrado.";
            replyInput.value = "";

            const activeCard = document.getElementById('card-' + currentTicketId);
            if (activeCard) {
              activeCard.setAttribute('data-is-closed', 'true');
              activeCard.setAttribute('data-status', 'read');
              let dot = activeCard.querySelector('.unread-dot');
              if (dot) dot.style.display = 'none';

              let badge = activeCard.querySelector('.status-badge-mini');
              if (badge) {
                badge.className = 'status-badge-mini badge-cerrado';
                badge.innerText = 'Cerrado';
              }
            }
            updateCounters();
          } else {
            btn.disabled = false;
            btn.innerHTML = originalHtml;
          }
        })
        .catch(error => {
          btn.disabled = false;
          btn.innerHTML = originalHtml;
        });
    });
  }
});

function applyCurrentFilter() {
  const cards = document.querySelectorAll('.ticket-chat-card');
  cards.forEach(card => {
    if (activeFilterStatus === 'all') {
      card.style.display = 'flex';
    } else if (card.getAttribute('data-status') === activeFilterStatus) {
      card.style.display = 'flex';
    } else {
      card.style.display = 'none';
    }
  });
}

function filterTickets(status, element) {
  activeFilterStatus = status;
  document.querySelectorAll('.stat-card').forEach(card => card.classList.remove('active-filter'));
  element.classList.add('active-filter');

  const labelMap = { 'all': 'Todas', 'unread': 'No Leídas / Pendientes', 'read': 'Leídas' };
  document.getElementById('currentFilterLabel').innerText = labelMap[status];

  applyCurrentFilter();
}

function loadTicket(ticketId, event) {
  if (event) event.preventDefault();
  const cards = document.querySelectorAll('.ticket-chat-card');
  cards.forEach(c => c.classList.remove('active'));

  const activeCard = document.getElementById('card-' + ticketId);
  activeCard.classList.add('active');

  if (activeCard.getAttribute('data-status') === 'unread') {
    activeCard.setAttribute('data-status', 'read');
    let dot = activeCard.querySelector('.unread-dot');
    if (dot) dot.style.display = 'none';
    updateCounters();
    if (activeFilterStatus === 'unread') { activeCard.style.display = 'none'; }
  }

  currentTicketId = ticketId;
  const isClosed = activeCard.getAttribute('data-is-closed') === 'true';

  const noSel = document.getElementById('noTicketSelected');
  const loading = document.getElementById('chatLoading');
  const header = document.getElementById('chatHeader');
  const msgs = document.getElementById('chatMessages');
  const inputArea = document.getElementById('chatInputArea');
  const replyInput = document.getElementById('replyInput');
  const btnSend = document.getElementById('btnSendReply');
  const btnCloseObj = document.getElementById('btnCloseTicketObj');

  noSel.style.display = 'none';
  header.style.display = 'none';
  msgs.style.display = 'none';
  inputArea.style.display = 'none';
  loading.style.display = 'block';

  if (chatInterval) clearInterval(chatInterval);

  fetch(`/soporte/api/mensajes/${ticketId}/`)
    .then(response => response.json())
    .then(data => {
      loading.style.display = 'none';
      header.style.display = 'flex';
      msgs.style.display = 'flex';
      inputArea.style.display = 'flex';

      document.getElementById('headerUserName').innerText = data.usuario_nombre;
      document.getElementById('headerUserEmail').innerText = data.usuario_correo;
      document.getElementById('headerUserInitial').innerText = data.usuario_nombre.charAt(0).toUpperCase();

      if (isClosed) {
        btnCloseObj.style.display = 'none';
        replyInput.disabled = true;
        btnSend.disabled = true;
        replyInput.placeholder = "Este ticket ya ha sido cerrado.";
      } else {
        btnCloseObj.style.display = 'block';
        replyInput.disabled = false;
        btnSend.disabled = false;
        replyInput.placeholder = "Escribe tu respuesta...";
      }

      msgs.innerHTML = '';
      data.mensajes.forEach(msg => {
        appendMessageBubble(msg, msgs);
      });

      scrollToBottom();
      if (!isClosed) { document.getElementById('replyInput').focus(); }

      chatInterval = setInterval(refreshMessagesEnVivo, 3000);
    })
    .catch(error => {
      loading.style.display = 'none';
      noSel.style.display = 'flex';
    });
}

function refreshMessagesEnVivo() {
  if (!currentTicketId) return;
  fetch(`/soporte/api/mensajes/${currentTicketId}/`)
    .then(response => response.json())
    .then(data => {
      const msgs = document.getElementById('chatMessages');
      const cantidadActual = msgs.querySelectorAll('.message-row').length;

      if (data.mensajes && data.mensajes.length > cantidadActual) {
        const mensajesNuevos = data.mensajes.slice(cantidadActual);
        mensajesNuevos.forEach(msg => {
          appendMessageBubble(msg, msgs);
        });
        scrollToBottom();
      }
    });
}

function sendMessage() {
  const input = document.getElementById('replyInput');
  const mensajeTexto = input.value.trim();
  const msgsContainer = document.getElementById('chatMessages');

  if (!mensajeTexto || !currentTicketId) return;

  input.disabled = true;
  const btn = document.getElementById('btnSendReply');
  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i>';

  const csrfToken = getCookie('csrftoken');
  fetch('/soporte/api/enviar-mensaje/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
    body: JSON.stringify({ ticket_id: currentTicketId, mensaje: mensajeTexto })
  })
    .then(response => response.json())
    .then(data => {
      input.disabled = false;
      btn.disabled = false;
      btn.innerHTML = '<i class="fas fa-paper-plane"></i>';
      input.focus();

      if (data.success) {
        input.value = '';
        appendMessageBubble(data, msgsContainer);
        scrollToBottom();
      }
    })
    .catch(error => {
      input.disabled = false;
      btn.disabled = false;
      btn.innerHTML = '<i class="fas fa-paper-plane"></i>';
    });
}

function closeTicket(event) {
  if (!currentTicketId) return;
  btnToLoad = event.currentTarget;
  var myModal = new bootstrap.Modal(document.getElementById('confirmCloseModal'));
  myModal.show();
}

function appendMessageBubble(msgData, container) {
  const row = document.createElement('div');
  row.className = 'message-row ' + (msgData.es_admin_respuesta ? 'msg-out' : 'msg-in');
  const bubbleHtml = `
        <div class="msg-content-wrapper">
            <div class="msg-info">
                ${msgData.remitente_nombre} &nbsp; <span style="font-weight:normal; color: #64748b;">${msgData.fecha_envio_formateada}</span>
            </div>
            <div class="message-bubble">${msgData.mensaje}</div>
        </div>
    `;
  row.innerHTML = bubbleHtml;
  container.appendChild(row);
}

function scrollToBottom() {
  const msgs = document.getElementById('chatMessages');
  msgs.scrollTop = msgs.scrollHeight;
}

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

document.getElementById('replyInput').addEventListener('keypress', function (e) {
  if (e.key === 'Enter') { sendMessage(); }
});