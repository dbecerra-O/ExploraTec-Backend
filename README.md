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
│   │   └── user.py          # Modelo de usuario
│   ├── schemas/
│   │   ├── user.py          # Esquemas de usuario
│   │   ├── scene.py         # Esquemas de escena
│   │   ├── chat.py          # Esquemas de chat
│   │   └── token.py         # Esquemas de token
│   ├── crud/
│   │   ├── user.py          # Operaciones CRUD de user
│   │   ├── chat.py          # Operaciones CRUD de chat
│   │   └── scene.py          # Operaciones CRUD de scene
│   ├── routers/
│   │   ├── auth.py          # Autenticación
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

## 🛠️ Endpoints Principales

### Autenticación
- `POST /auth/register` - Registrar nuevo usuario
- `POST /auth/login` - Iniciar sesión
- `POST /auth/token` - Obtener token (OAuth2)

### Usuarios
- `GET /users/me` - Perfil del usuario actual
- `PUT /users/me` - Actualizar perfil
- `GET /users/profile/{user_id}` - Ver perfil público

### Administrador
- `GET /admin/users` - Listar todos los usuarios
- `POST /admin/users` - Crear usuario
- `POST /admin/users/admin` - Crear administrador
- `PUT /admin/users/{user_id}` - Actualizar usuario
- `DELETE /admin/users/{user_id}` - Eliminar usuario
- `PUT /admin/users/{user_id}/toggle-admin` - Cambiar rol de admin

### Rutas de Ejemplo
- `GET /` - Página de inicio (público)
- `GET /protected` - Ruta protegida (requiere login)
- `GET /admin-only` - Solo administradores
- `GET /health` - Estado de la aplicación

## 🔄 Seeder Automático

La aplicación incluye un seeder que:
- Se ejecuta automáticamente al iniciar la aplicación
- Elimina todas las tablas existentes
- Crea las tablas nuevamente
- Inserta datos de prueba

Esto significa que **cada vez que reinicies la aplicación, la base de datos se resetea** con los datos de prueba.

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
GROQ_API_KEY=API_KEY  
ANTHROPIC_API_KEY=API_KEY
```

### Desactivar el seeder automático

En `app/main.py`, comenta o modifica la función `lifespan` para no ejecutar el seeder.

## 🚀 Despliegue

Para producción:
1. Cambiar `SECRET_KEY` por una clave segura
2. Configurar CORS con dominios específicos
3. Usar un servidor PostgreSQL dedicado
4. Configurar variables de entorno de producción
5. Desactivar el seeder automático

## 📝 Notas

- La base de datos se resetea en cada inicio (por el seeder)
- Los tokens JWT expiran según la configuración
- Se puede iniciar sesión con username o email
- Los administradores tienen acceso completo a la gestión de usuarios