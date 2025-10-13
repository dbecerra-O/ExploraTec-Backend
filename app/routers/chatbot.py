from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Dict
import openai
import os

from app.database import get_db
from app.dependencies import get_current_active_user, get_current_admin_user
from app.schemas.chat import (
    Conversation as ConversationSchema, ConversationSimple, ConversationCreate, ConversationUpdate,
    ChatMessage, ChatResponse, MessageFeedbackCreate, MessageFeedback,
    ChatStats
)
from app.crud.chat import conversation_crud, message_crud, feedback_crud, stats_crud
from app.crud.scene import scene_crud
from app.models.user import User
from app.models.chat import Conversation, Message
from app.services.intent_detector import IntentDetector

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

# Configurar cliente OpenAI
def get_openai_client():
    """Obtener cliente de OpenAI configurado"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise Exception("OPENAI_API_KEY no encontrada en las variables de entorno")
    return openai.OpenAI(api_key=api_key)

def generate_ai_response(user_message: str, scene_context: str = None, conversation_history: List[Dict] = None) -> tuple:
    """
    Generar respuesta usando OpenAI GPT-4o-mini
    Retorna: (respuesta, tokens_usados)
    """
    try:
        client = get_openai_client()
        
        # System prompt específico para Tecsup
        system_prompt = """Eres un asistente virtual de Tecsup, una institución de educación técnica en Perú.
Tu objetivo es ayudar a los usuarios con información sobre:
- Carreras técnicas
- Proceso de admisión y requisitos
- Instalaciones del campus (laboratorios, biblioteca, deportes)
- Vida estudiantil y servicios
- Horarios y calendario académico
- Becas y financiamiento

Responde de manera amigable, informativa y concisa siempre en español, sin importar el idioma en que el usuario escriba. 
Si no tienes información específica, ofrece ayuda general y sugiere contactar a la administración."""

        if scene_context:
            system_prompt += f"\n\nContexto adicional: El usuario está actualmente en {scene_context}. Puedes hacer referencia a esta ubicación si es relevante para tu respuesta."

        # Preparar mensajes
        messages = [{"role": "system", "content": system_prompt}]
        
        # Agregar historial de conversación (últimos 3 mensajes para mantener contexto)
        if conversation_history:
            for msg in conversation_history[-3:]:
                if msg.get("content") and msg.get("content").strip():
                    role = "user" if msg.get("is_from_user") else "assistant"
                    messages.append({"role": role, "content": msg.get("content")})
        
        # Agregar mensaje actual del usuario
        messages.append({"role": "user", "content": user_message})
        
        # Llamar a OpenAI con gpt-4o-mini (el más económico y eficiente)
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Modelo más económico: $0.15/$0.60 por 1M tokens
            messages=messages,
            max_tokens=300,  # Respuestas concisas pero completas
            temperature=0.7,
        )
        
        result = response.choices[0].message.content.strip()
        total_tokens = response.usage.total_tokens
        
        print(f"✓ Respuesta generada con gpt-4o-mini. Tokens usados: {total_tokens}")
        return result, total_tokens
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error al generar respuesta con OpenAI: {error_msg}")
        
        # Mensaje de error más amigable
        if "insufficient_quota" in error_msg or "429" in error_msg:
            raise HTTPException(
                status_code=503,
                detail="El servicio de IA temporalmente no está disponible. Por favor, intenta más tarde."
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Error al conectar con el servicio de IA: {error_msg}"
            )

def generate_conversation_title(message_content: str) -> str:
    """Generar título automático para la conversación usando gpt-4o-mini"""
    try:
        client = get_openai_client()
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Mismo modelo económico
            messages=[
                {"role": "system", "content": "Genera un título corto y descriptivo (máximo 6 palabras) para esta conversación en español."},
                {"role": "user", "content": message_content}
            ],
            max_tokens=15,  # Títulos cortos = menos tokens
            temperature=0.5
        )

        if response and hasattr(response, "choices") and len(response.choices) > 0:
            content = response.choices[0].message.content
            return content.strip() if content else "Conversación sin título"
        else:
            return "Conversación sin título"

    except Exception as e:
        print(f"⚠️ Error generando título: {str(e)}")
        # Fallback: usar primeras palabras del mensaje
        words = message_content.split()[:4]
        return " ".join(words) + "..." if len(words) >= 4 else message_content[:30]

# API ENDPOINTS
@router.post("/message", response_model=ChatResponse, response_model_exclude_none=True)
async def send_message(
    message: ChatMessage,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Enviar mensaje al chatbot con IA integrada.
    Crea conversación automáticamente si no existe una.
    """
    
    #  Validar que el mensaje no exceda 500 caracteres
    if len(message.content) > 500:
        raise HTTPException(
            status_code=400,
            detail="El mensaje no puede superar los 500 caracteres"
        )
        
    intent_result = IntentDetector.detect_intent(message.content)
    
    conversation = None
    is_new_conversation = False
    
    # Obtener o crear conversación
    if message.conversation_id:
        conversation = conversation_crud.get_conversation(db, message.conversation_id)
        if not conversation or conversation.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Conversación no encontrada")
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
        content=message.content,
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
    
    # Generar respuesta con IA
    bot_response, tokens_used = generate_ai_response(
        user_message=message.content,
        scene_context=scene_context,
        conversation_history=conversation_history
    )
    
    # Crear mensaje del asistente
    assistant_message = message_crud.create_assistant_message(
        db, bot_response, conversation.id, None, tokens_used
    )
    
    # Actualizar timestamp de conversación
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