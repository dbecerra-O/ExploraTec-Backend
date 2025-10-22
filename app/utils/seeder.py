from sqlalchemy.orm import Session
from app.database import engine, SessionLocal
from app.models.user import User
from app.models.scene import Scene
from app.models.chat import Conversation, Message, MessageFeedback
from app.crud.user import user_crud
from app.crud.scene import scene_crud
from app.schemas.user import UserCreate
from app.schemas.scene import SceneCreate
from app.models.knowledge import KnowledgeBase
from app.services.embeddings import embed_texts, get_openai_client

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
        {"scene_key": "0-entrada", "name": "Entrada Principal"},
        {"scene_key": "1-patio-central", "name": "Patio Central"},
        {"scene_key": "2-biblioteca", "name": "Biblioteca"},
        {"scene_key": "3-laboratorio-mecanica", "name": "Laboratorio de Mecánica"},
        {"scene_key": "4-comedor", "name": "Comedor Estudiantil"},
        {"scene_key": "5-auditorio", "name": "Auditorio Principal"},
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

def seed_knowledge(db: Session):
    """Agregar entradas de ejemplo a la base de conocimiento (knowledge_base)"""
    # Obtener algunas escenas para relacionar contenido si aplica
    entrada = scene_crud.get_scene_by_key(db, "0-entrada")
    biblioteca = scene_crud.get_scene_by_key(db, "2-biblioteca")

    knowledge_entries = [
        {
            "content": "La biblioteca de Tecsup ofrece préstamo de libros, salas de estudio grupal y acceso a bases de datos digitales.",
            "category": "servicios",
            "subcategory": "biblioteca",
            "scene_id": biblioteca.id if biblioteca else None
        },
        {
            "content": "La carrera de Mecatrónica Industrial tiene una duración aproximada de 3 años (6 semestres).",
            "category": "carreras",
            "subcategory": "mecatronica",
            "scene_id": None
        },
        {
            "content": "Para postular a Tecsup, debes completar la solicitud en línea, presentar certificado de estudios secundarios y rendir el examen de admisión.",
            "category": "admisiones",
            "subcategory": "requisitos",
            "scene_id": None
        },
        {
            "content": "El comedor estudiantil se encuentra en el primer piso, cerca del patio central, y ofrece opciones de comida económica para estudiantes.",
            "category": "servicios",
            "subcategory": "comedor",
            "scene_id": entrada.id if entrada else None
        },
        {
            "content": "Los docentes expertos dentro de tecnologia digital incluyen especialistas en desarrollo de software, redes y ciberseguridad. Como Silvia Montoya y Jaime Gomez",
            "category": "carreras",
            "subcategory": "Tecnología digital",
            "scene_id": None
        }
    ]

    added = 0
    # Primero insertar filas sin embeddings
    created_kbs = []
    for entry in knowledge_entries:
        kb = KnowledgeBase(
            content=entry["content"],
            category=entry["category"],
            subcategory=entry.get("subcategory"),
            scene_id=entry.get("scene_id"),
            is_active=True
        )
        db.add(kb)
        try:
            db.commit()
            db.refresh(kb)
            created_kbs.append(kb)
            added += 1
        except Exception as e:
            db.rollback()
            logger.error(f"Error insertando knowledge entry: {e}")

    # Si hay clave de OpenAI, intentar generar embeddings en batch y guardarlos
    try:
        # Esto verifica si la variable de entorno está presente y si el cliente puede inicializarse
        get_openai_client()
        texts = [k.content for k in created_kbs]
        if texts:
            embeddings = embed_texts(texts)
            for kb_obj, emb in zip(created_kbs, embeddings):
                kb_obj.embedding = emb
                db.add(kb_obj)
            db.commit()
            logger.info("Embeddings generados y guardados para entries seed.")
    except Exception as e:
        # No crítico: si falla, las filas quedan sin embedding y se pueden calcular luego
        logger.warning(f"No se pudieron generar embeddings en el seeder: {e}")

    logger.info(f"✅ {added} entradas de knowledge_base creadas.")

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
        # Agregar knowledge base
        seed_knowledge(db)
        
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