from sqlalchemy.orm import Session
from app.database import engine, SessionLocal
from app.models.user import User
from app.models.scene import Scene, LinkHotspot, InfoHotspot, SceneLevel
from app.models.chat import Conversation, Message, MessageFeedback
from app.crud.user import user_crud
from app.crud.scene import scene_crud
from app.crud import chat as chat_crud  # ✅ importar todo el módulo, no sub-objetos
from app.schemas.user import UserCreate
from app.schemas.scene import SceneCreate, LinkHotspotCreate, InfoHotspotCreate, SceneLevelCreate
from app.schemas.chat import ConversationCreate, MessageFeedbackCreate, MessageCreate
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_tables():
    """Crear todas las tablas"""
    from app.database import Base
    Base.metadata.create_all(bind=engine)
    logger.info("Tablas creadas correctamente")


def drop_tables():
    """Eliminar todas las tablas"""
    from app.database import Base
    Base.metadata.drop_all(bind=engine)
    logger.info("Tablas eliminadas correctamente")


def seed_tecsup_scenes(db: Session):
    """Crear escenas reales de Tecsup basadas en el tour virtual"""
    
    tecsup_scenes = [
        {
            "scene_key": "0-entrada",
            "name": "Entrada",
            "face_size": 1024,
            "initial_yaw": 2.068067774237692,
            "initial_pitch": 0.03346392230207229,
            "initial_fov": 1.3926760049349705,
            "link_hotspots": [
                LinkHotspotCreate(yaw=1.9204639688937917, pitch=-0.002028122994131465, rotation=0, target_scene_id="1-patio-central")
            ],
            "info_hotspots": [],
            "levels": [
                SceneLevelCreate(tile_size=256, size=256, fallback_only=True),
                SceneLevelCreate(tile_size=512, size=512, fallback_only=False),
                SceneLevelCreate(tile_size=512, size=1024, fallback_only=False)
            ]
        },
        {
            "scene_key": "1-patio-central",
            "name": "Patio Central",
            "face_size": 1024,
            "initial_yaw": -0.37378225865015224,
            "initial_pitch": 0.10870001243675098,
            "initial_fov": 1.3926760049349705,
            "link_hotspots": [
                LinkHotspotCreate(yaw=2.752987778948084, pitch=-0.012615710038859973, rotation=0, target_scene_id="0-entrada"),
                LinkHotspotCreate(yaw=-0.08231905245866855, pitch=0.006307545346725618, rotation=0, target_scene_id="2-camino")
            ],
            "info_hotspots": [
                InfoHotspotCreate(yaw=1.7008975200473486, pitch=-0.048665228131163474, title="Cafetín", text="El cafetín de Tecsup es un espacio diseñado para brindar comodidad donde los estudiantes pueden disfrutar de snacks, bebidas y alimentos."),
                InfoHotspotCreate(yaw=-2.5197525587454024, pitch=-0.017992820492674255, title="Secretaría", text="La secretaría de Tecsup es el punto de referencia para atender las consultas administrativas y académicas de los estudiantes."),
                InfoHotspotCreate(yaw=-0.8002573703119804, pitch=0.02753771597134147, title="Auditorio", text="El auditorio de Tecsup es un espacio diseñado para el aprendizaje, la innovación y el intercambio de ideas.")
            ],
            "levels": [
                SceneLevelCreate(tile_size=256, size=256, fallback_only=True),
                SceneLevelCreate(tile_size=512, size=512, fallback_only=False),
                SceneLevelCreate(tile_size=512, size=1024, fallback_only=False)
            ]
        },
        {
            "scene_key": "2-camino",
            "name": "Camino",
            "face_size": 1024,
            "initial_yaw": 0.7804664979256959,
            "initial_pitch": 0.07928142668257365,
            "initial_fov": 1.3926760049349705,
            "link_hotspots": [
                LinkHotspotCreate(yaw=-2.4241354608098664, pitch=0.08603545120801748, rotation=0, target_scene_id="1-patio-central"),
                LinkHotspotCreate(yaw=0.7225895516070011, pitch=0.005992476736270902, rotation=0, target_scene_id="4-pabellon-7")
            ],
            "info_hotspots": [],
            "levels": [
                SceneLevelCreate(tile_size=256, size=256, fallback_only=True),
                SceneLevelCreate(tile_size=512, size=512, fallback_only=False),
                SceneLevelCreate(tile_size=512, size=1024, fallback_only=False)
            ]
        },
        {
            "scene_key": "4-pabellon-7",
            "name": "Pabellón 7",
            "face_size": 1024,
            "initial_yaw": 2.7890632846116805,
            "initial_pitch": 0.0979808966190987,
            "initial_fov": 1.3926760049349705,
            "link_hotspots": [
                LinkHotspotCreate(yaw=-0.8328945391073148, pitch=-0.04981811906169753, rotation=0, target_scene_id="14-salon-701"),
                LinkHotspotCreate(yaw=-0.9797354094636308, pitch=-0.058074825105254746, rotation=0, target_scene_id="2-camino")
            ],
            "info_hotspots": [],
            "levels": [
                SceneLevelCreate(tile_size=256, size=256, fallback_only=True),
                SceneLevelCreate(tile_size=512, size=512, fallback_only=False),
                SceneLevelCreate(tile_size=512, size=1024, fallback_only=False)
            ]
        },
        {
            "scene_key": "14-salon-701",
            "name": "Salón 701",
            "face_size": 1024,
            "initial_yaw": 0.3499848226088904,
            "initial_pitch": 0.13118616109151837,
            "initial_fov": 1.3926760049349705,
            "link_hotspots": [
                LinkHotspotCreate(yaw=-2.8695697069294415, pitch=0.08315707590686472, rotation=0, target_scene_id="4-pabellon-7")
            ],
            "info_hotspots": [
                InfoHotspotCreate(yaw=0.32317072286488724, pitch=0.05321212207160464, title="Laboratorio de Computación", text="Laboratorio equipado con tecnología de última generación para el desarrollo de competencias digitales y programación.")
            ],
            "levels": [
                SceneLevelCreate(tile_size=256, size=256, fallback_only=True),
                SceneLevelCreate(tile_size=512, size=512, fallback_only=False),
                SceneLevelCreate(tile_size=512, size=1024, fallback_only=False)
            ]
        },
        {
            "scene_key": "6-polideportivo",
            "name": "Polideportivo",
            "face_size": 1024,
            "initial_yaw": 2.855754504708207,
            "initial_pitch": -0.0039251213590034695,
            "initial_fov": 1.3926760049349705,
            "link_hotspots": [
                LinkHotspotCreate(yaw=-0.14334777072640748, pitch=-0.08332311174008744, rotation=0, target_scene_id="1-patio-central")
            ],
            "info_hotspots": [
                InfoHotspotCreate(yaw=-1.8808330011448735, pitch=0.0003712450725377181, title="Cancha de Básquet", text="Cancha diseñada para fomentar el deporte y la actividad física entre los estudiantes."),
                InfoHotspotCreate(yaw=2.751514009576252, pitch=0.02737968052720774, title="Cancha Principal", text="Espacio dedicado a la actividad física y el bienestar estudiantil con deportes como fútbol y futsal.")
            ],
            "levels": [
                SceneLevelCreate(tile_size=256, size=256, fallback_only=True),
                SceneLevelCreate(tile_size=512, size=512, fallback_only=False),
                SceneLevelCreate(tile_size=512, size=1024, fallback_only=False)
            ]
        },
        {
            "scene_key": "26-biblioteca",
            "name": "Biblioteca",
            "face_size": 1024,
            "initial_yaw": -1.5889819252946982,
            "initial_pitch": 0.0588478331193123,
            "initial_fov": 1.3926760049349705,
            "link_hotspots": [
                LinkHotspotCreate(yaw=-1.945504251554631, pitch=0.0011027762344539838, rotation=0, target_scene_id="1-patio-central")
            ],
            "info_hotspots": [
                InfoHotspotCreate(yaw=-1.6839102988183416, pitch=-0.01863227684441071, title="Biblioteca", text="La biblioteca de Tecsup es un espacio fundamental para el desarrollo académico con amplia colección de libros, revistas y recursos digitales.")
            ],
            "levels": [
                SceneLevelCreate(tile_size=256, size=256, fallback_only=True),
                SceneLevelCreate(tile_size=512, size=512, fallback_only=False),
                SceneLevelCreate(tile_size=512, size=1024, fallback_only=False)
            ]
        },
        {
            "scene_key": "15-salones-de-mecanica",
            "name": "Salones de Mecánica",
            "face_size": 1024,
            "initial_yaw": 2.579913967038893,
            "initial_pitch": 0.20462232258914526,
            "initial_fov": 1.3926760049349705,
            "link_hotspots": [
                LinkHotspotCreate(yaw=2.532295439513698, pitch=0.07767178102434258, rotation=0, target_scene_id="1-patio-central")
            ],
            "info_hotspots": [
                InfoHotspotCreate(yaw=1.951353050988632, pitch=0.1436105184965868, title="Salón de Mecánica", text="Espacio dedicado a la formación práctica con herramientas y equipos especializados para ingeniería mecánica.")
            ],
            "levels": [
                SceneLevelCreate(tile_size=256, size=256, fallback_only=True),
                SceneLevelCreate(tile_size=512, size=512, fallback_only=False),
                SceneLevelCreate(tile_size=512, size=1024, fallback_only=False)
            ]
        }
    ]
    
    for scene_data in tecsup_scenes:
        existing_scene = scene_crud.get_scene_by_key(db, scene_key=scene_data["scene_key"])
        if not existing_scene:
            scene_create = SceneCreate(**scene_data)
            scene = scene_crud.create_scene(db=db, scene=scene_create)
            logger.info(f"Escena creada: {scene.scene_key} - {scene.name}")
        else:
            logger.info(f"Escena {scene_data['scene_key']} ya existe")

def seed_users(db: Session):
    """Crear usuarios de prueba"""
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
    else:
        logger.info("Usuario administrador ya existe")

    test_users = [
        UserCreate(email="estudiante1@tecsup.edu.pe", username="estudiante1", password="student123", is_active=True),
        UserCreate(email="estudiante2@tecsup.edu.pe", username="estudiante2", password="student123", is_active=True),
        UserCreate(email="visitante@example.com", username="visitante", password="visitor123", is_active=True),
        UserCreate(email="profesor@tecsup.edu.pe", username="profesor", password="teacher123", is_active=True),
        UserCreate(email="postulante@example.com", username="postulante", password="prospect123", is_active=True)
    ]

    for user_data in test_users:
        existing_user = user_crud.get_user_by_username(db, username=user_data.username)
        if not existing_user:
            user = user_crud.create_user(db=db, user=user_data)
            logger.info(f"Usuario creado: {user.username}")
        else:
            logger.info(f"Usuario {user_data.username} ya existe")

def run_seeder():
    logger.info("Iniciando seeder del Tour Virtual Tecsup...")

    drop_tables()
    create_tables()

    db = SessionLocal()

    try:
        seed_users(db)
        seed_tecsup_scenes(db)

        total_users = db.query(User).count()
        total_scenes = db.query(Scene).count()
        total_hotspots = db.query(LinkHotspot).count() + db.query(InfoHotspot).count()

        logger.info("=" * 70)
        logger.info("TOUR VIRTUAL TECSUP - SISTEMA COMPLETO INICIALIZADO")
        logger.info("=" * 70)
        logger.info(f"Usuarios: {total_users} (Admins: {db.query(User).filter(User.is_admin == True).count()}, Activos: {db.query(User).filter(User.is_active == True).count()})")
        logger.info(f"Escenas: {total_scenes} | Hotspots: {total_hotspots}")

        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"Error ejecutando seeder: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seeder()
