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
    
    scenes_data = [
        {"scene_key": "0-entrada", "name": "Entrada"},
        {"scene_key": "1-patio-central", "name": "Patio Central"},
        {"scene_key": "2-camino", "name": "Camino"},
        {"scene_key": "3-pabellon-4---piso-2-s", "name": "Pabellón 4 - Piso 2-S"},
        {"scene_key": "4-pabellon-7", "name": "Pabellón 7"},
        {"scene_key": "5-area-de-salones-4b", "name": "Área de Salones 4B"},
        {"scene_key": "6-polideportivo", "name": "Polideportivo"},
        {"scene_key": "7-area-de-tecnologia", "name": "Área de Tecnología"},
        {"scene_key": "8-area-de-mecanica", "name": "Área de Mecánica"},
        {"scene_key": "9-mecanica", "name": "Mecánica"},
        {"scene_key": "10-segundo-piso-e", "name": "Segundo Piso E"},
        {"scene_key": "11-segundo-piso-s", "name": "Segundo Piso S"},
        {"scene_key": "12-zona-verde", "name": "Zona Verde"},
        {"scene_key": "13-cerca-del-ajedrez", "name": "Cerca del Ajedrez"},
        {"scene_key": "14-salon-701", "name": "Salón 701"},
        {"scene_key": "15-salones-de-mecanica", "name": "Salones de Mecánica"},
        {"scene_key": "16-salon-702", "name": "Salón 702"},
        {"scene_key": "17-salon-704", "name": "Salón 704"},
        {"scene_key": "18-maquinitas", "name": "Maquinitas"},
        {"scene_key": "19-pabellon-4---piso-2-e", "name": "Pabellón 4 - Piso 2-E"},
        {"scene_key": "20-pabellon-4---piso-2-m", "name": "Pabellón 4 - Piso 2-M"},
        {"scene_key": "21-pabellon-4---piso-2--a", "name": "Pabellón 4 - Piso 2-A"},
        {"scene_key": "22-pabellon-4---piso-1", "name": "Pabellón 4 - Piso 1"},
        {"scene_key": "23-salon-pabellon-4", "name": "Salón Pabellón 4"},
        {"scene_key": "24-pabellon-4", "name": "Pabellón 4"},
        {"scene_key": "25-entrada-biblioteca", "name": "Entrada Biblioteca"},
        {"scene_key": "26-biblioteca", "name": "Biblioteca"},
        {"scene_key": "27-pabellon-14", "name": "Pabellón 14"},
        {"scene_key": "28-salon-1509", "name": "Salón 1509"}
    ]
    
    for scene_data in scenes_data:
        existing = scene_crud.get_scene_by_key(db, scene_data["scene_key"])
        if not existing:
            scene = scene_crud.create_scene(db, SceneCreate(**scene_data))
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
    biblioteca = scene_crud.get_scene_by_key(db, "26-biblioteca")
    poli = scene_crud.get_scene_by_key(db, "6-polideportivo")
    pabellon7 = scene_crud.get_scene_by_key(db, "4-pabellon-7")

    knowledge_entries = [
        {
            "content": "La biblioteca cuenta con préstamo de libros, salas de estudio grupal, acceso a computadoras y bases de datos digitales.",
            "category": "servicios",
            "subcategory": "biblioteca",
            "scene_id": biblioteca.id if biblioteca else None
        },
        {
            "content": "El polideportivo tiene cancha de fútbol, básquet, gimnasio y vestuarios. Horario: Lunes a Viernes 7am-9pm.",
            "category": "servicios",
            "subcategory": "deportes",
            "scene_id": poli.id if poli else None
        },
        {
            "content": "El Pabellón 7 tiene los salones 701, 702 y 704. Se imparten clases de carreras técnicas.",
            "category": "servicios",
            "subcategory": "salones",
            "scene_id": pabellon7.id if pabellon7 else None
        },
        {
            "content": "Tecsup ofrece carreras como Mecatrónica Industrial, Tecnología Digital, Mantenimiento de Maquinaria.",
            "category": "carreras",
            "subcategory": None,
            "scene_id": None
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