let currentTicketId = null;

/* =========================
   HELPERS UI
========================= */
const UI = {
  noSelected: document.getElementById("noTicketSelected"),
  header: document.getElementById("chatHeader"),
  messages: document.getElementById("chatMessages"),
  inputArea: document.getElementById("chatInputArea"),
  replyInput: document.getElementById("replyInput"),
  sendBtn: document.getElementById("btnSendReply"),
};

function showChatUI() {
  UI.noSelected.classList.add("hidden");
  UI.header.classList.remove("hidden");
  UI.messages.classList.remove("hidden");
  UI.inputArea.classList.remove("hidden");
}

function showEmptyState() {
  UI.noSelected.classList.remove("hidden");
  UI.header.classList.add("hidden");
  UI.messages.classList.add("hidden");
  UI.inputArea.classList.add("hidden");
}

/* =========================
   LOAD TICKET
========================= */
function loadTicket(ticketId, event) {
  if (event) event.preventDefault();
  if (!ticketId) return;

  currentTicketId = ticketId;

  // Activar tarjeta
  document.querySelectorAll("#ticketList a").forEach((c) =>
    c.classList.remove("active")
  );
  const activeCard = document.getElementById("card-" + ticketId);
  if (activeCard) activeCard.classList.add("active");

  showEmptyState(); // limpia UI mientras carga

  fetch(`/soporte/api/mensajes/${ticketId}/`)
    .then((res) => res.json())
    .then((data) => {
      updateHeader(data);
      renderMessages(data.mensajes);
      showChatUI();
      focusInput();
    })
    .catch((err) => {
      console.error("Error cargando ticket:", err);
      alert("No se pudo cargar la conversación.");
      showEmptyState();
    });
}

/* =========================
   HEADER
========================= */
function updateHeader(data) {
  document.getElementById("headerUserName").textContent =
    data.usuario_nombre;

  document.getElementById("headerUserEmail").textContent =
    data.usuario_correo;

  document.getElementById("headerTicketId").textContent =
    data.numero_reclamo;

  document.getElementById("headerTicketStatus").textContent =
    data.estado_ticket;

  // inicial
  const avatar = document.querySelector("#chatHeader .rounded-full");
  if (avatar) {
    avatar.textContent = data.usuario_nombre.charAt(0).toUpperCase();
  }
}

/* =========================
   MENSAJES
========================= */
function renderMessages(messages) {
  UI.messages.innerHTML = "";

  messages.forEach((msg) => {
    UI.messages.appendChild(createMessage(msg));
  });

  scrollToBottom();
}

function createMessage(msg) {
  const row = document.createElement("div");
  row.className =
    "message-row " + (msg.es_admin_respuesta ? "msg-out" : "msg-in");

  row.innerHTML = `
    <div class="message-bubble">
      <div class="msg-info">
        <strong>${msg.remitente_nombre}</strong>
        <span>${msg.fecha_envio_formateada}</span>
      </div>
      <div>${msg.mensaje}</div>
    </div>
  `;

  return row;
}

/* =========================
   SEND MESSAGE
========================= */
function sendMessage() {
  const text = UI.replyInput.value.trim();
  if (!text || !currentTicketId) return;

  toggleInput(false);

  fetch("/soporte/api/enviar-mensaje/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify({
      ticket_id: currentTicketId,
      mensaje: text,
    }),
  })
    .then((res) => res.json())
    .then((data) => {
      toggleInput(true);

      if (!data.success) {
        alert(data.error || "Error al enviar mensaje");
        return;
      }

      UI.replyInput.value = "";
      UI.messages.appendChild(createMessage(data));
      scrollToBottom();
    })
    .catch((err) => {
      console.error(err);
      alert("No se pudo enviar el mensaje.");
      toggleInput(true);
    });
}

function toggleInput(enabled) {
  UI.replyInput.disabled = !enabled;
  UI.sendBtn.disabled = !enabled;
}

/* =========================
   CLOSE TICKET
========================= */
function closeTicket(e) {
  if (!currentTicketId) return;
  if (!confirm("¿Cerrar este ticket?")) return;

  const btn = e.currentTarget;
  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

  fetch("/soporte/api/cerrar-ticket/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify({ ticket_id: currentTicketId }),
  })
    .then((res) => res.json())
    .then((data) => {
      btn.disabled = false;
      btn.innerHTML = '<i class="fas fa-times"></i> Cerrar';

      if (!data.success) {
        alert(data.error || "Error al cerrar ticket");
        return;
      }

      document.getElementById("headerTicketStatus").textContent =
        data.nuevo_estado;

      // actualizar lista lateral
      const card = document.getElementById("card-" + currentTicketId);
      if (card) {
        const status = card.querySelector(".text-blue-400");
        if (status) status.textContent = data.nuevo_estado;
      }
    })
    .catch((err) => {
      console.error(err);
      alert("Error al cerrar ticket");
      btn.disabled = false;
    });
}

/* =========================
   UTILIDADES
========================= */
function scrollToBottom() {
  UI.messages.scrollTop = UI.messages.scrollHeight;
}

function focusInput() {
  UI.replyInput.focus();
}

function getCookie(name) {
  return document.cookie
    .split("; ")
    .find((row) => row.startsWith(name + "="))
    ?.split("=")[1];
}

/* =========================
   EVENTOS
========================= */
UI.replyInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendMessage();
});