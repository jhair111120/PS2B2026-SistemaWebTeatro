(() => {
  const storageKey = "purchaseCart";
  const deadlineKey = "purchaseDeadline";
  const serviceFee = 5;

  const page = document.querySelector("[data-purchase-step]");
  if (!page) return;

  const step = page.dataset.purchaseStep;
  let cart = readCart();
  let modalQty = 1;
  let selectedZone = "";
  let selectedPrice = 0;

  if (step === "zones") {
    ensureDeadline();
    initZoneMap();
    initQuantityModal();
    initContinueButton();
  }

  if (step === "payment") {
    ensureDeadline();
    renderSummary();
    initPayButton();
  }

  if (step === "success") {
    renderSuccess();
    localStorage.removeItem(deadlineKey);
  }

  initTimer();

  function ensureDeadline() {
    if (!localStorage.getItem(deadlineKey)) {
      localStorage.setItem(deadlineKey, String(Date.now() + 15 * 60 * 1000));
    }
  }

  function readCart() {
    try {
      const value = localStorage.getItem(storageKey);
      return value ? JSON.parse(value) : [];
    } catch {
      return [];
    }
  }

  function saveCart() {
    localStorage.setItem(storageKey, JSON.stringify(cart));
  }

  function getTotals() {
    const subtotal = cart.reduce((acc, item) => acc + item.price * item.qty, 0);
    const service = subtotal > 0 ? serviceFee : 0;
    return { subtotal, service, total: subtotal + service };
  }

  function initTimer() {
    const countdownEl = document.getElementById("countdown");
    if (!countdownEl) return;

    ensureDeadline();

    const tick = () => {
      const deadline = Number(localStorage.getItem(deadlineKey) || 0);
      const diff = Math.max(0, deadline - Date.now());
      const mins = Math.floor(diff / 60000);
      const secs = Math.floor((diff % 60000) / 1000);
      countdownEl.textContent = `${mins}:${secs.toString().padStart(2, "0")}`;
    };

    tick();
    setInterval(tick, 1000);
  }

  function initZoneMap() {
    document.querySelectorAll(".zone-path").forEach((zone) => {
      zone.addEventListener("click", () => {
        selectedZone = zone.dataset.zone || "";
        selectedPrice = Number(zone.dataset.price || 0);
        modalQty = 1;
        setModalState();
        document.getElementById("quantity-modal")?.classList.remove("hidden");
      });
    });

    renderSummary();
  }

  function initQuantityModal() {
    document.querySelectorAll("[data-close-modal]").forEach((button) => {
      button.addEventListener("click", closeModal);
    });

    document.querySelectorAll("[data-qty-change]").forEach((button) => {
      button.addEventListener("click", () => {
        modalQty = Math.max(1, modalQty + Number(button.dataset.qtyChange || 0));
        setModalState();
      });
    });

    document.getElementById("modal-add-btn")?.addEventListener("click", () => {
      const existing = cart.find((item) => item.zone === selectedZone);
      if (existing) {
        existing.qty += modalQty;
      } else {
        cart.push({ zone: selectedZone, price: selectedPrice, qty: modalQty });
      }
      saveCart();
      renderSummary();
      closeModal();
    });
  }

  function setModalState() {
    const zoneName = document.getElementById("modal-zone-name");
    const zonePrice = document.getElementById("modal-zone-price");
    const qtyValue = document.getElementById("modal-qty");
    if (zoneName) zoneName.textContent = selectedZone;
    if (zonePrice) zonePrice.textContent = `Bs. ${selectedPrice} por entrada`;
    if (qtyValue) qtyValue.textContent = String(modalQty);
  }

  function closeModal() {
    document.getElementById("quantity-modal")?.classList.add("hidden");
  }

  function renderSummary() {
    const itemsContainer = document.getElementById("cart-items");
    const continueButton = document.getElementById("btn-continue-payment");
    if (!itemsContainer) return;

    const { subtotal, service, total } = getTotals();
    itemsContainer.innerHTML = "";

    if (cart.length === 0) {
      itemsContainer.innerHTML = '<p class="text-center text-gray-500 py-4">No has seleccionado zonas aún</p>';
      if (continueButton) continueButton.disabled = true;
    } else {
      if (continueButton) continueButton.disabled = false;
      cart.forEach((item, index) => {
        const row = document.createElement("div");
        row.className = "selected-item";
        row.innerHTML = `
          <div>
            <p class="font-bold text-sm">${item.zone}</p>
            <p class="text-xs text-gray-500">${item.qty} entradas x Bs. ${item.price}</p>
          </div>
          <div class="flex items-center gap-4">
            <span class="font-bold">Bs. ${item.price * item.qty}</span>
            <button type="button" class="btn-remove-item" aria-label="Eliminar">
              <i class="fas fa-trash-alt"></i>
            </button>
          </div>
        `;
        row.querySelector(".btn-remove-item")?.addEventListener("click", () => {
          cart.splice(index, 1);
          saveCart();
          renderSummary();
        });
        itemsContainer.appendChild(row);
      });
    }

    setText("subtotal-val", `Bs. ${subtotal}`);
    setText("service-val", `Bs. ${service}`);
    setText("total-val", `Bs. ${total}`);
    setText("btn-pay-purchase", `Pagar Bs. ${total.toFixed(2)}`);
  }

  function initContinueButton() {
    const continueButton = document.getElementById("btn-continue-payment");
    if (!continueButton) return;
    continueButton.addEventListener("click", () => {
      if (cart.length === 0) return;
      window.location.href = "/finalizar-compra/";
    });
  }

  function initPayButton() {
    const payButton = document.getElementById("btn-pay-purchase");
    if (!payButton) return;
    payButton.addEventListener("click", () => {
      window.location.href = "/compra-exitosa/";
    });
  }

  function renderSuccess() {
    const successItems = document.getElementById("success-cart-items");
    if (!successItems) return;

    const { total } = getTotals();
    setText("success-total", `Bs. ${total}`);
    successItems.innerHTML = "";

    if (cart.length === 0) {
      successItems.innerHTML = '<p class="text-center text-gray-500 py-4">No hay datos de compra</p>';
      return;
    }

    cart.forEach((item) => {
      const row = document.createElement("div");
      row.className = "selected-item";
      row.innerHTML = `
        <div>
          <p class="font-bold text-sm">${item.zone}</p>
          <p class="text-xs text-gray-500">${item.qty} entradas x Bs. ${item.price}</p>
        </div>
        <span class="font-bold">Bs. ${item.price * item.qty}</span>
      `;
      successItems.appendChild(row);
    });
  }

  function setText(id, value) {
    const element = document.getElementById(id);
    if (element) element.textContent = value;
  }
})();
