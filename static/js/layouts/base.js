// =================================================================
//  base.js  —  Teatro Jaime Laredo
//  Cubre: toasts · modal auth · tabs · toggle password · Escape key
// =================================================================

// ── Utilidades ────────────────────────────────────────────────────
const $  = (id)  => document.getElementById(id);
const $$ = (sel) => document.querySelectorAll(sel);

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

function ensureCsrfTokens() {
  const token = getCookie('csrftoken');
  if (!token) return;
  document.querySelectorAll('#auth-modal form input[name="csrfmiddlewaretoken"]').forEach((el) => {
    el.value = token;
  });
}


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
  switchAuthTab(tab);
  ensureCsrfTokens();
}

/** Cierra el modal */
function closeAuthModal() {
  const modal = $('auth-modal');
  modal.classList.add('hidden');
  modal.classList.remove('flex');
  document.body.classList.remove('overflow-hidden');
}

/** Cambia entre pestañas sin cerrar el modal */
function switchAuthTab(tab) {
  const isLogin = tab === 'login';
  const btnLogin = $('tab-login');
  const btnSignup = $('tab-signup');
  const formLogin = $('form-login');
  const formSignup = $('form-signup');

  if (!btnLogin || !btnSignup || !formLogin || !formSignup) return;

  btnLogin.classList.toggle('active', isLogin);
  btnSignup.classList.toggle('active', !isLogin);

  // form-login visible by default
  formLogin.classList.toggle('hidden', !isLogin);
  formSignup.classList.toggle('hidden', isLogin);
}

/** Muestra / oculta la contraseña del input dentro del mismo .input-wrapper */
function togglePassword(iconEl) {
  const input = iconEl?.previousElementSibling;
  if (!input) return;
  if (input.type === 'password') {
    input.type = 'text';
    iconEl.classList.remove('fa-eye-slash');
    iconEl.classList.add('fa-eye');
  } else {
    input.type = 'password';
    iconEl.classList.remove('fa-eye');
    iconEl.classList.add('fa-eye-slash');
  }
}

// ── Validaciones Visuales (Miguel) ───────────────────────────────
function toggleVal(input, regex, feedId) {
  const feed = document.getElementById(feedId);
  if (!input || !feed) return;
  if (regex.test(input.value)) {
    input.classList.add('is-valid-custom');
    input.classList.remove('is-invalid-custom');
    feed.classList.remove('show');
  } else {
    input.classList.add('is-invalid-custom');
    input.classList.remove('is-valid-custom');
    feed.classList.add('show');
  }
}
function valNombre(id) {
  toggleVal(
    document.getElementById(id),
    /^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(\s[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*$/,
    `${id}-feed`,
  );
}
function valApellido(id) {
  toggleVal(
    document.getElementById(id),
    /^[A-ZÁÉÍÓÚÑ][a-zA-ZáéíóúñÁÉÍÓÚÑ]*(\s[A-ZÁÉÍÓÚÑ][a-zA-ZáéíóúñÁÉÍÓÚÑ]*)*$/,
    `${id}-feed`,
  );
}
function valEmail() {
  toggleVal(
    document.getElementById('reg-correo'),
    /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,10}$/,
    'email-feed',
  );
}
function valPwd() {
  toggleVal(
    document.getElementById('reg-pwd'),
    /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&.-])[A-Za-z\d@$!%*?&.-]{8,}$/,
    'pwd-feed',
  );
}
function valTel() {
  const input = document.getElementById('reg-tel');
  const container = document.getElementById('phone-container');
  const feed = document.getElementById('tel-feed');
  if (!input || !container || !feed) return;

  if (input.value === '') {
    container.style.borderColor = '#000';
    feed.classList.remove('show');
    return;
  }
  if (/^[67][0-9]{7}$/.test(input.value)) {
    container.style.borderColor = '#198754';
    feed.classList.remove('show');
  } else {
    container.style.borderColor = '#dc3545';
    feed.classList.add('show');
  }
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
  ensureCsrfTokens();

  // Cerrar modal con Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeAuthModal();
  });

  // Auto-abrir modal con ?action=login|signup (como Miguel)
  const params = new URLSearchParams(window.location.search);
  const action = params.get('action');
  if (action === 'login' || action === 'signup') {
    openAuthModal(action);
    window.history.replaceState({}, document.title, window.location.pathname);
  }
});