from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.routers.auth import router as auth_router
from app.routers.users import router as users_router  
from app.routers.admin import router as admin_router
from app.routers.scenes import router as scenes_router
from app.routers.user_scenes import router as user_scenes_router
from app.dependencies import get_current_active_user, get_current_admin_user
from app.models.user import User
from app.utils.seeder import run_seeder

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lifespan event handler para ejecutar el seeder al inicio
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Iniciando aplicación...")
    try:
        # Ejecutar seeder al iniciar la aplicación
        run_seeder()
        logger.info("Seeder ejecutado correctamente")
    except Exception as e:
        logger.error(f"Error ejecutando seeder: {e}")
    
    yield    
    # Shutdown
    logger.info("Cerrando aplicación...")

# Crear la aplicación FastAPI
app = FastAPI(
    title="FastAPI JWT Auth System",
    description="Sistema de autenticación con JWT para usuarios y administradores",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica los dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(admin_router)
app.include_router(scenes_router)
app.include_router(user_scenes_router)

# Rutas de ejemplo para probar la autenticación
@app.get("/")
async def root():
    """Endpoint público de bienvenida"""
    return {
        "message": "¡Bienvenido al Tour Virtual 360° de Tecsup con FastAPI y JWT!",
        "description": "Sistema de autenticación para recorrido virtual del campus",
        "docs": "/docs",
        "endpoints": {
            "auth": {
                "register": "POST /auth/register",
                "login": "POST /auth/login",
                "token": "POST /auth/token"
            },
            "users": {
                "me": "GET /users/me",
                "update_me": "PUT /users/me",
                "profile": "GET /users/profile/{user_id}"
            },
            "scenes": {
                "list": "GET /scenes/",
                "get_scene": "GET /scenes/{scene_id}",
                "get_by_key": "GET /scenes/key/{scene_key}",
                "create": "POST /scenes/ (admin only)",
                "update": "PUT /scenes/{scene_id} (admin only)",
                "delete": "DELETE /scenes/{scene_id} (admin only)"
            },
            "navigation": {
                "enter_scene": "POST /user/enter-scene/{scene_key}",
                "current_scene": "GET /user/current-scene", 
                "leave_scene": "POST /user/leave-scene"
            },
            "admin": {
                "users": "GET /admin/users",
                "create_user": "POST /admin/users",
                "create_admin": "POST /admin/users/admin",
                "get_user": "GET /admin/users/{user_id}",
                "update_user": "PUT /admin/users/{user_id}",
                "delete_user": "DELETE /admin/users/{user_id}",
                "toggle_admin": "PUT /admin/users/{user_id}/toggle-admin"
            }
        },
        "tecsup_scenes": [
            "0-entrada", "1-patio-central", "26-biblioteca", 
            "6-polideportivo", "14-salon-701", "15-salones-de-mecanica"
        ]
    }

@app.get("/protected")
async def protected_route(current_user: User = Depends(get_current_active_user)):
    """Ruta protegida que requiere autenticación"""
    return {
        "message": f"¡Hola {current_user.username}! Esta es una ruta protegida.",
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "is_admin": current_user.is_admin
        }
    }

@app.get("/admin-only")
async def admin_only_route(current_admin: User = Depends(get_current_admin_user)):
    """Ruta que solo pueden acceder los administradores"""
    return {
        "message": f"¡Hola {current_admin.username}! Eres un administrador.",
        "admin": {
            "id": current_admin.id,
            "username": current_admin.username,
            "email": current_admin.email,
        }
    }

# Health check
@app.get("/health")
async def health_check():
    """Endpoint para verificar el estado de la aplicación"""
    return {"status": "healthy", "message": "La aplicación está funcionando correctamente"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)