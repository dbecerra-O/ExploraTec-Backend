import time
from typing import List, Optional
import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.database import get_db
from app.models.user import User
from app.models.chat import Conversation, Message

from app.schemas.chat import (
    Conversation as ConversationSchema, ConversationSimple, ConversationCreate, ConversationUpdate,
    ChatMessage, ChatResponse, MessageFeedbackCreate, MessageFeedback,
    ChatStats
)
from app.crud.chat import conversation_crud, message_crud, feedback_crud, stats_crud
from app.crud.user import user_crud
from app.crud.scene import scene_crud

from app.services.chatbot import (
    validate_message_content, check_rate_limit, generate_ai_response,
    get_or_create_conversation, handle_clarification_response, retrieve_knowledge_context,
    get_scene_context, get_conversation_history, handle_navigation_if_needed
)
from app.services.intent_detector import IntentDetector
from app.dependencies import get_current_active_user, get_current_admin_user

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

# API ENDPOINTS
@router.post("/message", response_model=ChatResponse, response_model_exclude_none=True)
async def send_message(
    message: ChatMessage,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Enviar mensaje al chatbot con IA integrada.
    """
    start_time = time.time()
 
    #  Validacion de contenido
    is_valid, error_msg = validate_message_content(message.content)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    rate_ok, rate_msg = check_rate_limit(db, current_user.id)
    if not rate_ok:
        raise HTTPException(status_code=429, detail=rate_msg) 
    
    conversation, is_new_conversation = get_or_create_conversation(
        db=db,
        message=message,
        current_user=current_user
    )

    intent_result = IntentDetector.detect_intent(message.content)
    try:
        message_text = (message.content or "").strip().lower()
        if scene_id and re.search(r"\bq(ue|u[eé])?\s*(e\s*)?hay\s+a?qui\b", message_text):
            intent_result = {
                "category": "informacion_ubicacion",
                "confidence": 0.95,
                "keywords_found": ["que hay aqui"],
                "requires_clarification": False,
                "all_matches": [("informacion_ubicacion", 0.95)]
            }
    except Exception:
        pass
    
    # Crear mensaje del usuario
    user_message = message_crud.create_user_message_with_intent(
        db=db,
        content=message.content.strip(),
        conversation_id=conversation.id,
        scene_context=message.scene_context,
        intent_category=intent_result["category"],
        intent_confidence=intent_result["confidence"],
        intent_keywords=intent_result["keywords_found"],
        requires_clarification=intent_result["requires_clarification"]
    )
    
    if intent_result["requires_clarification"]:
        return handle_clarification_response(
            db=db,
            conversation=conversation,
            user_message=user_message,
            intent_result=intent_result,
            message=message,
            is_new_conversation=is_new_conversation,
            start_time=start_time
        )
    scene_id = None
    if message.scene_context:
        scene = scene_crud.get_scene_by_key(db, message.scene_context)
        if scene:
            scene_id = scene.id

    retrieved_context = retrieve_knowledge_context(
        db=db,
        query=message.content.strip(),
        scene_id=scene_id
    )

    # retrieved_context is now possibly a dict: {"text": str|None, "events": list|None}
    retrieved_context_text = None
    retrieved_events = None
    if isinstance(retrieved_context, dict):
        retrieved_context_text = retrieved_context.get("text")
        retrieved_events = retrieved_context.get("events")
    else:
        retrieved_context_text = retrieved_context

    scene_context = get_scene_context(db, scene_id)
    conversation_history = get_conversation_history(db, conversation.id)
    
    bot_response, tokens_used = generate_ai_response(
        user_message=message.content.strip(),
        scene_context=scene_context,
        conversation_history=conversation_history,
        retrieved_context=retrieved_context_text
    )
    
    # Crear mensaje del asistente
    assistant_message = message_crud.create_assistant_message(
        db, bot_response, conversation.id, None, tokens_used
    )

    # Obtener scene_id desde scene_context si existe
    scene_id = None
    if message.scene_context:
        scene = scene_crud.get_scene_by_key(db, message.scene_context)
        if scene:
            scene_id = scene.id

    navigation_data = handle_navigation_if_needed(
        db=db,
        intent_category=intent_result["category"],
        message_content=message.content,
        scene_context=message.scene_context,
        assistant_message=assistant_message,
        intent_all_matches=intent_result.get("all_matches")
    )
    
    conversation_crud.update_conversation(db, conversation.id, ConversationUpdate())
    response_time_ms = int((time.time() - start_time) * 1000)
    
    conversation_simple = ConversationSimple(
        id=conversation.id,
        title=conversation.title,
        scene_id=conversation.scene_id,
        is_active=conversation.is_active,
        user_id=conversation.user_id,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at
    )
    def _message_to_dict(msg: Message) -> dict:
        return {
            "id": msg.id,
            "conversation_id": msg.conversation_id,
            "content": msg.content,
            "is_from_user": msg.is_from_user,
            "scene_context": msg.scene_context.scene_key if getattr(msg, "scene_context", None) else None,
            "tokens_used": msg.tokens_used,
            "created_at": msg.created_at,
            "feedback": None,
            "intent_category": getattr(msg, "intent_category", None),
            "intent_confidence": getattr(msg, "intent_confidence", None),
            "intent_keywords": getattr(msg, "intent_keywords", None),
            "requires_clarification": getattr(msg, "requires_clarification", None)
        }

    return ChatResponse(
        user_message=_message_to_dict(user_message),
        assistant_message=_message_to_dict(assistant_message),
        conversation=conversation_simple,
        is_new_conversation=is_new_conversation,
        navigation=navigation_data,
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
    def _message_to_dict(msg: Message) -> dict:
        return {
            "id": msg.id,
            "conversation_id": msg.conversation_id,
            "content": msg.content,
            "is_from_user": msg.is_from_user,
            "scene_context": msg.scene_context.scene_key if getattr(msg, "scene_context", None) else None,
            "tokens_used": msg.tokens_used,
            "created_at": msg.created_at,
            "feedback": None,
            "intent_category": getattr(msg, "intent_category", None),
            "intent_confidence": getattr(msg, "intent_confidence", None),
            "intent_keywords": getattr(msg, "intent_keywords", None),
            "requires_clarification": getattr(msg, "requires_clarification", None)
        }

    conversation_dict = {
        "id": conversation.id,
        "title": conversation.title,
        "scene_id": conversation.scene_id,
        "is_active": conversation.is_active,
        "user_id": conversation.user_id,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "messages": [_message_to_dict(m) for m in conversation.messages]
    }

    return conversation_dict

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

@router.get("/admin/users/{user_id}/conversations/{conversation_id}/messages", response_model=ConversationSchema, response_model_exclude_none=True)
async def get_user_conversation_with_messages(
    user_id: int,
    conversation_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Ver conversación específica de un usuario con TODOS sus mensajes (solo admin)."""
    
    user = user_crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    conversation = conversation_crud.get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    
    if conversation.user_id != user_id:
        raise HTTPException(status_code=400, detail="Esta conversación no pertenece al usuario especificado")

    def _message_to_dict(msg: Message) -> dict:
        return {
            "id": msg.id,
            "conversation_id": msg.conversation_id,
            "content": msg.content,
            "is_from_user": msg.is_from_user,
            "scene_context": msg.scene_context.scene_key if getattr(msg, "scene_context", None) else None,
            "tokens_used": msg.tokens_used,
            "created_at": msg.created_at,
            "feedback": None,
            "intent_category": getattr(msg, "intent_category", None),
            "intent_confidence": getattr(msg, "intent_confidence", None),
            "intent_keywords": getattr(msg, "intent_keywords", None),
            "requires_clarification": getattr(msg, "requires_clarification", None)
        }

    conversation_dict = {
        "id": conversation.id,
        "title": conversation.title,
        "scene_id": conversation.scene_id,
        "is_active": conversation.is_active,
        "user_id": conversation.user_id,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "messages": [_message_to_dict(m) for m in conversation.messages]
    }

    return conversation_dict

@router.get("/admin/analytics/overview")
async def get_chat_analytics(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Analíticas básicas del sistema de chat"""
    
    # Estadísticas generales
    total_users_with_conversations = db.query(User.id).join(Conversation).distinct().count()
    avg_conversations_per_user = db.query(Conversation).count() / max(total_users_with_conversations, 1)
    
    # Usuarios más activos - usando select_from() para establecer el orden de joins
    top_users = db.query(
        User.id, User.username,
        func.count(Conversation.id).label('conversations'),
        func.count(Message.id).label('messages')
    ).select_from(User).join(
        Conversation, User.id == Conversation.user_id
    ).join(
        Message, Message.conversation_id == Conversation.id
    ).group_by(
        User.id, User.username
    ).order_by(func.count(Message.id).desc()).limit(5).all()
    
    return {
        "total_users_with_conversations": total_users_with_conversations,
        "avg_conversations_per_user": round(avg_conversations_per_user, 2),
        "top_active_users": [
            {
                "id": user.id,
                "username": user.username,
                "conversations": user.conversations,
                "messages": user.messages
            }
            for user in top_users
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
                "scene_context": msg.scene_context.scene_key if msg.scene_context else None,
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

@router.get("/admin/messages")
async def get_all_messages_admin(
    skip: int = 0,
    limit: int = 50,
    scene_context: Optional[str] = None,
    intent_category: Optional[str] = None,
    min_confidence: Optional[float] = None,
    only_user_messages: bool = True,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Obtener todos los mensajes con sus intenciones y métricas (admin).
    """
    
    # Consulta base
    query = db.query(
        Message,
        User.username.label('username'),
        Conversation.title.label('conversation_title')
    ).join(
        Conversation, Message.conversation_id == Conversation.id
    ).join(
        User, Conversation.user_id == User.id
    )
    
    # Aplicar filtros
    if only_user_messages:
        query = query.filter(Message.is_from_user == True)
    
    # Filtrar por scene_key si se proporciona
    if scene_context is not None:
        scene = scene_crud.get_scene_by_key(db, scene_context)
        scene_id = scene.id if scene else None
        if scene_id is not None:
            query = query.filter(Message.scene_context_id == scene_id)
    
    if intent_category:
        query = query.filter(Message.intent_category == intent_category)
    
    if min_confidence is not None:
        query = query.filter(Message.intent_confidence >= min_confidence)
    
    # Contar total antes de paginar
    total_count = query.count()
    
    # Aplicar ordenamiento y paginación
    messages = query.order_by(desc(Message.created_at)).offset(skip).limit(limit).all()
    
    # Estadísticas de intenciones para los mensajes filtrados
    intent_stats = db.query(
        Message.intent_category,
        func.count(Message.id).label('count'),
        func.avg(Message.intent_confidence).label('avg_confidence')
    ).filter(
        Message.id.in_([msg[0].id for msg in messages]),
        Message.intent_category.isnot(None)
    ).group_by(Message.intent_category).all()
    
    return {
        "total_messages": total_count,
        "showing": len(messages),
        "skip": skip,
        "limit": limit,
        "intent_statistics": [
            {
                "category": stat[0],
                "count": stat[1],
                "avg_confidence": round(float(stat[2] or 0), 2)
            }
            for stat in intent_stats
        ],
        "messages": [
            {
                "id": msg[0].id,
                "content": msg[0].content,
                "username": msg[1],
                "conversation_title": msg[2],
                "scene_context": msg[0].scene_context.scene_key if msg[0].scene_context else None,
                "is_from_user": msg[0].is_from_user,
                "intent_category": msg[0].intent_category,
                "intent_confidence": msg[0].intent_confidence,
                "intent_keywords": msg[0].intent_keywords,
                "requires_clarification": msg[0].requires_clarification,
                "tokens_used": msg[0].tokens_used,
                "created_at": msg[0].created_at
            }
            for msg in messages
        ]
    }