# Plataforma de Gestión de Suscripciones y Cobros de Streaming (Netflix y Crunchyroll)

Plataforma web integral orientada a la administración organizada, automatizada y escalable de suscripciones compartidas de servicios de streaming (Netflix y Crunchyroll). Permite gestionar cuentas maestras, perfiles individuales asignados a clientes, control de fechas de corte, verificación y aprobación de comprobantes de pago y generación de recordatorios oportunos vía WhatsApp.

---

## 🚀 Tecnologías Utilizadas

### Front-End
- **HTML5 & CSS3**: Estructura semántica y diseño visual personalizado.
- **Bootstrap 5**: Maquetación responsiva, componentes visuales y utilidades de espaciado.
- **Tipografía Inter**: Lectura optimizada e interfaz moderna y profesional.
- **JavaScript (ES6+)**: Interacción dinámica, manipulación del DOM y consumo asíncrono de API mediante `fetch`.

### Back-End
- **Python (3.10+)**: Lenguaje robusto para lógica de servidor.
- **Django**: Framework web para desarrollo rápido, seguro y estructurado.
- **SQLite3**: Base de datos ligera e integrada para entorno de desarrollo local.
- **PostgreSQL**: Motor de base de datos relacional para el entorno de producción (despliegue en Render).
- **python-dotenv**: Gestión segura de variables de entorno mediante archivos `.env`.

---

## 📁 Estructura del Proyecto

```text
gestor-streaming/
├── backend/                  # Código fuente del Back-End (Django)
│   ├── config/               # Configuración central del proyecto Django (settings, urls, wsgi)
│   ├── .env.example          # Plantilla de variables de entorno requeridas
│   ├── requirements.txt      # Dependencias de paquetes de Python
│   └── manage.py             # Script de administración de Django
├── frontend/                 # Código fuente del Front-End (Cliente y Admin)
│   ├── assets/               # Hojas de estilo CSS personalizadas, scripts JS e imágenes
│   └── index.html            # Interfaz de usuario para clientes y panel administrativo
├── .gitignore                # Reglas de exclusión para Git (ignora .env, venv, sqlite3, etc.)
└── README.md                 # Documentación principal del repositorio
```

---

## ⚙️ Variables de Entorno Requeridas

Las credenciales y configuraciones sensibles se gestionan en el archivo `backend/.env` (no incluido en el repositorio por motivos de seguridad). Se provee la plantilla `backend/.env.example` con las siguientes variables:

| Variable | Descripción | Valor sugerido para desarrollo |
| :--- | :--- | :--- |
| `SECRET_KEY` | Clave criptográfica única de Django para firmas y sesiones. | Cadena aleatoria segura (e.g. `django-insecure-...`) |
| `DEBUG` | Indicador de modo depuración (`True` o `False`). | `True` |
| `ALLOWED_HOSTS` | Lista de hosts/dominios permitidos separados por comas. | `localhost,127.0.0.1` |
| `DATABASE_URL` | URL de conexión al motor de base de datos relacional. | `sqlite:///db.sqlite3` |

---

## 🛠️ Instalación y Puesta en Marcha Local

Sigue estos pasos para levantar el entorno de desarrollo en tu máquina local:

### 1. Clonar el repositorio
```bash
git clone https://github.com/hnginv04-afk/gestor-streaming.git
cd gestor-streaming
```

### 2. Configurar el Back-End (Django)
```bash
# Navegar a la carpeta backend
cd backend

# Crear entorno virtual de Python
python -m venv venv

# Activar el entorno virtual
# En Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# En Linux / macOS:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno locales
copy .env.example .env    # En Windows
# cp .env.example .env    # En Linux/macOS
```
> Edita el archivo `.env` recién creado y define un `SECRET_KEY` seguro y `DEBUG=True`.

### 3. Aplicar migraciones y crear superusuario
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. Iniciar el servidor de desarrollo
```bash
python manage.py runserver
```
El Back-End estará disponible en: `http://127.0.0.1:8000/`  
El panel de administración estará en: `http://127.0.0.1:8000/admin/`

### 5. Visualizar el Front-End
Puedes abrir el archivo `frontend/index.html` directamente en tu navegador o utilizando la extensión **Live Server** en Visual Studio Code.

---

## 📌 Convención de Commits
Este repositorio sigue la especificación de **Conventional Commits**:
- `feat:` Nuevas características o funcionalidades.
- `fix:` Corrección de errores o bugs.
- `docs:` Cambios o adiciones en documentación.
- `chore:` Tareas rutinarias de configuración y mantenimiento.
- `refactor:` Reestructuración de código sin alterar su comportamiento externo.
