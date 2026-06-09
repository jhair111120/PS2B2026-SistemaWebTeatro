document.addEventListener("DOMContentLoaded", function () {
  // 1. Efecto de sombreado y cambio de fondo al hacer scroll
  const navbar = document.querySelector('.navbar');

  if (navbar) {
    window.addEventListener('scroll', function () {
      if (window.scrollY > 50) {
        navbar.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.5)';
        navbar.style.backgroundColor = '#070a0f';
      } else {
        navbar.style.boxShadow = 'none';
        navbar.style.backgroundColor = 'var(--bg-navbar)';
      }
    });
  }

  // 2. Asignación dinámica de la clase 'active' según la URL actual
  const currentLocation = location.href;
  const navLinks = document.querySelectorAll('.navbar-nav .nav-link');

  navLinks.forEach(link => {
    if (link.href === currentLocation) {
      navLinks.forEach(l => l.classList.remove('active'));
      link.classList.add('active');
    }
  });
});