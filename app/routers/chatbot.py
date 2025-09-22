from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
import openai
import httpx
import random
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

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

def generate_ai_response(user_message: str, scene_context: str = None, conversation_history: List[Dict] = None) -> str:
    """
    Función que usa APIs de IA para generar respuestas inteligentes.
    Soporta OpenAI, Groq y Claude con fallback a respuestas predefinidas.
    """
    
    try:
        if os.getenv("OPENAI_API_KEY"):
            return generate_openai_response(user_message, scene_context, conversation_history)
        elif os.getenv("GROQ_API_KEY"):
            return generate_groq_response(user_message, scene_context, conversation_history)
        elif os.getenv("ANTHROPIC_API_KEY"):
            return generate_claude_response(user_message, scene_context, conversation_history)
        else:
            return generate_predefined_response(user_message)
            
    except Exception as e:
        print(f"Error con API de IA: {e}")
        return generate_predefined_response(user_message)

def generate_openai_response(user_message: str, scene_context: str = None, conversation_history: List[Dict] = None) -> str:
    """Generar respuesta usando OpenAI GPT"""
    
    openai.api_key = os.getenv("OPENAI_API_KEY")
    
    system_prompt = """Eres un asistente virtual de Tecsup, una institución de educación técnica en Perú.
    Tu objetivo es ayudar a los usuarios con información sobre:
    - Carreras técnicas (ingeniería, tecnología, gestión)
    - Proceso de admisión y requisitos
    - Instalaciones del campus (laboratorios, biblioteca, deportes)
    - Vida estudiantil y servicios

    Responde de manera amigable, informativa y concisa. Si no tienes información específica, 
    ofrece ayuda general y sugiere contactar a la administración."""

    if scene_context:
        system_prompt += f"\n\nEl usuario está actualmente en: {scene_context}. Puedes hacer referencia a esta ubicación si es relevante."

    messages = [{"role": "system", "content": system_prompt}]
    
    if conversation_history:
        for msg in conversation_history[-3:]:  # Últimos 3 mensajes
            role = "user" if msg.get("is_from_user") else "assistant"
            messages.append({"role": role, "content": msg.get("content", "")})
    messages.append({"role": "user", "content": user_message})
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=200,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise Exception(f"Error OpenAI: {e}")

def generate_groq_response(user_message: str, scene_context: str = None, conversation_history: List[Dict] = None) -> str:
    """Generar respuesta usando Groq API"""
    
    api_key = os.getenv("GROQ_API_KEY")
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    system_prompt = """Eres un asistente virtual de Tecsup Perú. Ayudas con información sobre carreras técnicas, 
    admisiones, instalaciones y vida estudiantil. Responde de forma amigable y concisa en español."""
    
    if scene_context:
        system_prompt += f" El usuario está en: {scene_context}."
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Simplificar el historial
    if conversation_history and len(conversation_history) > 0:
        for msg in conversation_history[-2:]:  # Solo últimos 2 mensajes
            if msg.get("content") and msg.get("content").strip():
                role = "user" if msg.get("is_from_user") else "assistant"
                messages.append({"role": role, "content": msg.get("content")})
    
    messages.append({"role": "user", "content": user_message})
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "max_tokens": 150,
        "temperature": 0.7,
        "stream": False  # Asegurar que no sea streaming
    }
    
    try:
        with httpx.Client(timeout=15.0) as client:  # Aumentar timeout
            response = client.post(url, headers=headers, json=data)
            
            # Debug: imprimir detalles del error
            if response.status_code != 200:
                print(f"Error Status: {response.status_code}")
                print(f"Error Response: {response.text}")
                raise Exception(f"Groq API error {response.status_code}: {response.text}")
            
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
            
    except httpx.HTTPError as e:
        raise Exception(f"Error HTTP Groq: {e}")
    except Exception as e:
        raise Exception(f"Error Groq: {e}")

def generate_claude_response(user_message: str, scene_context: str = None, conversation_history: List[Dict] = None) -> str:
    """Generar respuesta usando Claude API de Anthropic"""
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    url = "https://api.anthropic.com/v1/messages"
    
    system_prompt = """Eres un asistente virtual de Tecsup, institución técnica de Perú. 
    Ayuda con información sobre carreras, admisiones, instalaciones y servicios estudiantiles."""
    
    if scene_context:
        system_prompt += f" Usuario ubicado en: {scene_context}."
    
    conversation_context = ""
    if conversation_history:
        for msg in conversation_history[-3:]:
            role = "Usuario" if msg.get("is_from_user") else "Asistente"
            conversation_context += f"{role}: {msg.get('content', '')}\n"
    
    prompt = f"{conversation_context}Usuario: {user_message}\nAsistente:"
    
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    
    data = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 150,
        "system": system_prompt,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        with httpx.Client() as client:
            response = client.post(url, headers=headers, json=data, timeout=15.0)
            response.raise_for_status()
            result = response.json()
            return result["content"][0]["text"].strip()
    except Exception as e:
        raise Exception(f"Error Claude: {e}")

def generate_predefined_response(user_message: str) -> str:
    """Respuestas predefinidas como fallback cuando no hay API de IA configurada"""
    
    responses_by_keyword = {
        "hola": [
            "¡Hola! Bienvenido al tour virtual de Tecsup. ¿En qué puedo ayudarte?",
            "¡Hola! Soy tu asistente virtual. ¿Tienes alguna pregunta sobre Tecsup?"
        ],
        "biblioteca": [
            "La biblioteca de Tecsup cuenta con recursos digitales y espacios de estudio. ¿Te gustaría saber más?",
            "Nuestra biblioteca está equipada con tecnología moderna para el aprendizaje."
        ],
        "laboratorio": [
            "Los laboratorios de Tecsup tienen tecnología de última generación. ¿Qué área te interesa?",
            "Contamos con laboratorios especializados en diferentes carreras técnicas."
        ],
        "carrera": [
            "Tecsup ofrece carreras técnicas en ingeniería y tecnología. ¿Tienes alguna preferencia?",
            "Nuestras carreras preparan profesionales técnicos altamente calificados."
        ],
        "admision": [
            "El proceso de admisión incluye evaluaciones. ¿Necesitas información específica?",
            "Para postular necesitas educación secundaria completa y aprobar nuestras evaluaciones."
        ],
        "gracias": [
            "¡De nada! ¿Hay algo más en lo que pueda ayudarte?",
            "¡Un placer ayudarte! ¿Tienes alguna otra pregunta?"
        ]
    }
    
    user_message_lower = user_message.lower()
    
    for keyword, responses in responses_by_keyword.items():
        if keyword in user_message_lower:
            return random.choice(responses)
    
    return "Gracias por tu mensaje. ¿En qué puedo ayudarte con información sobre Tecsup?"


# API ENDPOINTS
@router.post("/message", response_model=ChatResponse)
async def send_message(
    message: ChatMessage,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Enviar mensaje al chatbot con IA integrada.
    Crea conversación automáticamente si no existe una.
    """
    
    conversation = None
    is_new_conversation = False
    
    # Obtener o crear conversación
    if message.conversation_id:
        conversation = conversation_crud.get_conversation(db, message.conversation_id)
        if not conversation or conversation.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Conversación no encontrada")
    else:
        # Crear nueva conversación automáticamente
        conversation_data = ConversationCreate(
            title=f"Conversación - {current_user.username}",
            scene_id=message.scene_context_id,
            is_active=True
        )
        conversation = conversation_crud.create_conversation(db, conversation_data, current_user.id)
        is_new_conversation = True
    
    # Crear mensaje del usuario
    user_message = message_crud.create_user_message(
        db, message.content, conversation.id, message.scene_context_id
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
    
    # Obtener contexto de escena
    scene_context = None
    if message.scene_context_id:
        scene = scene_crud.get_scene(db, message.scene_context_id)
        scene_context = scene.name if scene else None
    
    # Generar respuesta con IA
    bot_response = generate_ai_response(
        user_message=message.content,
        scene_context=scene_context,
        conversation_history=conversation_history
    )
    
    # Crear mensaje del asistente (scene_context_id = None como solicitaste)
    assistant_message = message_crud.create_assistant_message(
        db, bot_response, conversation.id, None
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
                "full_name": user.full_name,
                "conversations": user.conversations,
                "messages": user.messages
            }
            for user in top_users
        ]
    }