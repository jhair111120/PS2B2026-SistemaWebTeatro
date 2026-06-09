// static/js/pages/users/perfil.js

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

document.addEventListener("DOMContentLoaded", function () {
  const container = document.getElementById('sesiones-container');
  if (!container) return;

  const url = container.getAttribute('data-url');

  function actualizarSesiones() {
    const syncIcon = document.getElementById('sync-icon');
    if (syncIcon) syncIcon.classList.add('fa-spin');

    fetch(url + '?t=' + new Date().getTime(), { cache: 'no-store' })
      .then(response => {
        if (!response.ok) throw new Error('Error en la red');
        return response.json();
      })
      .then(data => {
        if (data.error) return;

        let html = '';
        data.forEach(s => {
          let iconClass = 'fa-laptop';
          if (s.sistema_operativo === 'Windows') iconClass = 'fa-windows';
          else if (s.sistema_operativo === 'Android') iconClass = 'fa-android';
          else if (s.sistema_operativo === 'iOS' || s.sistema_operativo === 'MacOS') iconClass = 'fa-apple';

          html += `
                <div class="d-flex justify-content-between align-items-center border-bottom pb-3 mb-3" style="border-color: #333 !important;">
                  <div>
                    <div class="fw-bold text-white small">
                      <i class="fab ${iconClass} me-2 text-white-50"></i>${s.sistema_operativo} • ${s.navegador}
                    </div>
                    <div class="text-white-50 mt-1" style="font-size: 0.8rem;">
                      <i class="fas fa-map-marker-alt me-1"></i> ${s.ip_address} &nbsp;•&nbsp; 
                      <i class="far fa-clock me-1"></i> ${s.tiempo_str}
                    </div>
                  </div>
                `;

          if (s.is_current) {
            html += `<span class="status-badge"><i class="fas fa-circle me-1" style="font-size: 0.5rem;"></i> Actual</span></div>`;
          } else {
            html += `
                    <button type="button" class="btn btn-link text-danger small fw-bold text-decoration-none p-0" 
                            data-bs-toggle="modal" data-bs-target="#confirmSessionModal" 
                            onclick="document.getElementById('modal_session_key').value = '${s.session_key}'">Cerrar sesión</button>
                    </div>`;
          }
        });

        if (data.length === 0) {
          html = '<p class="text-white-50 small">No hay registro de sesiones para mostrar.</p>';
        }

        container.innerHTML = html;
        if (syncIcon) syncIcon.classList.remove('fa-spin');
      })
      .catch(error => {
        if (syncIcon) syncIcon.classList.remove('fa-spin');
      });
  }

  const btnSync = document.getElementById('btn-sync-sesiones');
  if (btnSync) {
    btnSync.addEventListener('click', actualizarSesiones);
  }

  actualizarSesiones();
  setInterval(actualizarSesiones, 10000);
});