from sqlalchemy.orm import Session
from app.database import engine, SessionLocal
from app.models.user import User
from app.models.scene import Scene
from app.crud.user import user_crud
from app.crud.scene import scene_crud
from app.schemas.user import UserCreate
from app.schemas.scene import SceneCreate
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def drop_tables():
    """Eliminar todas las tablas"""
    from app.database import drop_all_tables
    drop_all_tables()

def create_tables():
    """Crear todas las tablas"""
    from app.database import Base
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Tablas creadas correctamente")
    except Exception as e:
        logger.error(f"Error creando tablas: {e}")
        raise

def seed_basic_scenes(db: Session):
    """Crear escenas"""
    
    scenes = [
        {
            "scene_key": "0-entrada",
            "name": "Entrada"
        },
        {
            "scene_key": "1-patio-central",
            "name": "Patio Central"
        }
    ]
    
    for scene_data in scenes:
        existing_scene = scene_crud.get_scene_by_key(db, scene_key=scene_data["scene_key"])
        if not existing_scene:
            scene_create = SceneCreate(**scene_data)
            scene = scene_crud.create_scene(db=db, scene=scene_create)
            logger.info(f"Escena creada: {scene.scene_key} - {scene.name}")

def seed_users(db: Session):
    """Crear usuarios"""
    
    # Usuario administrador
    admin_data = UserCreate(
        email="admin@tecsup.edu.pe",
        username="admin",
        password="admin123",
        is_active=True
    )
    
    existing_admin = user_crud.get_user_by_username(db, username="admin")
    if not existing_admin:
        admin_user = user_crud.create_admin_user(db=db, user=admin_data)
        logger.info(f"Usuario administrador creado: {admin_user.username}")
    
    # Usuario estudiante
    student_data = UserCreate(
        email="estudiante@tecsup.edu.pe",
        username="estudiante",
        password="student123",
        is_active=True
    )
    
    existing_student = user_crud.get_user_by_username(db, username="estudiante")
    if not existing_student:
        student_user = user_crud.create_user(db=db, user=student_data)
        logger.info(f"Usuario estudiante creado: {student_user.username}")

def run_seeder():
    """Ejecutar el seeder basico"""
    logger.info("Iniciando seeder...")
    
    # Eliminar y crear tablas
    drop_tables()
    create_tables()
    
    # Crear sesión
    db = SessionLocal()
    
    try:
        # Agregar datos básicos
        seed_users(db)
        seed_basic_scenes(db)
        
        # Estadísticas
        total_users = db.query(User).count()
        total_scenes = db.query(Scene).count()
        
        logger.info("=" * 50)
        logger.info("TOUR VIRTUAL TECSUP - SEEDER EJECUTADO")
        logger.info("=" * 50)
        logger.info(f"Usuarios: {total_users}")
        logger.info(f"Escenas: {total_scenes}")
        logger.info("=" * 50)
        logger.info("CREDENCIALES:")
        logger.info("Admin: admin / admin123")
        logger.info("Estudiante: estudiante / student123")
        logger.info("=" * 50)
        logger.info("API: http://localhost:8000")
        logger.info("Docs: http://localhost:8000/docs")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"Error ejecutando seeder: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run_seeder()