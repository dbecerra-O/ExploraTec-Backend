from typing import Dict, List, Tuple
from enum import Enum
import re

class IntentCategory(str, Enum):
    """Categorías de intención del usuario"""
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
    Detector de intenciones mejorado con:
    - Detección por patrones regex (alta prioridad)
    - Sistema de puntuación por keywords (fallback)
    - Manejo de múltiples intenciones
    """

    NAVIGATION_PATTERNS = [
        r'\b(quiero|voy|vamos|puedo|necesito)\s+(ir|llegar)\s+(a|al|a la|hacia)\b',
        r'\bc[oó]mo\s+(llego|voy|llegar|ir)\b',
        r'\b(llevame|ll[eé]vame|gu[ií]ame)\s+(a|al|a la|hacia)\b',
        r'\b(ruta|camino|direcci[oó]n)\s+(a|al|a la|hacia|para)\b',
        r'\bd[oó]nde\s+(est[aá]|queda|se encuentra)\b',
        r'\b(necesito|debo|tengo que)\s+(estar|ir|llegar)\s+(en|a|al)\b',
        r'\b(me dirijo|voy rumbo|en camino)\s+(a|al|hacia)\b',
        r'\b(visitar[eé]?|conocer)\s+(el|la|los)\b',
    ]
    
    # Palabras clave organizadas por prioridad
    INTENT_KEYWORDS = {
        IntentCategory.NAVIGATION: {
            "high_priority": [
                "como llego", "como voy", "como llegar", 
                "ruta", "camino", "direccion",
                "quiero ir", "llevame", "vamos a", "guiame"
            ],
            "medium_priority": [
                "donde esta", "donde queda", "ubicacion",
                "ir a", "ir al", "voy a"
            ],
            "low_priority": ["llegar", "cerca"]
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
            "high_priority": ["servicios del", "servicios de", "que ofrece"],
            "medium_priority": ["servicios", "gimnasio", "enfermeria"],
            "low_priority": ["donde puedo", "tiene"]
        },
        IntentCategory.SCHEDULES: {
            "high_priority": ["horario", "que hora", "cuando abre", "cuando cierra"],
            "medium_priority": ["atencion", "disponible", "funcionamiento"],
            "low_priority": ["abierto", "dias"]
        },
        IntentCategory.LOCATION_INFO: {
            "high_priority": ["que es esto", "que es este", "que hay aqui"],
            "medium_priority": ["que es", "que hay en", "informacion sobre", "cuentame", "describe"],
            "low_priority": ["que tiene", "para que sirve"]
        }
    }
    
    @staticmethod
    def _normalize_common_typos(message: str) -> str:
        """Corregir typos comunes en palabras de navegación"""
        typo_map = {
            "quero": "quiero", "kiero": "quiero", "qiero": "quiero",
            "yego": "llego", "liego": "llego", "llgo": "llego",
            "cmo": "como", "comoo": "como",
            "dnde": "donde", "dond": "donde", "dode": "donde",
            "bicaliteca": "biblioteca", "bibloteca": "biblioteca",
            "comidor": "comedor", "comedro": "comedor",
            "laboraotrio": "laboratorio", "laboratrio": "laboratorio"
        }
        
        words = message.split()
        corrected = []
        for word in words:
            clean = word.lower().strip('.,!?¿')
            corrected.append(typo_map.get(clean, word))
        
        return " ".join(corrected)

    @staticmethod
    def detect_intent(message: str) -> Dict:
        """
        Detectar la intención principal del mensaje
        
        Prioridad de detección:
        1. Patrones de navegación (regex)
        2. Sistema de puntuación (keywords)
        3. Manejo de múltiples intenciones
        """
        message_lower = message.lower()
        
        # ========================================
        # PASO 1: DETECCIÓN POR PATRONES (PRIORIDAD MÁXIMA)
        # ========================================
        nav_match = IntentDetector.detect_navigation_pattern(message_lower)
        if nav_match:
            return nav_match
        
        # ========================================
        # PASO 2: SISTEMA DE PUNTUACIÓN (KEYWORDS)
        # ========================================
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
        
        # ========================================
        # PASO 3: PRIORIZAR NAVEGACIÓN SI EMPATE
        # ========================================
        best_category, best_score = sorted_categories[0]
        
        # Si hay empate o diferencia pequeña, priorizar NAVEGACION
        if len(sorted_categories) >= 2:
            second_category, second_score = sorted_categories[1]
            
            # Si navegación está en top 2 y la diferencia es < 2 puntos
            if (IntentCategory.NAVIGATION in [best_category, second_category] and 
                abs(best_score - second_score) < 2.0):
                best_category = IntentCategory.NAVIGATION
                best_score = max(best_score, second_score)
        
        # Normalizar confianza
        confidence = min(best_score / 6.0, 1.0)
        
        # Verificar si hay múltiples intenciones con scores similares
        requires_clarification = False
        if len(sorted_categories) >= 2:
            second_score = sorted_categories[1][1]
            # Si la diferencia es menor a 2 puntos Y navegación no está involucrada
            if ((best_score - second_score) < 2.0 and 
                best_category != IntentCategory.NAVIGATION):
                requires_clarification = True
                confidence = 0.5
        
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
    def detect_navigation_pattern(message: str) -> Dict:
        """Detectar patrones claros de navegación usando regex"""
        for pattern in IntentDetector.NAVIGATION_PATTERNS:
            if re.search(pattern, message):
                # Extraer palabras clave del match
                keywords = []
                if "quiero ir" in message or "voy a" in message:
                    keywords.append("quiero ir")
                elif "como llego" in message or "como voy" in message:
                    keywords.append("como llego")
                elif "llevame" in message or "guiame" in message:
                    keywords.append("llevame")
                elif "donde esta" in message or "donde queda" in message:
                    keywords.append("donde esta")
                else:
                    keywords.append("navegación detectada")
                
                return {
                    "category": IntentCategory.NAVIGATION.value,
                    "confidence": 0.90,  # Alta confianza por patrón
                    "keywords_found": keywords,
                    "requires_clarification": False,
                    "all_matches": [(IntentCategory.NAVIGATION.value, 0.90)]
                }
        
        return None

    @staticmethod
    def get_clarification_message(all_matches: List[Tuple[str, float]]) -> str:
        """Generar mensaje de clarificación cuando hay múltiples intenciones"""
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