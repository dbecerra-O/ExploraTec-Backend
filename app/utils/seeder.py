from sqlalchemy.orm import Session
from app.database import engine, SessionLocal
from app.database import drop_all_tables
from app.models.user import User
from app.models.scene import Scene
from app.models.chat import Conversation, Message
from app.crud.user import user_crud
from app.crud.scene import scene_crud
from app.schemas.user import UserCreate
from app.schemas.scene import SceneCreate
from app.models.knowledge import KnowledgeBase
from app.services.embeddings import embed_texts, get_openai_client
import app.models.note
from app.crud.event import event_crud
from app.schemas.event import EventCreate
import logging
from datetime import datetime, timedelta

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def drop_tables():
    """Eliminar todas las tablas"""
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
        {"scene_key": "0-entrada", "name": "Entrada", "is_relevant": True},
        {"scene_key": "1-patio-central", "name": "Patio Central", "is_relevant": True},
        {"scene_key": "2-camino", "name": "Camino", "is_relevant": False},
        {"scene_key": "3-pabellon-4---piso-2-s", "name": "Pabellón 4 - Piso 2-S", "is_relevant": False},
        {"scene_key": "4-pabellon-7", "name": "Pabellón 7", "is_relevant": False},
        {"scene_key": "5-area-de-salones-4b", "name": "Área de Salones 4B", "is_relevant": False},
        {"scene_key": "6-polideportivo", "name": "Polideportivo", "is_relevant": True},
        {"scene_key": "7-area-de-tecnologia", "name": "Área de Tecnología", "is_relevant": False},
        {"scene_key": "8-area-de-mecanica", "name": "Área de Mecánica", "is_relevant": False},
        {"scene_key": "9-mecanica", "name": "Mecánica", "is_relevant": False},
        {"scene_key": "10-segundo-piso-e", "name": "Segundo Piso E", "is_relevant": False},
        {"scene_key": "11-segundo-piso-s", "name": "Segundo Piso S", "is_relevant": False},
        {"scene_key": "12-zona-verde", "name": "Zona Verde", "is_relevant": False},
        {"scene_key": "13-cerca-del-ajedrez", "name": "Cerca del Ajedrez", "is_relevant": False},
        {"scene_key": "14-salon-701", "name": "Salón 701", "is_relevant": False},
        {"scene_key": "15-salones-de-mecanica", "name": "Salones de Mecánica", "is_relevant": False},
        {"scene_key": "16-salon-702", "name": "Salón 702", "is_relevant": False},
        {"scene_key": "17-salon-704", "name": "Salón 704", "is_relevant": False},
        {"scene_key": "18-maquinitas", "name": "Maquinitas", "is_relevant": False},
        {"scene_key": "19-pabellon-4---piso-2-e", "name": "Pabellón 4 - Piso 2-E", "is_relevant": False},
        {"scene_key": "20-pabellon-4---piso-2-m", "name": "Pabellón 4 - Piso 2-M", "is_relevant": False},
        {"scene_key": "21-pabellon-4---piso-2--a", "name": "Pabellón 4 - Piso 2-A", "is_relevant": False},
        {"scene_key": "22-pabellon-4---piso-1", "name": "Pabellón 4 - Piso 1", "is_relevant": False},
        {"scene_key": "23-salon-pabellon-4", "name": "Salón Pabellón 4", "is_relevant": False},
        {"scene_key": "24-pabellon-4", "name": "Pabellón 4", "is_relevant": True},
        {"scene_key": "25-entrada-biblioteca", "name": "Entrada Biblioteca", "is_relevant": False},
        {"scene_key": "26-biblioteca", "name": "Biblioteca", "is_relevant": True},
        {"scene_key": "27-pabellon-14", "name": "Pabellón 14", "is_relevant": False},
        {"scene_key": "28-salon-1509", "name": "Salón 1509", "is_relevant": False}
    ]
    
    for scene_data in scenes_data:
        existing = scene_crud.get_scene_by_key(db, scene_data["scene_key"])
        if not existing:
            scene = scene_crud.create_scene(db, SceneCreate(**scene_data))
            logger.info(f"Escena creada: {scene.scene_key} - {scene.name}")


def seed_events(db: Session):
    """Crear 4 eventos de ejemplo y asociarlos a escenas relevantes."""
    logger.info("Creando eventos de ejemplo...")
    try:
        events_data = [
            {
                "title": "Feria Tecnológica",
                "description": "Feria con proyectos estudiantiles y demostraciones.",
                "event_date": datetime.now() + timedelta(days=7),
                "location": "Pabellón 4",
                "scene_key": "24-pabellon-4"
            },
            {
                "title": "Charla de Admisiones",
                "description": "Información sobre carreras y proceso de admisión.",
                "event_date": datetime.now() + timedelta(days=14),
                "location": "Biblioteca",
                "scene_key": "26-biblioteca"
            },
            {
                "title": "Taller de Robótica",
                "description": "Taller práctico para introducir robótica educativa.",
                "event_date": datetime.now() + timedelta(days=10),
                "location": "Área de Tecnología",
                "scene_key": "7-area-de-tecnologia"
            },
            {
                "title": "Concierto de Bienvenida",
                "description": "Evento musical para dar la bienvenida a los nuevos alumnos.",
                "event_date": datetime.now() + timedelta(days=3),
                "location": "Patio Central",
                "scene_key": "1-patio-central"
            }
        ]

        created = 0
        for ev in events_data:
            scene = scene_crud.get_scene_by_key(db, ev["scene_key"]) if ev.get("scene_key") else None
            ev_create = EventCreate(
                title=ev["title"],
                description=ev.get("description"),
                event_date=ev["event_date"],
                location=ev.get("location"),
                scene_id=scene.id if scene else None
            )
            try:
                event_crud.create_event(db, ev_create)
                created += 1
            except Exception as e:
                logger.error(f"Error creando evento '{ev['title']}': {e}")

        logger.info(f"{created} eventos creados.")
    except Exception as e:
        logger.error(f"Error en seed_events: {e}")
        raise

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
        logger.warning(f"No se pudieron generar embeddings en el seeder: {e}")

    logger.info(f"{added} entradas de knowledge_base creadas.")

def seed_example_conversations(db: Session):
    """Crear 4 conversaciones de ejemplo con mensajes (usuario + asistente)."""
    from app.crud.scene import scene_crud

    logger.info("creando conversaciones de ejemplo...")
    try:
        student = user_crud.get_user_by_username(db, username="estudiante")

        s_bib = scene_crud.get_scene_by_key(db, "26-biblioteca")
        s_entrada = scene_crud.get_scene_by_key(db, "0-entrada")

        created = 0

        if student:
            conv1 = Conversation(
                user_id=student.id, 
                title="Consulta Biblioteca", 
                scene_id=s_bib.id if s_bib else None, 
                is_active=True,
                created_at=datetime.now() - timedelta(days=3)
            )
            db.add(conv1)
            db.commit()
            db.refresh(conv1)
            
            msgs1 = [
                Message(
                    conversation_id=conv1.id, 
                    content="¿La biblioteca tiene préstamo de libros y salas de estudio?", 
                    is_from_user=True, 
                    scene_context_id=s_bib.id if s_bib else None,
                    created_at=datetime.now() - timedelta(days=3, hours=2),
                    intent_category="servicios",
                    intent_confidence=0.95,
                    intent_keywords=["biblioteca", "libros", "préstamo", "estudio", "salas"]
                ),
                Message(
                    conversation_id=conv1.id, 
                    content="Sí, la biblioteca ofrece préstamo de libros, salas de estudio grupal y acceso a computadoras con bases de datos digitales. El horario es de lunes a viernes de 8am a 8pm.", 
                    is_from_user=False, 
                    scene_context_id=s_bib.id if s_bib else None,
                    created_at=datetime.now() - timedelta(days=3, hours=2, minutes=1)
                )
            ]
            db.add_all(msgs1)
            db.commit()
            created += 1

            conv2 = Conversation(
                user_id=student.id, 
                title="Ruta al Auditorio", 
                scene_id=s_entrada.id if s_entrada else None, 
                is_active=True,
                created_at=datetime.now() - timedelta(days=2)
            )
            db.add(conv2)
            db.commit()
            db.refresh(conv2)
            
            msgs2 = [
                Message(
                    conversation_id=conv2.id, 
                    content="¿Cómo llego al auditorio desde la entrada?", 
                    is_from_user=True, 
                    scene_context_id=s_entrada.id if s_entrada else None,
                    created_at=datetime.now() - timedelta(days=2, hours=1),
                    intent_category="navegacion",
                    intent_confidence=0.9,
                    intent_keywords=["auditorio", "quiero ir"]
                ),
                Message(
                    conversation_id=conv2.id, 
                    content="Desde la entrada camina hacia el patio central, luego toma la rampa hacia la izquierda; el auditorio está en el Pabellón 4, segundo piso. Está señalizado.", 
                    is_from_user=False, 
                    scene_context_id=s_entrada.id if s_entrada else None,
                    created_at=datetime.now() - timedelta(days=2, hours=1, minutes=1)
                )
            ]
            db.add_all(msgs2)
            db.commit()
            created += 1

            # Conversación 3: Horario del polideportivo
            s_poli = scene_crud.get_scene_by_key(db, "6-polideportivo")
            conv3 = Conversation(
                user_id=student.id,
                title="Horario Polideportivo",
                scene_id=s_poli.id if s_poli else None,
                is_active=True,
                created_at=datetime.now() - timedelta(days=1)
            )
            db.add(conv3)
            db.commit()
            db.refresh(conv3)

            msgs3 = [
                Message(
                    conversation_id=conv3.id,
                    content="¿Cuál es el horario del polideportivo?",
                    is_from_user=True,
                    scene_context_id=s_poli.id if s_poli else None,
                    created_at=datetime.now() - timedelta(days=1, hours=2),
                    intent_category="servicios",
                    intent_confidence=0.88,
                    intent_keywords=["polideportivo", "horario"]
                ),
                Message(
                    conversation_id=conv3.id,
                    content="El polideportivo está abierto de Lunes a Viernes de 7am a 9pm; los fines de semana tiene horario reducido.",
                    is_from_user=False,
                    scene_context_id=s_poli.id if s_poli else None,
                    created_at=datetime.now() - timedelta(days=1, hours=1, minutes=50)
                )
            ]
            db.add_all(msgs3)
            db.commit()
            created += 1

            # Conversación 4: Salones y carreras
            s_tec = scene_crud.get_scene_by_key(db, "7-area-de-tecnologia")
            conv4 = Conversation(
                user_id=student.id,
                title="Docentes Tecnología",
                scene_id=s_tec.id if s_tec else None,
                is_active=True,
                created_at=datetime.now() - timedelta(hours=12)
            )
            db.add(conv4)
            db.commit()
            db.refresh(conv4)

            msgs4 = [
                Message(
                    conversation_id=conv4.id,
                    content="Que docentes conoces de la area de Tecnologia Digital?",
                    is_from_user=True,
                    scene_context_id=s_tec.id if s_tec else None,
                    created_at=datetime.now() - timedelta(hours=11),
                    intent_category="informacion",
                    intent_confidence=0.92,
                    intent_keywords=["docentes", "tecnologia digital"]
                ),
                Message(
                    conversation_id=conv4.id,
                    content="En Tecnología Digital hay docentes como Silvia Montoya y Jaime Gomez. También se imparten cursos de desarrollo y redes.",
                    is_from_user=False,
                    scene_context_id=s_tec.id if s_tec else None,
                    created_at=datetime.now() - timedelta(hours=10, minutes=50)
                )
            ]
            db.add_all(msgs4)
            db.commit()
            created += 1

        logger.info(f"{created} conversaciones de ejemplo creadas.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error creando conversaciones de ejemplo: {e}")
        raise

def run_seeder():
    """Ejecutar el seeder basico"""
    logger.info("Iniciando seeder...")
    
    # Eliminar y crear tablas
    drop_tables()
    create_tables()
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        if not inspector.has_table('scenes'):
            logger.warning("La tabla 'scenes' no existe después de create_tables(). Reintentando create_all().")
            create_tables()
            inspector = inspect(engine)
            if not inspector.has_table('scenes'):
                raise RuntimeError("La tabla 'scenes' no pudo ser creada. Revise la conexión y permisos de la BD.")
    except Exception as ex:
        logger.error(f"Error verificando/creando tablas: {ex}")
        raise
    
    # Crear sesión
    db = SessionLocal()
    
    try:
        # Agregar datos básicos
        seed_users(db)
        # Agregar escenas básicas
        seed_basic_scenes(db)
        # Agregar eventos de ejemplo
        seed_events(db)
        # Agregar knowledge base
        seed_knowledge(db)
        # Agregar conversaciones de ejemplo
        seed_example_conversations(db)
        
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