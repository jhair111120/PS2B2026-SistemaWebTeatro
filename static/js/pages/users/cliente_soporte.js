let chatPollingInterval = null;

document.addEventListener("DOMContentLoaded", function () {
    if (typeof URL_MENSAJES_API !== 'undefined') {
        loadClientMessagesFirstTime();
        if (!ES_TICKET_CERRADO) {
            chatPollingInterval = setInterval(refreshClientMessagesEnVivo, 3000);
        }
    }
});

function loadClientMessagesFirstTime() {
    fetch(URL_MENSAJES_API)
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById('clientChatMessages');
            container.innerHTML = '';
            if (data.mensajes && data.mensajes.length > 0) {
                appendClientBubble({
                    es_mio: false,
                    mensaje: "¡Hola! 👋 Bienvenido al soporte oficial. Nuestro equipo te atenderá pronto.",
                    fecha_envio_formateada: "Auto"
                }, container, false);
            }
            data.mensajes.forEach(msg => appendClientBubble(msg, container, true));
            scrollToBottomClient();
        });
}

function refreshClientMessagesEnVivo() {
    fetch(URL_MENSAJES_API)
        .then(res => res.json())
        .then(data => {
            // 🔥 DETECCIÓN DE CIERRE EN TIEMPO REAL 🔥
            if (data.ticket_cerrado && !ES_TICKET_CERRADO) {
                ES_TICKET_CERRADO = true;
                clearInterval(chatPollingInterval);
                updateUIForClosedTicket();
            }

            const msgs = document.getElementById('clientChatMessages');
            const cantidadActual = msgs.querySelectorAll('.real-msg-row').length;
            if (data.mensajes && data.mensajes.length > cantidadActual) {
                data.mensajes.slice(cantidadActual).forEach(msg => appendClientBubble(msg, msgs, true));
                scrollToBottomClient();
            }
        });
}

function updateUIForClosedTicket() {
    // 1. Cambiar indicador de cabecera
    const headerStatus = document.getElementById('statusIndicatorContainer');
    headerStatus.innerHTML = `
        <div class="fw-bold text-white fs-5">Soporte Teatro La Paz</div>
        <div class="small text-danger fw-bold">Ticket Cerrado</div>
    `;

    // 2. Cambiar input por banner
    const bottomSection = document.getElementById('chatBottomSection');
    bottomSection.innerHTML = `
        <div class="banner-cerrado">
            <i class="fas fa-lock me-2"></i> Este ticket ha sido cerrado. Si tienes otra duda, crea uno nuevo.
        </div>
    `;

    // 3. Actualizar lista lateral (si existe el elemento)
    const currentSideTicket = document.getElementById(`side-ticket-${TICKET_ID}`);
    if (currentSideTicket) {
        const badge = currentSideTicket.querySelector('.status-container');
        badge.innerHTML = '<span class="status-badge status-closed">Cerrado</span>';
    }
}

function sendClientMessage() {
    const input = document.getElementById('clientReplyInput');
    const msg = input.value.trim();
    if (!msg || ES_TICKET_CERRADO) return;

    input.disabled = true;
    const btn = document.querySelector('.btn-send-client');
    btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i>';

    fetch(URL_ENVIAR_MENSAJE_API, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookieClient('csrftoken') },
        body: JSON.stringify({ mensaje: msg })
    })
        .then(res => res.json())
        .then(data => {
            input.disabled = false; btn.innerHTML = '<i class="fas fa-paper-plane"></i>';
            if (data.success) { input.value = ''; appendClientBubble(data, document.getElementById('clientChatMessages'), true); scrollToBottomClient(); }
            else { alert('Error: ' + data.error); }
        });
}

function appendClientBubble(msgData, container, isReal) {
    const row = document.createElement('div');
    row.className = `msg-row ${isReal ? 'real-msg-row' : ''} ${msgData.es_mio ? 'msg-client' : 'msg-agent'}`;
    row.innerHTML = `
        <div class="msg-content-wrapper">
            <div class="msg-bubble">${msgData.mensaje}</div>
            <div class="msg-info">${msgData.fecha_envio_formateada}</div>
        </div>
    `;
    container.appendChild(row);
}

function scrollToBottomClient() { const msgs = document.getElementById('clientChatMessages'); msgs.scrollTo({ top: msgs.scrollHeight, behavior: 'smooth' }); }

function getCookieClient(n) { let v = null; if (document.cookie) { document.cookie.split(';').forEach(c => { let p = c.trim().split('='); if (p[0] === n) v = decodeURIComponent(p[1]); }); } return v; }

const replyInput = document.getElementById('clientReplyInput');
if (replyInput) replyInput.addEventListener('keypress', e => { if (e.key === 'Enter') sendClientMessage(); });