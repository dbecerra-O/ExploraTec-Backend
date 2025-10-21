from typing import List, Dict, Optional, Any
from sqlalchemy import text
from sqlalchemy.orm import Session
import math

from app.models.knowledge import KnowledgeBase, Event
from app.services.embeddings import embed_text


def cosine_distance(a: List[float], b: List[float]) -> float:
    """Calcula distance = 1 - cosine_similarity entre dos vectores."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 1.0
    return 1.0 - (dot / (norm_a * norm_b))


def retrieve_similar_passages(db: Session, query: str, top_k: int = 4, scene_id: Optional[int] = None, distance_threshold: Optional[float] = None) -> List[Dict]:
    """Búsqueda híbrida: vector + keyword"""

    q_emb = embed_text(query)
    q_emb_str = '[' + ','.join(map(str, q_emb)) + ']'

    vector_results = []
    try:
        if scene_id is not None:
            sql_scene = """
                SELECT id, content, category,
                embedding <=> CAST(:q_vector AS vector) AS distance
                FROM knowledge_base
                WHERE is_active = true
                AND scene_id = :scene_id
                ORDER BY distance ASC
                LIMIT :top_k
            """
            result_scene = db.execute(text(sql_scene), {"q_vector": q_emb_str, "scene_id": scene_id, "top_k": top_k})
            rows_scene = result_scene.mappings().all()
            vector_results = [
                {"id": r["id"], "content": r["content"], "category": r["category"], "distance": float(r["distance"])}
                for r in rows_scene
            ]

            if len(vector_results) < top_k:
                remaining = top_k - len(vector_results)
                sql_global = """
                    SELECT id, content, category,
                    embedding <=> CAST(:q_vector AS vector) AS distance
                    FROM knowledge_base
                    WHERE is_active = true
                    AND scene_id IS NULL
                    ORDER BY distance ASC
                    LIMIT :remaining
                """
                result_global = db.execute(text(sql_global), {"q_vector": q_emb_str, "remaining": remaining})
                rows_global = result_global.mappings().all()
                vector_results += [
                    {"id": r["id"], "content": r["content"], "category": r["category"], "distance": float(r["distance"])}
                    for r in rows_global
                ]
        else:
            sql = """
                SELECT id, content, category,
                embedding <=> CAST(:q_vector AS vector) AS distance
                FROM knowledge_base
                WHERE is_active = true
                ORDER BY distance ASC
                LIMIT :top_k
            """
            result = db.execute(text(sql), {"q_vector": q_emb_str, "top_k": top_k})
            rows = result.mappings().all()
            vector_results = [
                {"id": r["id"], "content": r["content"], "category": r["category"], "distance": float(r["distance"])}
                for r in rows
            ]

        if distance_threshold is not None:
            vector_results = [r for r in vector_results if r.get("distance", 1.0) <= distance_threshold]

    except Exception as e:
        print(f"⚠️ Error vector search con pgvector, fallback Python: {e}")
        db.rollback()

        # CAMBIO: Fallback también incluye NULL
        query_q = db.query(KnowledgeBase).filter(KnowledgeBase.is_active == True)
        if scene_id is not None:
            query_q = query_q.filter(
                (KnowledgeBase.scene_id == scene_id) | (KnowledgeBase.scene_id.is_(None))
            )
        docs = query_q.all()

        docs_with_emb = [d for d in docs if getattr(d, "embedding", None) is not None]
        vector_results = []
        for d in docs_with_emb:
            dist = cosine_distance(q_emb, list(d.embedding))
            vector_results.append({
                "id": d.id,
                "content": d.content,
                "category": d.category,
                "distance": float(dist)
            })

        vector_results.sort(key=lambda x: x["distance"])
        if distance_threshold is not None:
            vector_results = [r for r in vector_results if r["distance"] <= distance_threshold]
        vector_results = vector_results[:top_k]

    # Keyword search: prefer resultados de la escena y completar con global si hace falta
    keyword_results = []
    try:
        if scene_id is not None:
            scene_q = db.query(KnowledgeBase).filter(
                KnowledgeBase.is_active == True,
                KnowledgeBase.scene_id == scene_id,
                KnowledgeBase.content.ilike(f"%{query}%")
            ).limit(top_k).all()
            for kb in scene_q:
                keyword_results.append({"id": kb.id, "content": kb.content, "category": kb.category, "distance": 0.5})

            if len(keyword_results) < top_k:
                remaining = top_k - len(keyword_results)
                global_q = db.query(KnowledgeBase).filter(
                    KnowledgeBase.is_active == True,
                    KnowledgeBase.scene_id.is_(None),
                    KnowledgeBase.content.ilike(f"%{query}%")
                ).limit(remaining).all()
                for kb in global_q:
                    if kb.id not in {r['id'] for r in keyword_results}:
                        keyword_results.append({"id": kb.id, "content": kb.content, "category": kb.category, "distance": 0.5})
        else:
            query_q = db.query(KnowledgeBase).filter(
                KnowledgeBase.is_active == True,
                KnowledgeBase.content.ilike(f"%{query}%")
            ).limit(top_k).all()
            for kb in query_q:
                keyword_results.append({"id": kb.id, "content": kb.content, "category": kb.category, "distance": 0.5})
    except Exception as e:
        print(f"⚠️ Error keyword search: {e}")

    combined = merge_hybrid_results(vector_results, keyword_results, top_k)
    combined = rerank_passages(query, combined)
    
    if combined:
        try:
            unique_ids = list(set(r["id"] for r in combined))
            db.query(KnowledgeBase).filter(
                KnowledgeBase.id.in_(unique_ids)
            ).update(
                {"usage_count": KnowledgeBase.usage_count + 1},
                synchronize_session=False
            )
            db.commit()
        except Exception as e:
            print(f"⚠️ Error al incrementar usage_count: {e}")
            db.rollback()

    return combined

def merge_hybrid_results(vector_results: List[Dict], keyword_results: List[Dict], top_k: int) -> List[Dict]:
    """Fusiona y deduplica resultados vector + keyword"""
    seen_ids = set()
    merged = []
    
    for r in vector_results:
        if r["id"] not in seen_ids:
            merged.append(r)
            seen_ids.add(r["id"])
    
    for r in keyword_results:
        if r["id"] not in seen_ids:
            merged.append(r)
            seen_ids.add(r["id"])
    
    return merged[:top_k]

def rerank_passages(query: str, passages: List[Dict]) -> List[Dict]:
    """Reordena pasajes por relevancia usando overlap de palabras"""
    if not passages:
        return passages
    
    query_words = set(query.lower().split())
    scored = []
    
    for p in passages:
        content_words = set(p["content"].lower().split())
        overlap = len(query_words & content_words)
        
        combined_score = (1 - p.get("distance", 0.5)) * 0.7 + (overlap / max(len(query_words), 1)) * 0.3
        scored.append((p, combined_score))
    
    ranked = [p for p, _ in sorted(scored, key=lambda x: x[1], reverse=True)]
    return ranked

def format_retrieved_passages(passages: List[Dict], max_chars_each: int = 800) -> Optional[str]:
    """Formatea los pasajes recuperados en un string para inyectar en el prompt."""
    if not passages:
        return None
    parts = []
    for i, p in enumerate(passages, start=1):
        content = p.get("content", "").strip()
        if len(content) > max_chars_each:
            content = content[:max_chars_each].rsplit(" ", 1)[0] + "..."
        parts.append(f"[{i}] ({p.get('category')}) {content}")
    return "\n\n".join(parts)

def search_events(db: Session, query: str, scene_id: Optional[int] = None) -> List[Any]:
    """Busca eventos relevantes basados en la consulta"""
    try:
        from datetime import datetime
        
        search_terms = query.lower().split()
        query_scene = db.query(Event).filter(
            Event.is_active == True,
            Event.event_date >= datetime.now(),
            Event.scene_id == scene_id
        )

        events_found = []
        for event in query_scene.all():
            event_text = f"{event.title} {event.description} {event.location}".lower()
            matches = sum(1 for term in search_terms if term in event_text)
            if matches > 0:
                events_found.append((event, matches))

        events_found.sort(key=lambda x: x[1], reverse=True)

        if events_found:
            return [event for event, score in events_found[:2]]

        return []
    
    except Exception as e:
        print(f"⚠️ Error en search_events: {e}")
        return []
    
def search_events_context(db: Session, query: str, scene_id: Optional[int] = None) -> Optional[str]:
    """Busca eventos relevantes y los formatea como contexto.

    Prioriza eventos de la escena; si no hay eventos y la query sugiere 'global', buscará globalmente.
    """
    try:
        q_lower = (query or "").lower()
        global_indicators = ["en general", "en todo", "en el campus", "todo el campus", "en general del campus", "por todo el campus", "en todas"]
        allow_global = any(token in q_lower for token in global_indicators)

        # Buscar por escena primero
        events = search_events(db, query, scene_id)

        if not events and allow_global:
            from datetime import datetime
            global_events = db.query(Event).filter(
                Event.is_active == True,
                Event.event_date >= datetime.now(),
                Event.scene_id.is_(None)
            ).order_by(Event.event_date).limit(3).all()
            events = global_events

        if not events:
            return None

        events_text = "📅 **Eventos próximos:**\n\n"
        for event in events[:3]:
            events_text += f"• **{event.title}**\n"
            events_text += f"  📍 {event.location or 'Ubicación por definir'}\n"
            events_text += f"  🕒 {event.event_date.strftime('%d/%m/%Y %H:%M')}\n"
            events_text += f"  📝 {event.description[:150]}...\n\n"

        return events_text.strip()

    except Exception as e:
        print(f"⚠️ Error buscando eventos: {e}")
        return None