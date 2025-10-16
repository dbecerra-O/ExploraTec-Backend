from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
import time
from app.models.user import User
from app.models.chat import Conversation, Message
from app.database import get_db

from app.services.chatbot import (
    validate_message_content, check_rate_limit, check_conversation_limit,
    generate_ai_response, generate_conversation_title
)
from app.services.intent_detector import IntentDetector
from app.services.rag import retrieve_similar_passages, format_retrieved_passages
from app.dependencies import get_current_active_user, get_current_admin_user
from app.schemas.chat import (
    Conversation as ConversationSchema, ConversationSimple, ConversationCreate, ConversationUpdate,
    ChatMessage, ChatResponse, MessageFeedbackCreate, MessageFeedback,
    ChatStats
)
from app.crud.chat import conversation_crud, message_crud, feedback_crud, stats_crud
from app.crud.scene import scene_crud


router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

# API ENDPOINTS
@router.post("/message", response_model=ChatResponse, response_model_exclude_none=True)
async def send_message(
    message: ChatMessage,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    start_time = time.time()

    """
    Enviar mensaje al chatbot con IA integrada.
    """
    
    #  Validacion de contenido
    is_valid, error_msg = validate_message_content(message.content)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    rate_ok, rate_msg = check_rate_limit(db, current_user.id)
    if not rate_ok:
        raise HTTPException(status_code=429, detail=rate_msg)
        
    intent_result = IntentDetector.detect_intent(message.content)
    
    conversation = None
    is_new_conversation = False
    
    # Obtener o crear conversación
    if message.conversation_id:
        conversation = conversation_crud.get_conversation(db, message.conversation_id)
        if not conversation or conversation.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Conversación no encontrada")
        
        # Verificar límite de mensajes por conversación
        conv_limit_ok, conv_limit_msg = check_conversation_limit(db, conversation.id)
        if not conv_limit_ok:
            raise HTTPException(status_code=400, detail=conv_limit_msg)
        
    else:
        # Crear nueva conversación automáticamente
        auto_title = generate_conversation_title(message.content)

        conversation_data = ConversationCreate(
            title=auto_title,
            scene_id=message.scene_context_id,
            is_active=True
        )
        conversation = conversation_crud.create_conversation(db, conversation_data, current_user.id)
        is_new_conversation = True
    
    # Crear mensaje del usuario
    user_message = message_crud.create_user_message_with_intent(
        db=db,
        content=message.content.strip(),
        conversation_id=conversation.id,
        scene_context_id=message.scene_context_id,
        intent_category=intent_result["category"],
        intent_confidence=intent_result["confidence"],
        intent_keywords=intent_result["keywords_found"],
        requires_clarification=intent_result["requires_clarification"]
    )
    
    scene_context = None
    if message.scene_context_id:
        scene = scene_crud.get_scene(db, message.scene_context_id)
        scene_context = scene.name if scene else None
    
    if intent_result["requires_clarification"]:
        clarification_msg = IntentDetector.get_clarification_message(
            intent_result["all_matches"]
        )
        
        assistant_message = message_crud.create_assistant_message(
            db, clarification_msg, conversation.id, None
        )
        
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
    
    # Obtener historial para contexto de IA
    conversation_messages = message_crud.get_conversation_messages(db, conversation.id)
    conversation_history = [
        {
            "content": msg.content,
            "is_from_user": msg.is_from_user,
            "created_at": msg.created_at
        }
        for msg in conversation_messages
    ]
    
    # Recuperación RAG: buscar pasajes relevantes en la base de conocimiento
    try:
        passages = retrieve_similar_passages(db, message.content.strip(), top_k=4, scene_id=message.scene_context_id)
        retrieved_context = format_retrieved_passages(passages)
    except Exception as e:
        # Si falla la recuperación, continuamos sin contexto pero lo registramos
        print(f"⚠️ Error en RAG retrieval: {e}")
        db.rollback()
        retrieved_context = None

    # Generar respuesta con IA (incluyendo contexto recuperado si existe)
    bot_response, tokens_used = generate_ai_response(
        user_message=message.content.strip(),
        scene_context=scene_context,
        conversation_history=conversation_history,
        retrieved_context=retrieved_context
    )
    
    # Crear mensaje del asistente
    assistant_message = message_crud.create_assistant_message(
        db, bot_response, conversation.id, None, tokens_used
    )
    
    # Actualizar timestamp de conversación
    conversation_crud.update_conversation(db, conversation.id, ConversationUpdate())
    
    response_time_ms = int((time.time() - start_time) * 1000)

    # Preparar respuesta
    conversation_simple = ConversationSimple(
        id=conversation.id,
        title=conversation.title,
        scene_id=conversation.scene_id,
        is_active=conversation.is_active,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at
    )
    
    return ChatResponse(
        user_message=user_message,
        assistant_message=assistant_message,
        conversation=conversation_simple,
        is_new_conversation=is_new_conversation,
        response_time_ms=response_time_ms
    )

@router.get("/conversations", response_model=List[ConversationSimple])
async def get_my_conversations(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener mis conversaciones"""
    conversations = conversation_crud.get_user_conversations(db, current_user.id, skip, limit)
    
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
async def get_conversation_details(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener detalles de una conversación específica con todos sus mensajes"""
    conversation = conversation_crud.get_conversation(db, conversation_id)
    
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    
    return conversation

@router.post("/messages/{message_id}/feedback", response_model=MessageFeedback)
async def create_message_feedback(
    message_id: int,
    feedback: MessageFeedbackCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Dar feedback (like/dislike) a un mensaje del asistente"""
    
    message = message_crud.get_message(db, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")
    
    conversation = conversation_crud.get_conversation(db, message.conversation_id)
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para dar feedback a este mensaje")
    
    if message.is_from_user:
        raise HTTPException(status_code=400, detail="Solo puedes dar feedback a mensajes del asistente")
    
    created_feedback = feedback_crud.create_feedback(db, feedback, message_id, current_user.id)
    return created_feedback

# API ENDPOINTS - ADMIN
@router.get("/admin/stats", response_model=ChatStats)
async def get_chat_statistics(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Obtener estadísticas generales del sistema de chat"""
    return stats_crud.get_chat_stats(db)

@router.get("/admin/users/{user_id}/conversations", response_model=List[ConversationSimple])
async def get_user_conversations_admin(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Ver todas las conversaciones de un usuario específico (solo admin)"""
    
    # Verificar que el usuario existe
    from app.crud.user import user_crud
    user = user_crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    conversations = conversation_crud.get_user_conversations(db, user_id, skip, limit)
    
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

@router.get("/admin/users/{user_id}/conversations/{conversation_id}/messages", response_model=ConversationSchema)
async def get_user_conversation_with_messages(
    user_id: int,
    conversation_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Ver conversación específica de un usuario con TODOS sus mensajes (solo admin)."""
    
    # Verificar que el usuario existe
    from app.crud.user import user_crud
    user = user_crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Verificar que la conversación existe y pertenece al usuario
    conversation = conversation_crud.get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    
    if conversation.user_id != user_id:
        raise HTTPException(status_code=400, detail="Esta conversación no pertenece al usuario especificado")
    
    return conversation

@router.get("/admin/analytics/overview")
async def get_chat_analytics(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Analíticas básicas del sistema de chat"""
    
    # Estadísticas generales
    total_users_with_conversations = db.query(User.id).join(Conversation).distinct().count()
    avg_conversations_per_user = db.query(Conversation).count() / max(total_users_with_conversations, 1)
    
    # Usuarios más activos
    from sqlalchemy import func
    top_users = db.query(
        User.username, User.full_name,
        func.count(Conversation.id).label('conversations'),
        func.count(Message.id).label('messages')
    ).join(Conversation).join(Message).group_by(
        User.id, User.username, User.full_name
    ).order_by(func.count(Message.id).desc()).limit(5).all()
    
    return {
        "total_users_with_conversations": total_users_with_conversations,
        "avg_conversations_per_user": round(avg_conversations_per_user, 2),
        "top_active_users": [
            {
                "username": user.username,
                "conversations": user.conversations,
                "messages": user.messages
            }
            for user in top_users
        ]
    }

@router.get("/admin/intents/ambiguous")
async def get_ambiguous_queries(
    limit: int = 20,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Obtener consultas ambiguas que requirieron clarificación"""
    
    ambiguous_messages = message_crud.get_ambiguous_messages(db, skip=0, limit=limit)
    
    total_ambiguous = db.query(Message).filter(
        Message.requires_clarification == True,
        Message.is_from_user == True
    ).count()
    
    return {
        "total_ambiguous": total_ambiguous,
        "showing": len(ambiguous_messages),
        "examples": [
            {
                "id": msg.id,
                "content": msg.content,
                "detected_category": msg.intent_category,
                "confidence": msg.intent_confidence,
                "keywords": msg.intent_keywords,
                "created_at": msg.created_at
            }
            for msg in ambiguous_messages
        ]
    }

@router.get("/admin/intents/by-category/{category}")
async def get_messages_by_intent_category(
    category: str,
    limit: int = 50,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Obtener mensajes filtrados por categoría de intención"""
    
    messages = message_crud.get_messages_by_intent(db, category, skip=0, limit=limit)
    
    return {
        "category": category,
        "total_found": len(messages),
        "messages": [
            {
                "id": msg.id,
                "content": msg.content,
                "confidence": msg.intent_confidence,
                "keywords": msg.intent_keywords,
                "scene_context_id": msg.scene_context_id,
                "created_at": msg.created_at
            }
            for msg in messages
        ]
    }

@router.get("/admin/intents/low-confidence")
async def get_low_confidence_intents(
    threshold: float = 0.6,
    limit: int = 20,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Obtener mensajes con baja confianza en detección"""
    
    low_confidence_messages = db.query(Message).filter(
        Message.is_from_user == True,
        Message.intent_confidence < threshold,
        Message.intent_confidence.isnot(None)
    ).order_by(desc(Message.created_at)).limit(limit).all()
    
    return {
        "threshold": threshold,
        "total_found": len(low_confidence_messages),
        "messages": [
            {
                "id": msg.id,
                "content": msg.content,
                "detected_category": msg.intent_category,
                "confidence": msg.intent_confidence,
                "keywords": msg.intent_keywords,
                "created_at": msg.created_at
            }
            for msg in low_confidence_messages
        ]
    }