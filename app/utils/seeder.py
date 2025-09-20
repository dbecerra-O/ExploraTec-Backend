from sqlalchemy.orm import Session
from app.database import engine, SessionLocal, drop_all_tables
from app.models.user import User
from app.models.scene import Scene, LinkHotspot, InfoHotspot, SceneLevel
from app.models.chat import Conversation, Message, MessageFeedback
from app.crud.user import user_crud
from app.crud.scene import scene_crud
from app.schemas.user import UserCreate
from app.schemas.scene import SceneCreate, LinkHotspotCreate, InfoHotspotCreate, SceneLevelCreate
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    """Crear solo 2 escenas básicas"""
    
    scenes = [
        {
            "scene_key": "0-entrada",
            "name": "Entrada",
            "face_size": 1024,
            "initial_yaw": 2.068,
            "initial_pitch": 0.033,
            "initial_fov": 1.393,
            "link_hotspots": [
                LinkHotspotCreate(yaw=1.92, pitch=-0.002, rotation=0, target_scene_id="1-patio-central")
            ],
            "info_hotspots": [],
            "levels": [
                SceneLevelCreate(tile_size=256, size=256, fallback_only=True),
                SceneLevelCreate(tile_size=512, size=512, fallback_only=False)
            ]
        },
        {
            "scene_key": "1-patio-central",
            "name": "Patio Central",
            "face_size": 1024,
            "initial_yaw": -0.374,
            "initial_pitch": 0.109,
            "initial_fov": 1.393,
            "link_hotspots": [
                LinkHotspotCreate(yaw=2.753, pitch=-0.013, rotation=0, target_scene_id="0-entrada")
            ],
            "info_hotspots": [
                InfoHotspotCreate(yaw=1.701, pitch=-0.049, title="Cafetín", text="El cafetín de Tecsup es un espacio diseñado para brindar comodidad donde los estudiantes pueden disfrutar de snacks y bebidas."),
                InfoHotspotCreate(yaw=-2.520, pitch=-0.018, title="Secretaría", text="La secretaría atiende las consultas administrativas y académicas de los estudiantes.")
            ],
            "levels": [
                SceneLevelCreate(tile_size=256, size=256, fallback_only=True),
                SceneLevelCreate(tile_size=512, size=512, fallback_only=False)
            ]
        }
    ]
    
    for scene_data in scenes:
        existing_scene = scene_crud.get_scene_by_key(db, scene_key=scene_data["scene_key"])
        if not existing_scene:
            scene_create = SceneCreate(**scene_data)
            scene = scene_crud.create_scene(db=db, scene=scene_create)
            logger.info(f"Escena creada: {scene.scene_key} - {scene.name}")

def seed_users(db: Session):
    """Crear usuarios básicos"""
    
    # Usuario administrador
    admin_data = UserCreate(
        email="admin@tecsup.edu.pe",
        username="admin",
        full_name="Administrador Tecsup",
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
        full_name="Juan Pérez",
        password="student123",
        is_active=True
    )
    
    existing_student = user_crud.get_user_by_username(db, username="estudiante")
    if not existing_student:
        student_user = user_crud.create_user(db=db, user=student_data)
        logger.info(f"Usuario estudiante creado: {student_user.username}")

def run_seeder():
    """Ejecutar el seeder básico"""
    logger.info("Iniciando seeder básico del Tour Virtual Tecsup...")
    
    try:
        # Borrar base de datos
        drop_all_tables()
        
        # Crear tablas
        create_tables()
        
        # Crear sesión
        db = SessionLocal()
        
        try:
            # Sembrar datos básicos
            seed_users(db)
            seed_basic_scenes(db)
            
            # Estadísticas
            total_users = db.query(User).count()
            total_scenes = db.query(Scene).count()
            
            logger.info("=" * 50)
            logger.info("TOUR VIRTUAL TECSUP - SEEDER BÁSICO COMPLETO")
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
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error ejecutando seeder: {e}")
        raise

if __name__ == "__main__":
    run_seeder()