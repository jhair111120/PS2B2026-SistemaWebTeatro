document.addEventListener("DOMContentLoaded", () => {
  const tabs = document.querySelectorAll(".tab-btn");
  const contents = document.querySelectorAll(".tab-content");

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const target = tab.getAttribute("data-tab");

      // Reset tabs - Eliminamos las clases de Tailwind y usamos la clase maestra
      tabs.forEach((t) => {
        t.classList.remove("tab-btn--active");
      });
      
      contents.forEach((c) => {
        c.classList.add("hidden");
        c.classList.remove("fade-in");
      });

      // Activate clicked tab - Añadimos la clase maestra que tiene el borde azul
      tab.classList.add("tab-btn--active");

      // Show content
      const activeContent = document.getElementById(target);
      if (activeContent) {
        activeContent.classList.remove("hidden");
        // Animación suave
        setTimeout(() => {
          activeContent.classList.add("fade-in");
        }, 10);
      }
    });
  });
});
