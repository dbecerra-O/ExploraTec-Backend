from rapidfuzz import fuzz, process
from typing import Dict, List, Optional, Tuple
import heapq

class SceneGraph:
    """Grafo de escenas del campus con conexiones y distancias"""
    
    # Definir conexiones entre escenas (grafo)
    SCENE_CONNECTIONS = {
        "0-entrada": [
            ("1-patio-central", 1),  # (destino, peso/distancia)
        ],
        "1-patio-central": [
            ("0-entrada", 1),
            ("2-biblioteca", 2),
            ("3-laboratorio-mecanica", 2),
            ("4-comedor", 1),
            ("5-auditorio", 3),
        ],
        "2-biblioteca": [
            ("1-patio-central", 2),
        ],
        "3-laboratorio-mecanica": [
            ("1-patio-central", 2),
        ],
        "4-comedor": [
            ("1-patio-central", 1),
        ],
        "5-auditorio": [
            ("1-patio-central", 3),
        ],
    }
    
    # Mapeo de nombres a scene_key
    SCENE_ALIASES = {
        "biblioteca": "2-biblioteca",
        "biblio": "2-biblioteca",
        "laboratorio": "3-laboratorio-mecanica",
        "lab": "3-laboratorio-mecanica",
        "mecanica": "3-laboratorio-mecanica",
        "comedor": "4-comedor",
        "cafeteria": "4-comedor",
        "auditorio": "5-auditorio",
        "entrada": "0-entrada",
        "patio": "1-patio-central",
        "patio central": "1-patio-central",
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
        
        return None  # No hay ruta
    
    @staticmethod
    def resolve_scene_name(query: str, threshold: int = 70) -> Optional[str]:
        """Extraer nombre de escena de la consulta del usuario"""
        query_lower = query.lower()
        
        for alias, scene_key in SceneGraph.SCENE_ALIASES.items():
            if alias in query_lower:
                return scene_key

        words = query_lower.split()
        
        best_match = None
        best_adjusted_score = 0
        best_word = None
        
        for word in words:
            
            if len(word) < 4:
                continue
            # Comparar cada palabra con los aliases
            result = process.extractOne(
                word,
                SceneGraph.SCENE_ALIASES.keys(),
                scorer=fuzz.ratio,
                score_cutoff=threshold
            )
            
            if result:
                alias, raw_score, _ = result
                
                # CLAVE: Penalizar diferencias grandes de longitud
                word_len = len(word)
                alias_len = len(alias)
                length_ratio = min(word_len, alias_len) / max(word_len, alias_len)
                
                adjusted_score = raw_score * length_ratio
                
                if adjusted_score > best_adjusted_score:
                    best_match = alias
                    best_adjusted_score = adjusted_score
                    best_word = word
                    print(f"🔍 '{word}' → '{alias}': raw={raw_score}, len_ratio={length_ratio:.2f}, adjusted={adjusted_score:.1f}")
            
        # Requerir score ajustado mínimo de 60
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