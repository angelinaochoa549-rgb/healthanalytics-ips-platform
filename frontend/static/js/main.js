/**
 * main.js — inicialización global con control de roles
 */
(function () {
  const token = localStorage.getItem('access_token');
  const publicPaths = ['/login/'];

  if (!token && !publicPaths.includes(window.location.pathname)) {
    window.location.href = '/login/';
    return;
  }

  if (token) {
    const app = document.getElementById('app');
    if (app) app.style.display = 'flex';

    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const rol = user.role || '';

    // Mostrar info usuario
    const el = id => document.getElementById(id);
    if (el('sidebarUsername')) el('sidebarUsername').textContent = user.username || 'Usuario';
    if (el('sidebarRole')) el('sidebarRole').textContent = rol;
    if (el('userInitial')) el('userInitial').textContent = (user.username || 'U')[0].toUpperCase();

    // Control de menú por rol
    aplicarPermisos(rol);
  }

  // Reloj
  function updateClock() {
    const el = document.getElementById('currentTime');
    if (!el) return;
    el.textContent = new Date().toLocaleString('es-CO', {
      weekday: 'short', day: '2-digit', month: 'short',
      hour: '2-digit', minute: '2-digit',
    });
  }
  updateClock();
  setInterval(updateClock, 30000);
})();


function aplicarPermisos(rol) {
  const path = window.location.pathname;

  // Páginas restringidas por rol
  const restricciones = {
    'medico': ['/etl/', '/ml/'],
    'analista': ['/ml/'],
  };

  const bloqueadas = restricciones[rol] || [];

  // Redirigir si no tiene acceso a esta página
  if (bloqueadas.includes(path)) {
    window.location.href = '/dashboard/';
    return;
  }

  // Ocultar items del menú según rol
  if (rol === 'medico') {
    // Médico no ve ETL
    ocultarMenu('nav-etl');
  }

  if (rol === 'analista') {
    // Analista no ve ML
    ocultarMenu('nav-ml');
  }
}


function ocultarMenu(id) {
  const el = document.getElementById(id);
  if (el) el.style.display = 'none';
}


function logout() {
  const refresh = localStorage.getItem('refresh_token');
  if (refresh) {
    fetch('/api/auth/logout/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + localStorage.getItem('access_token')
      },
      body: JSON.stringify({ refresh }),
    }).catch(() => {});
  }
  localStorage.clear();
  window.location.href = '/login/';
}