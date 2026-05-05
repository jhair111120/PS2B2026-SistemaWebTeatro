// =================================================================
//  base.js  —  Teatro Jaime Laredo
//  Cubre: toasts · modal auth · tabs · toggle password · Escape key
// =================================================================

// ── Utilidades ────────────────────────────────────────────────────
const $  = (id)  => document.getElementById(id);
const $$ = (sel) => document.querySelectorAll(sel);


// ═════════════════════════════════════════════════════════════════
//  TOASTS
//  Auto-dismiss a los 4 s · click manual para cerrar
// ═════════════════════════════════════════════════════════════════
function initToasts() {
  $$('.toast').forEach((toast) => {
    const dismiss = (delay) => {
      setTimeout(() => {
        toast.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        toast.style.opacity    = '0';
        toast.style.transform  = 'translateX(1rem)';
        setTimeout(() => toast.remove(), 300);
      }, delay);
    };

    dismiss(4000);                           // auto
    toast.addEventListener('click', () => dismiss(0)); // manual
  });
}


// ═════════════════════════════════════════════════════════════════
//  MODAL DE AUTENTICACIÓN
// ═════════════════════════════════════════════════════════════════

/** Abre el modal en la pestaña indicada: 'login' (default) | 'signup' */
function openAuthModal(tab = 'login') {
  const modal = $('auth-modal');
  modal.classList.remove('hidden');
  modal.classList.add('flex');
  document.body.classList.add('overflow-hidden');
  switchTab(tab);
}

/** Cierra el modal */
function closeAuthModal() {
  const modal = $('auth-modal');
  modal.classList.add('hidden');
  modal.classList.remove('flex');
  document.body.classList.remove('overflow-hidden');
}

/** Cambia entre pestañas sin cerrar el modal */
function switchTab(tab) {
  const isLogin = tab === 'login';

  $('tab-login').classList.toggle('auth-tab--active',  isLogin);
  $('tab-signup').classList.toggle('auth-tab--active', !isLogin);

  $('form-login').classList.toggle('hidden',  !isLogin);
  $('form-signup').classList.toggle('hidden',  isLogin);
}

/** Muestra / oculta la contraseña del input dentro del mismo .input-wrapper */
function togglePassword(btn) {
  const input    = btn.closest('.input-wrapper').querySelector('input');
  const icon     = btn.querySelector('i');
  const isHidden = input.type === 'password';

  input.type = isHidden ? 'text' : 'password';
  icon.classList.toggle('fa-eye',       !isHidden);
  icon.classList.toggle('fa-eye-slash',  isHidden);
}


// ═════════════════════════════════════════════════════════════════
//  SMOOTH SCROLLING
// ═════════════════════════════════════════════════════════════════
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const targetId = this.getAttribute('href');
      if (targetId === '#') return;
      
      const targetElement = document.querySelector(targetId);
      if (targetElement) {
        e.preventDefault();
        targetElement.scrollIntoView({
          behavior: 'smooth'
        });
      }
    });
  });
}

// ═════════════════════════════════════════════════════════════════
//  INIT
// ═════════════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
  initToasts();
  initSmoothScroll();

  // Cerrar modal con Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeAuthModal();
  });
});