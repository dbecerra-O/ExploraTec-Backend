from rapidfuzz import fuzz, process
from typing import Dict, List, Optional, Tuple
import heapq
import unicodedata
import re

class SceneGraph:
    """Grafo de escenas del campus con conexiones y distancias"""
    
    # Definir conexiones entre escenas (grafo)
    SCENE_CONNECTIONS = {
        "0-entrada": [
            ("1-patio-central", 1)
        ],
        "1-patio-central": [
            ("0-entrada", 1),
            ("18-maquinitas", 1),
            ("22-pabellon-4---piso-1", 1),
            ("25-entrada-biblioteca", 1),
            ("2-camino", 1)
        ],
        "2-camino": [
            ("1-patio-central", 1),
            ("18-maquinitas", 1),
            ("4-pabellon-7", 1),
            ("13-cerca-del-ajedrez", 1)
        ],
        "3-pabellon-4---piso-2-s": [
            ("20-pabellon-4---piso-2-m", 1),
            ("24-pabellon-4", 1),
            ("5-area-de-salones-4b", 1)
        ],
        "4-pabellon-7": [
            ("14-salon-701", 1),
            ("16-salon-702", 1),
            ("17-salon-704", 1),
            ("5-area-de-salones-4b", 1),
            ("7-area-de-tecnologia", 1),
            ("8-area-de-mecanica", 1),
            ("2-camino", 1)
        ],
        "5-area-de-salones-4b": [
            ("4-pabellon-7", 1),
            ("24-pabellon-4", 1),
            ("3-pabellon-4---piso-2-s", 1),
            ("6-polideportivo", 1)
        ],
        "6-polideportivo": [
            ("7-area-de-tecnologia", 1),
            ("5-area-de-salones-4b", 1)
        ],
        "7-area-de-tecnologia": [
            ("6-polideportivo", 1),
            ("15-salones-de-mecanica", 1),
            ("8-area-de-mecanica", 1),
            ("5-area-de-salones-4b", 1),
            ("4-pabellon-7", 1),
            ("2-camino", 1)
        ],
        "8-area-de-mecanica": [
            ("12-zona-verde", 1),
            ("9-mecanica", 1),
            ("7-area-de-tecnologia", 1),
            ("5-area-de-salones-4b", 1),
            ("4-pabellon-7", 1),
            ("2-camino", 1)
        ],
        "9-mecanica": [
            ("8-area-de-mecanica", 1),
            ("10-segundo-piso-e", 1)
        ],
        "10-segundo-piso-e": [
            ("9-mecanica", 1),
            ("11-segundo-piso-s", 1)
        ],
        "11-segundo-piso-s": [
            ("10-segundo-piso-e", 1),
            ("15-salones-de-mecanica", 1),
            ("27-pabellon-14", 1),
            ("7-area-de-tecnologia", 1)
        ],
        "12-zona-verde": [
            ("8-area-de-mecanica", 1),
            ("13-cerca-del-ajedrez", 1)
        ],
        "13-cerca-del-ajedrez": [
            ("12-zona-verde", 1),
            ("2-camino", 1)
        ],
        "14-salon-701": [
            ("4-pabellon-7", 1)
        ],
        "15-salones-de-mecanica": [
            ("11-segundo-piso-s", 1),
            ("7-area-de-tecnologia", 1),
            ("27-pabellon-14", 1)
        ],
        "16-salon-702": [
            ("4-pabellon-7", 1)
        ],
        "17-salon-704": [
            ("4-pabellon-7", 1)
        ],
        "18-maquinitas": [
            ("2-camino", 1),
            ("1-patio-central", 1),
            ("24-pabellon-4", 1),
            ("19-pabellon-4---piso-2-e", 1)
        ],
        "19-pabellon-4---piso-2-e": [
            ("18-maquinitas", 1),
            ("23-salon-pabellon-4", 1),
            ("20-pabellon-4---piso-2-m", 1)
        ],
        "20-pabellon-4---piso-2-m": [
            ("19-pabellon-4---piso-2-e", 1),
            ("21-pabellon-4---piso-2--a", 1),
            ("3-pabellon-4---piso-2-s", 1)
        ],
        "21-pabellon-4---piso-2--a": [
            ("20-pabellon-4---piso-2-m", 1),
            ("22-pabellon-4---piso-1", 1)
        ],
        "22-pabellon-4---piso-1": [
            ("1-patio-central", 1),
            ("25-entrada-biblioteca", 1)
        ],
        "23-salon-pabellon-4": [
            ("19-pabellon-4---piso-2-e", 1)
        ],
        "24-pabellon-4": [
            ("18-maquinitas", 1),
            ("5-area-de-salones-4b", 1)
        ],
        "25-entrada-biblioteca": [
            ("26-biblioteca", 1),
            ("1-patio-central", 1),
            ("22-pabellon-4---piso-1", 1)
        ],
        "26-biblioteca": [
            ("25-entrada-biblioteca", 1)
        ],
        "27-pabellon-14": [
            ("15-salones-de-mecanica", 1),
            ("11-segundo-piso-s", 1),
            ("28-salon-1509", 1)
        ],
        "28-salon-1509": [
            ("27-pabellon-14", 1)
        ]
    }
    
    SCENE_ALIASES = {
        # Entrada
        "entrada": "0-entrada",
        "ingreso": "0-entrada",
        "puerta": "0-entrada",
        
        # Patio Central
        "patio": "1-patio-central",
        "patio central": "1-patio-central",
        "centro": "1-patio-central",
        
        # Camino
        "camino": "2-camino",
        "pasillo": "2-camino",
        
        # Biblioteca
        "biblioteca": "26-biblioteca",
        "biblio": "26-biblioteca",
        "entrada biblioteca": "25-entrada-biblioteca",
        
        # Polideportivo
        "polideportivo": "6-polideportivo",
        "poli": "6-polideportivo",
        "cancha": "6-polideportivo",
        "deportes": "6-polideportivo",
        
        # Áreas
        "tecnologia": "7-area-de-tecnologia",
        "area tecnologia": "7-area-de-tecnologia",
        "mecanica": "8-area-de-mecanica",
        "area mecanica": "8-area-de-mecanica",
        "zona verde": "12-zona-verde",
        
        # Pabellones
        "pabellon 4": "24-pabellon-4",
        "pabellon 7": "4-pabellon-7",
        "pabellon 14": "27-pabellon-14",
        
        # Salones específicos
        "salon 701": "14-salon-701",
        "701": "14-salon-701",
        "salon 702": "16-salon-702",
        "702": "16-salon-702",
        "salon 704": "17-salon-704",
        "704": "17-salon-704",
        "salon 1509": "28-salon-1509",
        "1509": "28-salon-1509",
        
        # Maquinitas
        "maquinitas": "18-maquinitas",
        "maquinas": "18-maquinitas",
        
        # Ajedrez
        "ajedrez": "13-cerca-del-ajedrez",
        "cerca ajedrez": "13-cerca-del-ajedrez"
    }
    
    @staticmethod
    def dijkstra(start: str, end: str) -> Optional[Tuple[List[str], int]]:
        """
        Algoritmo de Dijkstra para encontrar la ruta más corta
        
        Returns:
            (path, total_distance) o None si no hay ruta
        """
        if start not in SceneGraph.SCENE_CONNECTIONS or end not in SceneGraph.SCENE_CONNECTIONS:
            return None
        
        # Priority queue: (distancia, nodo_actual, camino)
        pq = [(0, start, [start])]
        visited = set()
        
        while pq:
            dist, current, path = heapq.heappop(pq)
            
            if current in visited:
                continue
            
            visited.add(current)
            
            # Llegamos al destino
            if current == end:
                return (path, dist)
            
            # Explorar vecinos
            for neighbor, weight in SceneGraph.SCENE_CONNECTIONS.get(current, []):
                if neighbor not in visited:
                    heapq.heappush(pq, (dist + weight, neighbor, path + [neighbor]))
        
        return None
    
    @staticmethod
    def resolve_scene_name(query: str, threshold: int = 70) -> Optional[str]:
        """Extraer nombre de escena de la consulta del usuario"""
        def _normalize(text: str) -> str:
            if not text:
                return ""
            text = unicodedata.normalize("NFD", text)
            text = "".join(ch for ch in text if not unicodedata.combining(ch))
            text = text.lower()
            text = re.sub(r"[^\w\s]", "", text)
            text = re.sub(r"\s+", " ", text).strip()
            return text

        raw_lower = query.lower()
        search_areas = [raw_lower]
        if "desde" in raw_lower:
            before_desde = raw_lower.split("desde", 1)[0].strip()
            if before_desde:
                search_areas.insert(0, before_desde)

        normalized_alias_map = { _normalize(alias): alias for alias in SceneGraph.SCENE_ALIASES.keys() }

        for area in search_areas:
            norm_area = _normalize(area)
            for norm_alias, alias in normalized_alias_map.items():
                if not norm_alias:
                    continue
                if norm_alias in norm_area:
                    return SceneGraph.SCENE_ALIASES[alias]

        words = _normalize(raw_lower).split()
        
        best_match = None
        best_adjusted_score = 0
        best_word = None
        
        for word in words:
            
            if len(word) < 3:
                continue
            result = process.extractOne(
                word,
                list(normalized_alias_map.keys()),
                scorer=fuzz.ratio,
                score_cutoff=threshold
            )
            
            if result:
                norm_alias, raw_score, _ = result
                alias = normalized_alias_map.get(norm_alias, norm_alias)
                
                word_len = len(word)
                alias_len = len(norm_alias)
                length_ratio = min(word_len, alias_len) / max(word_len, alias_len)
                
                adjusted_score = raw_score * length_ratio
                
                if adjusted_score > best_adjusted_score:
                    best_match = alias
                    best_adjusted_score = adjusted_score
                    best_word = word
                    print(f"🔍 '{word}' → '{alias}': raw={raw_score}, len_ratio={length_ratio:.2f}, adjusted={adjusted_score:.1f}")
            
        if best_match and best_adjusted_score >= 60:
            print(f"✅ Match final: '{best_word}' → '{best_match}' (score ajustado: {best_adjusted_score:.1f})")
            return SceneGraph.SCENE_ALIASES[best_match]
        
        print(f"❌ No se encontró match suficientemente bueno (mejor score: {best_adjusted_score:.1f})")
        return None
    
    @staticmethod
    def get_navigation_info(from_scene_key: str, to_scene_key: str) -> Optional[Dict]:
        """Obtener información de navegación entre dos escenas"""
        result = SceneGraph.dijkstra(from_scene_key, to_scene_key)
        
        if not result:
            return None
        
        path, distance = result
        
        return {
            "from_scene": from_scene_key,
            "to_scene": to_scene_key,
            "path": path,
            "distance": distance,
            "steps": len(path) - 1,
            "should_navigate": True
        }