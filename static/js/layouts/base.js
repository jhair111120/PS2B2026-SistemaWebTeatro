function valNombre(id) {
  toggleVal(document.getElementById(id), /^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(\s[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*$/, id + '-feed');
}

function valApellido(id) {
  toggleVal(document.getElementById(id), /^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(\s[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*$/, id + '-feed');
}

function valEmail() {
  toggleVal(document.getElementById('reg-correo'), /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,10}$/, 'email-feed');
}

function valPwd() {
  toggleVal(document.getElementById('reg-pwd'), /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&.-])[A-Za-z\d@$!%*?&.-]{8,}$/, 'pwd-feed');
}

function valTel() {
  const input = document.getElementById('reg-tel');
  const container = document.getElementById('phone-container');
  const feed = document.getElementById('tel-feed');
  if (input.value === "") {
    container.style.borderColor = "black";
    feed.classList.remove('show');
    return;
  }

  if (/^[67][0-9]{7}$/.test(input.value)) {
    container.style.borderColor = "#198754";
    feed.classList.remove('show');
  } else {
    container.style.borderColor = "#dc3545";
    feed.classList.add('show');
  }
}

function toggleVal(input, regex, feedId) {
  const feed = document.getElementById(feedId);
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

function switchAuthTab(tab) {
  const bLog = document.getElementById('tab-login');
  const bSig = document.getElementById('tab-signup');
  const fLog = document.getElementById('form-login');
  const fSig = document.getElementById('form-signup');
  if (tab === 'login') {
    bLog.classList.add('active');
    bSig.classList.remove('active');
    fLog.classList.remove('d-none');
    fSig.classList.add('d-none');
  } else {
    bSig.classList.add('active');
    bLog.classList.remove('active');
    fSig.classList.remove('d-none');
    fLog.classList.add('d-none');
  }
}

function togglePassword(icon) {
  const input = icon.previousElementSibling;
  if (input.type === 'password') {
    input.type = 'text';
    icon.classList.replace('fa-eye-slash', 'fa-eye');
  } else {
    input.type = 'password';
    icon.classList.replace('fa-eye', 'fa-eye-slash');
  }
}

document.addEventListener("DOMContentLoaded", function () {
  const action = new URLSearchParams(window.location.search).get('action');
  if (action === 'login' || action === 'signup') {
    var authModal = new bootstrap.Modal(document.getElementById('authModal'));
    switchAuthTab(action);
    authModal.show();
    window.history.replaceState({}, document.title, window.location.pathname);
  }
});