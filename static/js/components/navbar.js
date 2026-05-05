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