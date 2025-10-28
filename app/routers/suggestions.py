from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud.scene import scene_crud

router = APIRouter(prefix="/suggestions", tags=["Suggestions"])

SUGGESTED_QUESTIONS = {
    "0-entrada": [
        "¿Cómo llego a la biblioteca?",
        "¿Qué carreras ofrecen?",
        "¿Dónde está el comedor?"
    ],
    "1-patio-central": [
        "¿Qué hay en el patio?",
        "¿Cómo llego al laboratorio?",
        "¿Dónde está el auditorio?"
    ],
    "2-biblioteca": [
        "¿Qué servicios tiene la biblioteca?",
        "¿Cuál es el horario?",
        "¿Cómo saco libros prestados?"
    ],
    "3-laboratorio-mecanica": [
        "¿Qué equipos hay aquí?",
        "¿Horario del laboratorio?",
        "¿Qué carreras usan este lab?"
    ],
    "4-comedor": [
        "¿Qué hay de menú?",
        "¿Cuánto cuesta el almuerzo?",
        "¿Horario del comedor?"
    ],
    "5-auditorio": [
        "¿Qué eventos hay?",
        "¿Capacidad del auditorio?",
        "¿Cómo reservo el espacio?"
    ],
    None: [
        "¿Qué carreras técnicas ofrecen?",
        "¿Cómo puedo postular?",
        "¿Dónde está la biblioteca?",
        "¿Qué servicios tiene el campus?"
    ]
}

@router.get("/")
def get_suggestions(scene_context: str = None, db: Session = Depends(get_db)):
    """Obtener preguntas sugeridas según escena (usar scene_key)

    Parámetro: scene_context = scene_key (ej. "0-entrada").
    """
    scene_key = None
    if scene_context:
        # scene_context already a scene_key
        scene_key = scene_context

    return {
        "scene_context": scene_key,
        "suggestions": SUGGESTED_QUESTIONS.get(scene_key, SUGGESTED_QUESTIONS[None])
    }