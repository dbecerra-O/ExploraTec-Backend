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

def seed_chat_data(db):
    """Seeder de conversaciones, mensajes y feedback para user_id=2"""
    user_id = 2

    conversations_data = [
        {
            "title": "Primera conversación de prueba",
            "is_active": True,
            "messages": [
                {"content": "Hola, ¿cómo estás?", "is_from_user": True},
                {"content": "¡Hola! Estoy bien, gracias. ¿Y tú?", "is_from_user": False, "tokens_used": 12, "feedback": {"is_positive": True, "comment": "Muy buena respuesta, clara y rápida."}},
                {"content": "Muy bien, quería saber qué puedes hacer.", "is_from_user": True},
                {"content": "Puedo ayudarte con preguntas, darte información y mucho más.", "is_from_user": False, "tokens_used": 18, "feedback": {"is_positive": False, "comment": "Un poco genérica, esperaba más detalle."}},
            ],
        },
        {
            "title": "Consulta sobre cursos",
            "is_active": False,
            "messages": [
                {"content": "¿Qué cursos recomiendas para empezar con Python?", "is_from_user": True},
                {"content": "Te recomiendo comenzar con un curso de fundamentos de Python: variables, estructuras de control y funciones.", "is_from_user": False, "tokens_used": 25, "feedback": {"is_positive": True, "comment": "Respuesta muy útil, me dio un buen punto de partida."}},
                {"content": "¿Tienes algún curso avanzado?", "is_from_user": True},
                {"content": "Sí, también hay cursos sobre programación orientada a objetos y desarrollo web con Django.", "is_from_user": False, "tokens_used": 30},
            ],
        },
        {
            "title": "Asistencia técnica",
            "is_active": False,
            "messages": [
                {"content": "Mi aplicación no arranca, ¿qué puedo hacer?", "is_from_user": True},
                {"content": "Primero revisa si tienes los logs de error, suelen dar pistas del problema.", "is_from_user": False, "tokens_used": 20},
                {"content": "Me aparece un error de conexión a la base de datos.", "is_from_user": True},
                {"content": "Verifica que la base de datos esté corriendo y que las credenciales en el archivo de configuración sean correctas.", "is_from_user": False, "tokens_used": 32, "feedback": {"is_positive": True, "comment": "Excelente, esa fue justo la solución al problema."}},
            ],
        },
    ]

    for conv_data in conversations_data:
        conversation = Conversation(
            user_id=user_id,
            title=conv_data["title"],
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
                tokens_used=msg_data.get("tokens_used"),
            )
            db.add(msg)
            db.commit()
            db.refresh(msg)

            # Crear feedback si existe
            if "feedback" in msg_data:
                fb_data = msg_data["feedback"]
                feedback = MessageFeedback(
                    message_id=msg.id,
                    user_id=user_id,
                    is_positive=fb_data["is_positive"],
                    comment=fb_data.get("comment"),
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