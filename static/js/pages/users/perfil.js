/**
 * js/pages/users/perfil.js
 * Validaciones específicas para el perfil de usuario
 */

function valPerfNombre() {
  toggleVal(document.getElementById('perf-nombre'), /^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(\s[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*$/, 'perf-nombre-feed');
}

function valPerfApellido() {
  toggleVal(document.getElementById('perf-apellido'), /^[A-ZÁÉÍÓÚÑ][a-zA-ZáéíóúñÁÉÍÓÚÑ]*(\s[A-ZÁÉÍÓÚÑ][a-zA-ZáéíóúñÁÉÍÓÚÑ]*)*$/, 'perf-apellido-feed');
}

function valPerfEmail() {
  toggleVal(document.getElementById('perf-correo'), /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,10}$/, 'perf-email-feed');
}

function valPerfTel() {
  const input = document.getElementById('perf-tel');
  if (input.value === "") {
    input.classList.remove('is-invalid-custom', 'is-valid-custom');
    document.getElementById('perf-tel-feed').classList.remove('show');
    return;
  }
  toggleVal(input, /^[67][0-9]{7}$/, 'perf-tel-feed');
}

function valPerfDni() {
  const input = document.getElementById('perf-dni');
  if (input.value === "") {
    input.classList.remove('is-invalid-custom', 'is-valid-custom');
    document.getElementById('perf-dni-feed').classList.remove('show');
    return;
  }
  toggleVal(input, /^\d{7,8}(-[A-Z0-9]{1,3})?$/, 'perf-dni-feed');
}

function valPerfPwd() {
  toggleVal(document.getElementById('perf-pwd-new'), /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&.-])[A-Za-z\d@$!%*?&.-]{8,}$/, 'perf-pwd-feed');
  valPerfPwdMatch();
}

function valPerfPwdMatch() {
  const p1 = document.getElementById('perf-pwd-new').value;
  const p2 = document.getElementById('perf-pwd-conf');
  const feed = document.getElementById('perf-pwd-match-feed');

  if (p2.value === "") return;

  if (p1 === p2.value) {
    p2.classList.add('is-valid-custom');
    p2.classList.remove('is-invalid-custom');
    feed.classList.remove('show');
  } else {
    p2.classList.add('is-invalid-custom');
    p2.classList.remove('is-valid-custom');
    feed.classList.add('show');
  }
}