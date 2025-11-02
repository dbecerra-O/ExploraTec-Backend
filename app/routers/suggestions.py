from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.crud.scene import scene_crud
from app.crud.event import event_crud

router = APIRouter(prefix="/suggestions", tags=["Suggestions"])


def _generate_suggestions_for_scene(scene, db: Session) -> List[str]:
    """Genera sugerencias dinámicas basadas en la escena.

    - Siempre sugiere "¿Qué hay aquí?" y "¿Cómo llego a X?"
    - Si hay eventos activos en la escena, sugiere "¿Qué eventos hay?"
    - Añade sugerencias generales útiles según si la escena es relevante.
    """
    suggestions: List[str] = []
    if not scene:
        # Sugerencias globales por defecto
        return [
            "¿Qué carreras técnicas ofrecen?",
            "¿Cómo puedo postular?",
            "¿Dónde está la biblioteca?",
            "¿Qué servicios tiene el campus?"
        ]

    # Preguntas base
    suggestions.append("¿Qué hay aquí?")
    suggestions.append(f"¿Cómo llego a {scene.name}?")

    # Eventos asociados a la escena
    try:
        events = event_crud.get_events_by_scene(db, scene.id)
        if events and len(events) > 0:
            suggestions.append("¿Qué eventos hay?")
    except Exception:
        # Si falla la consulta de eventos, no bloqueamos las sugerencias
        pass

    # Sugerencias adicionales según relevancia
    if getattr(scene, "is_relevant", False):
        suggestions.append("¿Hay actividades destacadas aquí?")

    # Otras sugerencias genéricas para la escena
    suggestions.extend([
        "¿Cuál es el horario?",
        "¿Qué servicios están disponibles aquí?"
    ])

    # Devolver únicas y limitadas a 6
    unique = []
    for s in suggestions:
        if s not in unique:
            unique.append(s)
    return unique[:6]


@router.get("/")
def get_suggestions(scene_context: str = None, db: Session = Depends(get_db)):
    """Obtener preguntas sugeridas según escena (usar scene_key)

    Parámetro: scene_context = scene_key (ej. "0-entrada").
    """
    scene = None
    if scene_context:
        scene = scene_crud.get_scene_by_key(db, scene_context)

    suggestions = _generate_suggestions_for_scene(scene, db)

    return {
        "scene_context": scene_context,
        "suggestions": suggestions
    }