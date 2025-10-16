import os
import openai
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Optional

from app.models.chat import Message, Conversation


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
            "- Admisión y requisitos\n"
            "- Instalaciones\n"
            "- Vida estudiantil\n"
            "- Horarios y calendario académico\n"
            "- Becas y financiamiento\n\n"
            "Responde siempre en español de manera amigable y concisa."
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
                {"role": "system", "content": "Genera un título corto y descriptivo (máx. 6 palabras)."},
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
