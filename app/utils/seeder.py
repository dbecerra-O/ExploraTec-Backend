from sqlalchemy.orm import Session
from app.database import engine, SessionLocal
from app.models.user import User
from app.models.scene import Scene
from app.models.chat import Conversation, Message, MessageFeedback
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

def seed_chat_data(db):
    """Seeder de conversaciones, mensajes y feedback"""
    user_id = 2
    
    entrada = scene_crud.get_scene_by_key(db, "0-entrada")
    biblioteca = scene_crud.get_scene_by_key(db, "2-biblioteca")
    comedor = scene_crud.get_scene_by_key(db, "4-comedor")

    conversations_data = [
        {
            "title": "Consulta de navegación",
            "scene_id": entrada.id if entrada else None,
            "is_active": False,
            "messages": [
                {
                    "content": "¿Cómo llego a la biblioteca?",
                    "is_from_user": True,
                    "scene_context_id": entrada.id if entrada else None,
                    # Intención detectada: NAVEGACIÓN
                    "intent_category": "navegacion",
                    "intent_confidence": 0.83,
                    "intent_keywords": ["como llego", "biblioteca"],
                    "requires_clarification": False
                },
                {
                    "content": "Para llegar a la biblioteca desde la entrada, dirígete hacia el patio central y toma el pasillo de la derecha. La biblioteca está al final del pasillo.",
                    "is_from_user": False,
                    "tokens_used": 35,
                    "feedback": {
                        "is_positive": True,
                        "comment": "Instrucciones claras y precisas"
                    }
                },
                {
                    "content": "¿Y dónde está el comedor?",
                    "is_from_user": True,
                    "scene_context_id": biblioteca.id if biblioteca else None,
                    "intent_category": "navegacion",
                    "intent_confidence": 0.67,
                    "intent_keywords": ["donde esta", "comedor"],
                    "requires_clarification": False
                },
                {
                    "content": "El comedor está en el primer piso, cerca del patio central. Desde la biblioteca, vuelve al patio y toma la escalera de la izquierda.",
                    "is_from_user": False,
                    "tokens_used": 28
                }
            ]
        },
        {
            "title": "Información sobre carreras",
            "is_active": False,
            "messages": [
                {
                    "content": "¿Qué carreras técnicas ofrecen?",
                    "is_from_user": True,
                    # Intención detectada: CARRERAS
                    "intent_category": "carreras",
                    "intent_confidence": 0.83,
                    "intent_keywords": ["carreras"],
                    "requires_clarification": False
                },
                {
                    "content": "Tecsup ofrece diversas carreras técnicas como Mecatrónica Industrial, Mantenimiento de Maquinaria Pesada, Diseño Industrial, y Administración de Redes y Comunicaciones.",
                    "is_from_user": False,
                    "tokens_used": 42,
                    "feedback": {
                        "is_positive": True,
                        "comment": "Información completa y útil"
                    }
                },
                {
                    "content": "¿Cuánto dura la carrera de Mecatrónica?",
                    "is_from_user": True,
                    "intent_category": "carreras",
                    "intent_confidence": 0.67,
                    "intent_keywords": ["carrera"],
                    "requires_clarification": False
                },
                {
                    "content": "La carrera de Mecatrónica Industrial tiene una duración de 3 años (6 semestres académicos).",
                    "is_from_user": False,
                    "tokens_used": 22
                }
            ]
        },
        {
            "title": "Consulta ambigua sobre horarios y eventos",
            "is_active": False,
            "messages": [
                {
                    "content": "horario de eventos esta semana",
                    "is_from_user": True,
                    # Intención detectada: AMBIGUA (eventos vs horarios)
                    "intent_category": "eventos",
                    "intent_confidence": 0.50,
                    "intent_keywords": ["eventos", "horario", "esta semana"],
                    "requires_clarification": True
                },
                {
                    "content": "Entiendo que podrías estar preguntando sobre:\n• ¿Te interesa conocer eventos o actividades?\n• ¿Necesitas conocer horarios de atención?",
                    "is_from_user": False,
                    "tokens_used": 25
                },
                {
                    "content": "Quiero saber qué eventos hay esta semana",
                    "is_from_user": True,
                    "intent_category": "eventos",
                    "intent_confidence": 0.83,
                    "intent_keywords": ["eventos", "esta semana"],
                    "requires_clarification": False
                },
                {
                    "content": "Esta semana tenemos: Taller de Arduino (Miércoles 15:00, Lab. Electrónica), Charla de Empleabilidad (Jueves 16:00, Auditorio), y Campeonato de Fútbol (Viernes 17:00, Campo deportivo).",
                    "is_from_user": False,
                    "tokens_used": 45,
                    "feedback": {
                        "is_positive": True,
                        "comment": "Muy bien organizado y específico"
                    }
                }
            ]
        },
        {
            "title": "Consulta sobre servicios del campus",
            "scene_id": comedor.id if comedor else None,
            "is_active": False,
            "messages": [
                {
                    "content": "¿Qué servicios tiene la biblioteca?",
                    "is_from_user": True,
                    "scene_context_id": comedor.id if comedor else None,
                    # Intención detectada: SERVICIOS
                    "intent_category": "servicios",
                    "intent_confidence": 0.83,
                    "intent_keywords": ["servicios", "biblioteca"],
                    "requires_clarification": False
                },
                {
                    "content": "La biblioteca cuenta con: préstamo de libros, acceso a computadoras, salas de estudio grupal, conexión WiFi gratuita, y acceso a bases de datos digitales.",
                    "is_from_user": False,
                    "tokens_used": 38
                }
            ]
        },
        {
            "title": "Consulta de admisión",
            "is_active": True,  # Conversación activa
            "messages": [
                {
                    "content": "¿Cómo puedo postular a Tecsup?",
                    "is_from_user": True,
                    # Intención detectada: ADMISIONES
                    "intent_category": "admisiones",
                    "intent_confidence": 0.67,
                    "intent_keywords": ["postular"],
                    "requires_clarification": False
                },
                {
                    "content": "Para postular a Tecsup debes: 1) Completar la solicitud en línea, 2) Presentar certificado de estudios secundarios, 3) Rendir el examen de admisión, 4) Asistir a entrevista personal.",
                    "is_from_user": False,
                    "tokens_used": 48,
                    "feedback": {
                        "is_positive": True,
                        "comment": "Pasos claros y ordenados"
                    }
                },
                {
                    "content": "¿Cuáles son los requisitos?",
                    "is_from_user": True,
                    "intent_category": "admisiones",
                    "intent_confidence": 0.67,
                    "intent_keywords": ["requisitos"],
                    "requires_clarification": False
                },
                {
                    "content": "Los requisitos principales son: haber culminado la educación secundaria, tener entre 16 y 25 años, aprobar el examen de admisión con nota mínima de 13, y presentar documentos de identidad.",
                    "is_from_user": False,
                    "tokens_used": 42
                }
            ]
        },
        {
            "title": "Consulta general",
            "is_active": False,
            "messages": [
                {
                    "content": "Hola, ¿cómo estás?",
                    "is_from_user": True,
                    # Intención detectada: GENERAL (saludo)
                    "intent_category": "general",
                    "intent_confidence": 1.0,
                    "intent_keywords": [],
                    "requires_clarification": False
                },
                {
                    "content": "¡Hola! Estoy aquí para ayudarte con información sobre Tecsup. ¿En qué puedo asistirte?",
                    "is_from_user": False,
                    "tokens_used": 18
                }
            ]
        }
    ]

    for conv_data in conversations_data:
        conversation = Conversation(
            user_id=user_id,
            title=conv_data["title"],
            scene_id=conv_data.get("scene_id"),
            is_active=conv_data["is_active"],
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        for msg_data in conv_data["messages"]:
            msg = Message(
                conversation_id=conversation.id,
                content=msg_data["content"],
                is_from_user=msg_data["is_from_user"],
                scene_context_id=msg_data.get("scene_context_id"),
                tokens_used=msg_data.get("tokens_used"),
                intent_category=msg_data.get("intent_category"),
                intent_confidence=msg_data.get("intent_confidence"),
                intent_keywords=msg_data.get("intent_keywords"),
                requires_clarification=msg_data.get("requires_clarification", False)
            )
            db.add(msg)
            db.commit()
            db.refresh(msg)

            if "feedback" in msg_data:
                fb_data = msg_data["feedback"]
                feedback = MessageFeedback(
                    message_id=msg.id,
                    user_id=user_id,
                    is_positive=fb_data["is_positive"],
                    comment=fb_data.get("comment")
                )
                db.add(feedback)
                db.commit()

    logger.info("✅ 3 conversaciones con mensajes y feedback creadas para user_id=2.")

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
        seed_chat_data(db)
        
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