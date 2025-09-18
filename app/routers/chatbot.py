from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.dependencies import get_current_active_user, get_current_admin_user
from app.schemas.chat import (
    Conversation as ConversationSchema, ConversationSimple, ConversationCreate, ConversationUpdate,
    Message as MessageSchema, ChatMessage, ChatResponse, MessageFeedbackCreate, MessageFeedback,
    ChatStats, FeedbackType
)
from app.crud.chat import conversation_crud, message_crud, feedback_crud, stats_crud, MessageType
from app.crud.scene import scene_crud
from app.models.user import User
from app.models.chat import Conversation, Message, MessageFeedback
import random

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

def generate_chatbot_response(user_message: str, scene_name: str = None) -> str:
    """
    Función simple para generar respuestas del chatbot.
    En producción, aquí integrarías con un LLM como OpenAI, Claude, etc.
    """
    
    # Respuestas predefinidas basadas en palabras clave
    responses = {
        "hola": [
            "¡Hola! Bienvenido al tour virtual de Tecsup. ¿En qué puedo ayudarte?",
            "¡Hola! Soy tu asistente virtual para el recorrido por Tecsup. ¿Tienes alguna pregunta?"
        ],
        "biblioteca": [
            "La biblioteca de Tecsup cuenta con una amplia colección de libros técnicos y recursos digitales. ¿Te gustaría saber más sobre los servicios disponibles?",
            "Nuestra biblioteca está equipada con espacios de estudio individual y grupal, además de acceso a bases de datos especializadas."
        ],
        "laboratorio": [
            "Los laboratorios de Tecsup están equipados con tecnología de última generación para el aprendizaje práctico. ¿Qué área te interesa más?",
            "Contamos con laboratorios especializados en mecánica, tecnología, computación y más."
        ],
        "carrera": [
            "Tecsup ofrece carreras técnicas en ingeniería, tecnología y gestión. ¿Te interesa alguna área en particular?",
            "Nuestras carreras están diseñadas para formar profesionales técnicos altamente calificados."
        ],
        "admision": [
            "El proceso de admisión incluye evaluaciones académicas y entrevistas. ¿Necesitas información sobre fechas o requisitos?",
            "Para postular a Tecsup, necesitas completar tu educación secundaria y pasar nuestro proceso de selección."
        ],
        "polideportivo": [
            "El polideportivo cuenta con canchas para básquet, fútbol y futsal. Es un espacio para el desarrollo físico y la recreación.",
            "Nuestras instalaciones deportivas promueven el bienestar estudiantil y el trabajo en equipo."
        ],
        "patio": [
            "El patio central es el corazón del campus, donde se encuentra el cafetín, acceso a diferentes pabellones y espacios de encuentro.",
            "Desde el patio central puedes acceder a la biblioteca, secretaría, auditorio y demás instalaciones."
        ],
        "salon": [
            "Nuestros salones están equipados con tecnología moderna para facilitar el aprendizaje teórico y práctico.",
            "Los salones de Tecsup están diseñados para un ambiente de aprendizaje colaborativo e interactivo."
        ]
    }
    
    # Buscar palabras clave en el mensaje del usuario
    user_message_lower = user_message.lower()
    
    for keyword, keyword_responses in responses.items():
        if keyword in user_message_lower:
            response = random.choice(keyword_responses)
            if scene_name and scene_name != "None":
                response += f"\n\nVeo que estás en {scene_name}. ¿Hay algo específico de esta área que te gustaría conocer?"
            return response
    
    # Respuesta por defecto
    default_responses = [
        "Gracias por tu pregunta. Como asistente del tour virtual de Tecsup, estoy aquí para ayudarte a conocer nuestras instalaciones. ¿Qué te gustaría saber?",
        "Interesante pregunta. Te puedo ayudar con información sobre las instalaciones, carreras y servicios de Tecsup. ¿En qué área necesitas más detalles?",
        "Me parece una consulta importante. ¿Podrías ser más específico para poder darte la mejor información sobre Tecsup?"
    ]
    
    response = random.choice(default_responses)
    if scene_name and scene_name != "None":
        response += f"\n\nActualmente estás en {scene_name}."
    
    return response

@router.post("/message", response_model=ChatResponse)
async def send_message(
    message: ChatMessage,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Enviar un mensaje al chatbot"""
    
    # Obtener o crear conversación
    if message.conversation_id:
        conversation = conversation_crud.get_conversation(db, message.conversation_id)
        if not conversation or conversation.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Conversación no encontrada")
        is_new_conversation = False
    else:
        # Crear nueva conversación
        scene = None
        if message.scene_context_id:
            scene = scene_crud.get_scene(db, message.scene_context_id)
        
        conversation_data = ConversationCreate(
            title=f"Chat en {scene.name}" if scene else "Nueva conversación",
            scene_id=message.scene_context_id,
            is_active=True
        )
        conversation = conversation_crud.create_conversation(db, conversation_data, current_user.id)
        is_new_conversation = True
    
    # Crear mensaje del usuario
    user_message = message_crud.create_user_message(
        db, message.content, conversation.id, message.scene_context_id
    )
    
    # Generar respuesta del chatbot
    scene_name = None
    if message.scene_context_id:
        scene = scene_crud.get_scene(db, message.scene_context_id)
        scene_name = scene.name if scene else None
    
    bot_response = generate_chatbot_response(message.content, scene_name)
    
    # Crear mensaje del asistente
    assistant_message = message_crud.create_assistant_message(
        db, bot_response, conversation.id, message.scene_context_id
    )
    
    # Actualizar timestamp de la conversación
    conversation_crud.update_conversation(db, conversation.id, ConversationUpdate())
    
    # Preparar respuesta
    conversation_simple = ConversationSimple(
        id=conversation.id,
        title=conversation.title,
        scene_id=conversation.scene_id,
        is_active=conversation.is_active,
        user_id=conversation.user_id,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at
    )
    
    return ChatResponse(
        user_message=user_message,
        assistant_message=assistant_message,
        conversation=conversation_simple,
        is_new_conversation=is_new_conversation
    )

@router.get("/conversations", response_model=List[ConversationSimple])
async def get_user_conversations(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener las conversaciones del usuario"""
    conversations = conversation_crud.get_user_conversations(db, current_user.id, skip, limit)
    
    # Agregar conteo de mensajes
    conversations_simple = []
    for conv in conversations:
        message_count = len(conv.messages)
        conv_simple = ConversationSimple(
            id=conv.id,
            title=conv.title,
            scene_id=conv.scene_id,
            is_active=conv.is_active,
            user_id=conv.user_id,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=message_count
        )
        conversations_simple.append(conv_simple)
    
    return conversations_simple

@router.get("/conversations/{conversation_id}", response_model=ConversationSchema)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener una conversación específica con todos sus mensajes"""
    conversation = conversation_crud.get_conversation(db, conversation_id)
    
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    
    return conversation

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Eliminar una conversación"""
    conversation = conversation_crud.get_conversation(db, conversation_id)
    
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    
    deleted = conversation_crud.delete_conversation(db, conversation_id)
    if not deleted:
        raise HTTPException(status_code=400, detail="Error al eliminar la conversación")
    
    return {"message": "Conversación eliminada correctamente"}

@router.put("/conversations/{conversation_id}", response_model=ConversationSimple)
async def update_conversation(
    conversation_id: int,
    conversation_update: ConversationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Actualizar una conversación (ej: cambiar título, activar/desactivar)"""
    conversation = conversation_crud.get_conversation(db, conversation_id)
    
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    
    updated_conversation = conversation_crud.update_conversation(db, conversation_id, conversation_update)
    if not updated_conversation:
        raise HTTPException(status_code=400, detail="Error al actualizar la conversación")
    
    return ConversationSimple(
        id=updated_conversation.id,
        title=updated_conversation.title,
        scene_id=updated_conversation.scene_id,
        is_active=updated_conversation.is_active,
        user_id=updated_conversation.user_id,
        created_at=updated_conversation.created_at,
        updated_at=updated_conversation.updated_at
    )

@router.post("/messages/{message_id}/feedback", response_model=MessageFeedback)
async def create_message_feedback(
    message_id: int,
    feedback: MessageFeedbackCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Crear o actualizar feedback para un mensaje del asistente"""
    
    # Verificar que el mensaje existe
    message = message_crud.get_message(db, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")
    
    # Verificar que el mensaje pertenece a una conversación del usuario
    conversation = conversation_crud.get_conversation(db, message.conversation_id)
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para dar feedback a este mensaje")
    
    # Verificar que es un mensaje del asistente
    if message.is_from_user:
        raise HTTPException(status_code=400, detail="Solo puedes dar feedback a mensajes del asistente")
    
    # Crear el feedback
    created_feedback = feedback_crud.create_feedback(db, feedback, message_id, current_user.id)
    return created_feedback

@router.put("/messages/{message_id}/feedback", response_model=MessageFeedback)
async def update_message_feedback(
    message_id: int,
    feedback_update: MessageFeedbackCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Actualizar feedback existente para un mensaje"""
    
    # Verificar que el mensaje existe y el usuario tiene permisos
    message = message_crud.get_message(db, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")
    
    conversation = conversation_crud.get_conversation(db, message.conversation_id)
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para modificar este feedback")
    
    # Actualizar el feedback
    from app.schemas.chat import MessageFeedbackUpdate
    feedback_update_data = MessageFeedbackUpdate(
        feedback_type=feedback_update.feedback_type,
        comment=feedback_update.comment
    )
    
    updated_feedback = feedback_crud.update_feedback(db, message_id, feedback_update_data)
    if not updated_feedback:
        raise HTTPException(status_code=404, detail="Feedback no encontrado")
    
    return updated_feedback

@router.delete("/messages/{message_id}/feedback")
async def delete_message_feedback(
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Eliminar feedback de un mensaje"""
    
    # Verificar permisos
    message = message_crud.get_message(db, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")
    
    conversation = conversation_crud.get_conversation(db, message.conversation_id)
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para eliminar este feedback")
    
    # Eliminar el feedback
    deleted = feedback_crud.delete_feedback(db, message_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Feedback no encontrado")
    
    return {"message": "Feedback eliminado correctamente"}

# Endpoints para administradores

@router.get("/admin/stats", response_model=ChatStats)
async def get_chat_stats(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Obtener estadísticas del chatbot (solo admin)"""
    return stats_crud.get_chat_stats(db)

@router.get("/admin/conversations", response_model=List[ConversationSimple])
async def get_all_conversations(
    skip: int = 0,
    limit: int = 100,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Obtener todas las conversaciones (solo admin)"""
    conversations = db.query(Conversation).offset(skip).limit(limit).all()
    
    conversations_simple = []
    for conv in conversations:
        message_count = len(conv.messages)
        conv_simple = ConversationSimple(
            id=conv.id,
            title=conv.title,
            scene_id=conv.scene_id,
            is_active=conv.is_active,
            user_id=conv.user_id,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=message_count
        )
        conversations_simple.append(conv_simple)
    
    return conversations_simple

@router.get("/admin/conversations/{conversation_id}", response_model=ConversationSchema)
async def get_any_conversation(
    conversation_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Obtener cualquier conversación (solo admin)"""
    conversation = conversation_crud.get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    return conversation

@router.get("/admin/feedback/negative", response_model=List[MessageSchema])
async def get_negative_feedback_messages(
    skip: int = 0,
    limit: int = 50,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Obtener mensajes con feedback negativo para revisión (solo admin)"""
    
    messages = db.query(Message).join(MessageFeedback).filter(
        MessageFeedback.feedback_type == FeedbackType.DISLIKE
    ).order_by(Message.created_at.desc()).offset(skip).limit(limit).all()
    
    return messages

@router.get("/admin/feedback/positive", response_model=List[MessageSchema])
async def get_positive_feedback_messages(
    skip: int = 0,
    limit: int = 50,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Obtener mensajes con feedback positivo (solo admin)"""
    
    messages = db.query(Message).join(MessageFeedback).filter(
        MessageFeedback.feedback_type == FeedbackType.LIKE
    ).order_by(Message.created_at.desc()).offset(skip).limit(limit).all()
    
    return messages