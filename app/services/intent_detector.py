from typing import Dict, List, Tuple
from enum import Enum


class IntentCategory(str, Enum):
    """Categorías de intención del usuario (HU-02)"""
    NAVIGATION = "navegacion"
    LOCATION_INFO = "informacion_ubicacion"
    EVENTS = "eventos"
    CAREERS = "carreras"
    ADMISSIONS = "admisiones"
    SERVICES = "servicios"
    SCHEDULES = "horarios"
    GENERAL = "general"


class IntentDetector:
    """
    Detector de intenciones basado en palabras clave con sistema de puntuación (HU-02)
    """
    
    # Palabras clave organizadas por prioridad
    INTENT_KEYWORDS = {
        IntentCategory.NAVIGATION: {
            "high_priority": ["como llego", "como voy", "ruta", "camino", "direccion"],
            "medium_priority": ["donde esta", "donde queda", "ubicacion"],
            "low_priority": ["ir a", "llegar"]
        },
        IntentCategory.EVENTS: {
            "high_priority": ["eventos", "actividades", "calendario"],
            "medium_priority": ["que hay", "talleres", "charlas"],
            "low_priority": ["hoy", "esta semana"]
        },
        IntentCategory.CAREERS: {
            "high_priority": ["carreras", "que puedo estudiar", "programas"],
            "medium_priority": ["ingenieria", "tecnologia", "especialidad"],
            "low_priority": ["estudiar", "profesion"]
        },
        IntentCategory.ADMISSIONS: {
            "high_priority": ["admision", "postular", "inscripcion", "matricula"],
            "medium_priority": ["requisitos", "examen", "proceso"],
            "low_priority": ["como ingreso", "vacantes"]
        },
        IntentCategory.SERVICES: {
            "high_priority": ["biblioteca", "comedor", "cafeteria", "laboratorio"],
            "medium_priority": ["servicios", "gimnasio", "enfermeria"],
            "low_priority": ["donde puedo"]
        },
        IntentCategory.SCHEDULES: {
            "high_priority": ["horario", "que hora", "cuando abre", "cuando cierra"],
            "medium_priority": ["atencion", "disponible", "funcionamiento"],
            "low_priority": ["abierto", "dias"]
        },
        IntentCategory.LOCATION_INFO: {
            "high_priority": ["que es", "que hay en", "informacion sobre"],
            "medium_priority": ["cuentame", "describe", "para que sirve"],
            "low_priority": ["que tiene"]
        }
    }
    
    @staticmethod
    def detect_intent(message: str) -> Dict:
        """
        Detectar la intención principal del mensaje
        
        Args:
            message: Texto del mensaje del usuario
            
        Returns:
            {
                "category": str,              # Categoría detectada
                "confidence": float,          # Confianza (0-1)
                "keywords_found": List[str],  # Palabras clave encontradas
                "requires_clarification": bool,  # Si necesita clarificación
                "all_matches": List[Tuple[str, float]]  # Todas las categorías detectadas
            }
        """
        message_lower = message.lower()
        
        # Calcular puntuación para cada categoría
        category_scores = {}
        keywords_by_category = {}
        
        for category, priority_keywords in IntentDetector.INTENT_KEYWORDS.items():
            score = 0.0
            found_keywords = []
            
            # High priority keywords (peso 3)
            for keyword in priority_keywords["high_priority"]:
                if keyword in message_lower:
                    score += 3.0
                    found_keywords.append(keyword)
            
            # Medium priority (peso 2)
            for keyword in priority_keywords["medium_priority"]:
                if keyword in message_lower:
                    score += 2.0
                    found_keywords.append(keyword)
            
            # Low priority (peso 1)
            for keyword in priority_keywords["low_priority"]:
                if keyword in message_lower:
                    score += 1.0
                    found_keywords.append(keyword)
            
            if score > 0:
                category_scores[category] = score
                keywords_by_category[category] = found_keywords
        
        # Si no hay coincidencias, es consulta general
        if not category_scores:
            return {
                "category": IntentCategory.GENERAL.value,
                "confidence": 1.0,
                "keywords_found": [],
                "requires_clarification": False,
                "all_matches": []
            }
        
        # Ordenar categorías por puntuación
        sorted_categories = sorted(
            category_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        # Mejor categoría
        best_category, best_score = sorted_categories[0]
        
        # Normalizar confianza (máximo esperado: 6 puntos = 2 keywords high priority)
        confidence = min(best_score / 6.0, 1.0)
        
        # Verificar si hay múltiples intenciones con scores similares (HU-02: manejo de ambigüedad)
        requires_clarification = False
        if len(sorted_categories) >= 2:
            second_score = sorted_categories[1][1]
            # Si la diferencia es menor a 2 puntos, hay ambigüedad
            if (best_score - second_score) < 2.0:
                requires_clarification = True
                confidence = 0.5  # Reducir confianza por ambigüedad
        
        return {
            "category": best_category.value,
            "confidence": round(confidence, 2),
            "keywords_found": keywords_by_category[best_category],
            "requires_clarification": requires_clarification,
            "all_matches": [
                (cat.value, round(score, 2)) 
                for cat, score in sorted_categories
            ]
        }
    
    @staticmethod
    def get_clarification_message(all_matches: List[Tuple[str, float]]) -> str:
        """
        Generar mensaje de clarificación cuando hay múltiples intenciones (HU-02)
        
        Args:
            all_matches: Lista de tuplas (categoría, puntuación)
            
        Returns:
            Mensaje pidiendo clarificación al usuario
        """
        if len(all_matches) < 2:
            return "¿Podrías ser más específico con tu pregunta?"
        
        # Tomar las 2 intenciones principales
        top_intents = all_matches[:2]
        
        clarification_map = {
            "navegacion": "¿Quieres saber cómo llegar a algún lugar?",
            "eventos": "¿Te interesa conocer eventos o actividades?",
            "carreras": "¿Buscas información sobre carreras disponibles?",
            "admisiones": "¿Necesitas información sobre el proceso de admisión?",
            "servicios": "¿Quieres saber sobre servicios del campus?",
            "horarios": "¿Necesitas conocer horarios de atención?",
            "informacion_ubicacion": "¿Buscas información sobre un lugar específico?"
        }
        
        options = []
        for intent, _ in top_intents:
            if intent in clarification_map:
                options.append(clarification_map[intent])
        
        if options:
            return "Entiendo que podrías estar preguntando sobre:\n" + "\n".join(f"• {opt}" for opt in options)
        
        return "¿Podrías ser más específico con tu pregunta?"