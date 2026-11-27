// Configuración dinámica de la URL base de la API y del Panel Django Admin
// Si corre en localhost / 127.0.0.1 usa el backend local en puerto 8000
// Si está en producción (Render/Netlify) se conecta a la URL de Render

const isLocal = window.location.hostname === 'localhost' || 
                window.location.hostname === '127.0.0.1' || 
                window.location.protocol === 'file:';

window.API_BASE_URL = isLocal
  ? 'http://127.0.0.1:8000/api'
  : 'https://gestor-streaming-backend.onrender.com/api';

window.DJANGO_ADMIN_URL = isLocal
  ? 'http://127.0.0.1:8000/admin/'
  : 'https://gestor-streaming-backend.onrender.com/admin/';
