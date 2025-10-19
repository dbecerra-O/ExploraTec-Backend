import os
import openai
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Optional

from app.services.scene_graph import SceneGraph
from app.models.chat import Message, Conversation
from app.crud.scene import scene_crud
from app.crud.chat import conversation_crud, message_crud
from app.models.user import User
from app.schemas.chat import ChatMessage, ChatResponse, ConversationSimple, ConversationCreate
from app.services.intent_detector import IntentDetector
from app.services.rag import retrieve_similar_passages, format_retrieved_passages
import time


# === OPENAI CLIENTE ===
def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise Exception("OPENAI_API_KEY no encontrada en las variables de entorno")
    return openai.OpenAI(api_key=api_key, timeout=30)


# === VALIDACIONES ===
def validate_message_content(content: str) -> tuple[bool, Optional[str]]:
    content = content.strip()
    if not content:
        return False, "El mensaje no puede estar vacío"
    if len(content) < 2:
        return False, "El mensaje es demasiado corto"
    if len(content) > 500:
        return False, "El mensaje no puede superar los 500 caracteres"
    if len(set(content)) < 3:
        return False, "El mensaje parece ser spam"
    return True, None


def check_rate_limit(db: Session, user_id: int) -> tuple[bool, Optional[str]]:
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent_messages = db.query(Message).join(Conversation).filter(
        Conversation.user_id == user_id,
        Message.is_from_user == True,
        Message.created_at >= one_hour_ago
    ).count()
    if recent_messages >= 10:
        return False, f"Has alcanzado el límite de {10} mensajes por hora. Intenta más tarde."
    return True, None

def check_conversation_limit(db: Session, conversation_id: int) -> tuple[bool, Optional[str]]:
    message_count = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).count()
    if message_count >= 5:
        return False, f"Esta conversación ha alcanzado el límite de {5} mensajes. Crea una nueva conversación."
    return True, None

def handle_navigation_intent(message: str, current_scene_id: int, db: Session) -> Optional[Dict]:
    """Detectar si el usuario quiere navegar a otra escena"""
    
    # Obtener scene_key actual
    current_scene = scene_crud.get_scene(db, current_scene_id)
    if not current_scene:
        return None
    
    # Detectar escena destino del mensaje
    target_scene_key = SceneGraph.resolve_scene_name(message)
    if not target_scene_key:
        return None
    
    # NUEVO: Validar si ya está en el destino
    if current_scene.scene_key == target_scene_key:
        target_scene = scene_crud.get_scene_by_key(db, target_scene_key)
        return {
            "from_scene": current_scene.scene_key,
            "to_scene": target_scene_key,
            "from_scene_name": current_scene.name,
            "to_scene_name": target_scene.name if target_scene else target_scene_key,
            "to_scene_id": current_scene_id,
            "path": [current_scene.scene_key],
            "distance": 0,
            "steps": 0,
            "should_navigate": False,
            "already_here": True
        }
    
    # Calcular ruta
    nav_info = SceneGraph.get_navigation_info(
        current_scene.scene_key, 
        target_scene_key
    )
    
    if not nav_info:
        return None
    
    # Obtener nombres amigables
    target_scene = scene_crud.get_scene_by_key(db, target_scene_key)
    
    return {
        **nav_info,
        "from_scene_name": current_scene.name,
        "to_scene_name": target_scene.name if target_scene else target_scene_key,
        "to_scene_id": target_scene.id if target_scene else None,
        "already_here": False
    }

# === IA RESPUESTA ===
def generate_ai_response(user_message: str, scene_context: str = None,
                         conversation_history: List[Dict] = None,
                         retrieved_context: str = None) -> tuple:
    try:
        client = get_openai_client()
        system_prompt = (
            "Eres un asistente virtual de Tecsup, una institución de educación técnica en Perú.\n"
            "Tu objetivo es ayudar a los usuarios con información sobre:\n"
            "- Carreras técnicas\n"
            "- Proceso de admisión y requisitos\n"
            "- Instalaciones del campus (laboratorios, biblioteca, deportes)\n"
            "- Vida estudiantil y servicios\n"
            "- Horarios y calendario académico\n"
            "- Becas y financiamiento\n\n"
            
            # NUEVO: Instrucción de corrección ortográfica
            "IMPORTANTE: Si detectas errores ortográficos en nombres de lugares, "
            "corrige automáticamente en tu respuesta.\n"
            "Responde de manera amigable, informativa y concisa siempre en español, sin importar el idioma en que el usuario escriba.\n"
            "Si no tienes información específica, ofrece ayuda general y sugiere contactar a la administración."
        )

        if scene_context:
            system_prompt += f"\n\nContexto adicional: El usuario está en {scene_context}."

        if retrieved_context:
            system_prompt += f"\n\nInformación relacionada:\n{retrieved_context}\n\n"

        messages = [{"role": "system", "content": system_prompt}]

        if conversation_history:
            for msg in conversation_history[-3:]:
                if msg.get("content"):
                    role = "user" if msg.get("is_from_user") else "assistant"
                    messages.append({"role": role, "content": msg["content"]})

        messages.append({"role": "user", "content": user_message})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=300,
            temperature=0.7,
        )

        result = response.choices[0].message.content.strip()
        total_tokens = response.usage.total_tokens
        return result, total_tokens

    except openai.RateLimitError:
        raise HTTPException(status_code=429, detail="Demasiadas solicitudes. Intenta más tarde.")
    except openai.APITimeoutError:
        raise HTTPException(status_code=504, detail="Timeout en la respuesta de IA.")
    except Exception as e:
        print(f"❌ Error al generar respuesta: {e}")
        raise HTTPException(status_code=500, detail="Error al generar respuesta de IA.")


def generate_conversation_title(message_content: str) -> str:
    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Genera un título corto y descriptivo (máx. 6 palabras). Corrígelo si tiene errores ortográficos."},
                {"role": "user", "content": message_content}
            ],
            max_tokens=15,
            temperature=0.5
        )
        if response.choices:
            return response.choices[0].message.content.strip()
        return "Conversación sin título"
    except Exception:
        words = message_content.split()[:4]
        return " ".join(words) + "..."

# FUNCIONES AUXILIARES

def get_or_create_conversation(
    db: Session,
    message: ChatMessage,
    current_user: User
) -> tuple[Conversation, bool]:
    """Obtiene conversación existente o crea una nueva"""
    if message.conversation_id:
        conversation = conversation_crud.get_conversation(db, message.conversation_id)
        if not conversation or conversation.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Conversación no encontrada")
        
        # Verificar límite de mensajes por conversación
        conv_limit_ok, conv_limit_msg = check_conversation_limit(db, conversation.id)
        if not conv_limit_ok:
            raise HTTPException(status_code=400, detail=conv_limit_msg)
        
        return conversation, False
    else:
        # Crear nueva conversación automáticamente
        auto_title = generate_conversation_title(message.content)
        conversation_data = ConversationCreate(
            title=auto_title,
            scene_id=message.scene_context_id,
            is_active=True
        )
        conversation = conversation_crud.create_conversation(
            db, conversation_data, current_user.id
        )
        return conversation, True


def get_scene_context(db: Session, scene_id: Optional[int]) -> Optional[str]:
    """Obtiene el nombre de la escena actual"""
    if not scene_id:
        return None
    scene = scene_crud.get_scene(db, scene_id)
    return scene.name if scene else None


def get_conversation_history(db: Session, conversation_id: int) -> List[Dict]:
    """Obtiene el historial de mensajes de la conversación"""
    conversation_messages = message_crud.get_conversation_messages(db, conversation_id)
    return [
        {
            "content": msg.content,
            "is_from_user": msg.is_from_user,
            "created_at": msg.created_at
        }
        for msg in conversation_messages
    ]


def retrieve_knowledge_context(
    db: Session,
    query: str,
    scene_id: Optional[int]
) -> Optional[str]:
    """Recupera contexto relevante de la knowledge base usando RAG"""
    try:
        passages = retrieve_similar_passages(
            db, query, top_k=4, scene_id=scene_id
        )
        return format_retrieved_passages(passages)
    except Exception as e:
        print(f"⚠️ Error en RAG retrieval: {e}")
        db.rollback()
        return None


def handle_clarification_response(
    db: Session,
    conversation: Conversation,
    user_message: Message,
    intent_result: Dict,
    message: ChatMessage,
    is_new_conversation: bool,
    start_time: float
) -> ChatResponse:
    """Maneja respuesta cuando se necesita clarificación de intención"""
    clarification_msg = IntentDetector.get_clarification_message(
        intent_result["all_matches"]
    )
    
    assistant_message = message_crud.create_assistant_message(
        db, clarification_msg, conversation.id, None
    )
    
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
    
    return ChatResponse(
        user_message=user_message,
        assistant_message=assistant_message,
        conversation=conversation_simple,
        is_new_conversation=is_new_conversation,
        navigation=None,
        response_time_ms=response_time_ms
    )


def handle_navigation_if_needed(
    db: Session,
    intent_category: str,
    message_content: str,
    scene_context_id: Optional[int],
    assistant_message: Message
) -> Optional[Dict]:
    """Detecta y maneja navegación si la intención es 'navegacion'"""
    if intent_category != "navegacion" or not scene_context_id:
        return None
    
    navigation_data = handle_navigation_intent(
        message_content, 
        scene_context_id, 
        db
    )
    
    if not navigation_data:
        return None
    
    # Enriquecer respuesta del bot según el caso
    if navigation_data.get("already_here"):
        # Usuario ya está en el destino
        new_response = f"Ya te encuentras en {navigation_data['to_scene_name']}. ¿En qué más puedo ayudarte?"
    else:
        # Hay ruta para navegar
        steps = " → ".join([s.split("-")[1] for s in navigation_data["path"]])
        new_response = assistant_message.content + f"\n\n🗺️ Ruta sugerida: {steps}"
    
    assistant_message.content = new_response
    db.commit()
    
    return navigation_data