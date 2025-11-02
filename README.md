# FastAPI JWT Authentication System

Sistema completo de autenticación con JWT usando FastAPI, SQLAlchemy, PostgreSQL y bcrypt.

## 📁 Estructura del Proyecto

```
my_fastapi_app/
├── app/
│   ├── main.py              # Aplicación principal
│   ├── config.py            # Configuración
│   ├── database.py          # Configuración de BD
│   ├── dependencies.py      # Dependencias de autenticación
│   ├── models/
│   │   ├── chat.py          # Modelo de chat
│   │   ├── scene.py         # Modelo de scene
│   │   ├── knowledge.py     # Modelo de knowledge
│   │   ├── note.py          # Modelo de note
│   │   └── user.py          # Modelo de usuario
│   ├── schemas/
│   │   ├── user.py          # Esquemas de usuario
│   │   ├── scene.py         # Esquemas de scene
│   │   ├── event.py         # Esquemas de events
│   │   ├── knowledge.py     # Esquemas de knowledge
│   │   ├── note.py          # Esquemas de note
│   │   ├── chat.py          # Esquemas de chat
│   │   └── token.py         # Esquemas de token
│   ├── crud/
│   │   ├── user.py          # Operaciones CRUD de user
│   │   ├── chat.py          # Operaciones CRUD de chat
│   │   ├── event.py         # Operaciones CRUD de events
│   │   ├── knowledge.py     # Operaciones CRUD de knowledge
│   │   ├── note.py          # Operaciones CRUD de note
│   │   └── scene.py         # Operaciones CRUD de scene
│   ├── routers/
│   │   ├── auth.py          # Autenticación
│   │   ├── events.py        # Rutas de eventos
│   │   ├── notes.py         # Rutas de citas
│   │   ├── suggestions.py   # Rutas de sugerencias
│   │   ├── chatbot.py       # Rutas de chatbot
│   │   ├── user_scenes.py   # Rutas de escenas de usuario
│   │   ├── users.py         # Rutas de usuarios
│   │   └── admin.py         # Rutas de administrador
│   ├── core/
│   │   └── security.py      # Funciones de seguridad
│   └── utils/
│       └── seeder.py        # Datos de prueba
├── .env                     # Variables de entorno
├── .env.example             # Variables de entorno de ejemplo
├── requirements.txt         # Dependencias
├── run_seeder.py            # Seeder ejecutable
└── README.md
```

## ⚡ Instalación y Configuración

### 1. Clonar y configurar el entorno

```bash
# Crear directorio del proyecto
mkdir my_fastapi_app
cd my_fastapi_app

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

Crear el archivo `.env` con el contenido proporcionado o actualizar la `SECRET_KEY`.

### 3. Ejecutar la aplicación

```bash
# Desde el directorio raíz del proyecto
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

La aplicación estará disponible en: `http://localhost:8000`

## 📚 Documentación de la API

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🔐 Usuarios de Prueba

El seeder crea automáticamente estos usuarios:

### Administrador
- **Username**: `admin`
- **Email**: `admin@tecsup.edu.pe`
- **Password**: `admin123`
- **Rol**: Administrador

### Administrador
- **Username**: `estudiante`
- **Email**: `estudiante@tecsup.edu.pe`
- **Password**: `student123`
- **Rol**: Usuario

## 🔄 Seeder

```bash
# Ejecutar el seeder para la base de datos
python run_seeder.py
```

## 🛡️ Seguridad

- Contraseñas hasheadas con bcrypt
- Tokens JWT con expiración configurable
- Middleware CORS configurado
- Validación de datos con Pydantic
- Separación de roles (usuario/administrador)

## 🔧 Configuración Avanzada

### Cambiar configuración de JWT

En `.env`:
```env
DATABASE_URL=URL_DB
SECRET_KEY=tu-nueva-clave-super-secreta
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
OPENAI_API_KEY=API_KEY
```