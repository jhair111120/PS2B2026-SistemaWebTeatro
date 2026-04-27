// ================= DROPDOWN NAVBAR =================

const dropdown = document.getElementById("dropdownMenu");

// Botón específico del dropdown
const dropdownButton = document.querySelector("[onclick='toggleDropdown()']");

function toggleDropdown() {
  if (!dropdown) return;

  dropdown.classList.toggle("hidden");
}

// Cerrar al hacer click fuera
document.addEventListener("click", function (e) {
  if (!dropdown || !dropdownButton) return;

  const isClickInsideDropdown = dropdown.contains(e.target);
  const isClickOnButton = dropdownButton.contains(e.target);

  if (!isClickInsideDropdown && !isClickOnButton) {
    dropdown.classList.add("hidden");
  }
});

// Opcional: cerrar con ESC (pro UX)
document.addEventListener("keydown", function (e) {
  if (e.key === "Escape" && dropdown) {
    dropdown.classList.add("hidden");
  }
});

function switchTab(tab) {
  const isLogin = tab === 'login';

  document.getElementById('tab-login').classList.toggle('auth-tab--active', isLogin);
  document.getElementById('tab-signup').classList.toggle('auth-tab--active', !isLogin);

  document.getElementById('form-login').classList.toggle('hidden', !isLogin);
  document.getElementById('form-signup').classList.toggle('hidden', isLogin);
}

function togglePassword(btn) {
  const input = btn.previousElementSibling;
  const icon  = btn.querySelector('i');
  const isHidden = input.type === 'password';
  input.type = isHidden ? 'text' : 'password';
  icon.classList.toggle('fa-eye',      !isHidden);
  icon.classList.toggle('fa-eye-slash', isHidden);
}

// Leer ?tab=login o ?tab=signup de la URL
document.addEventListener('DOMContentLoaded', () => {
  const tab = new URLSearchParams(window.location.search).get('tab');
  if (tab === 'signup') switchTab('signup');
});