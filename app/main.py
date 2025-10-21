from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.routers import auth, users, admin, chatbot, user_scenes, suggestions, notes
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
    title="FastAPI ExploraTec Back",
    description="Sistema chatbot para el Tour Virtual 360° de Tecsup",
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
for router in [auth, users, admin, chatbot, user_scenes, suggestions, notes]:
    app.include_router(router.router)

# Rutas de ejemplo para probar la autenticación
@app.get("/")
async def root():
    """Endpoint público de bienvenida"""
    return {
        "message": "¡Bienvenido al Tour Virtual 360° de Tecsup",
        "description": "Sistema de autenticación para recorrido virtual del campus",
        "docs": "/docs",
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