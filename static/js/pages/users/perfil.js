document.addEventListener("DOMContentLoaded", () => {
  const tabs = document.querySelectorAll(".tab-btn");
  const contents = document.querySelectorAll(".tab-content");

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const target = tab.getAttribute("data-tab");

      // Reset tabs
      tabs.forEach((t) =>
        t.classList.remove("active", "bg-blue-600", "text-white"),
      );
      contents.forEach((c) => {
        c.classList.add("hidden");
        c.classList.remove("fade-in");
      });

      // Activate clicked tab
      tab.classList.add("active", "bg-blue-600", "text-white");

      // Show content
      const activeContent = document.getElementById(target);
      activeContent.classList.remove("hidden");

      // Animación suave
      setTimeout(() => {
        activeContent.classList.add("fade-in");
      }, 10);
    });
  });
});
