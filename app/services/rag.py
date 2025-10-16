"""Servicio RAG (Retrieval-Augmented Generation)."""

from typing import List, Dict, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
import math

from app.models.knowledge import KnowledgeBase
from app.services.embeddings import embed_text


def _cosine_distance(a: List[float], b: List[float]) -> float:
    """Calcula distance = 1 - cosine_similarity entre dos vectores."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 1.0
    return 1.0 - (dot / (norm_a * norm_b))


def retrieve_similar_passages(db: Session, query: str, top_k: int = 4, scene_id: Optional[int] = None, distance_threshold: Optional[float] = None) -> List[Dict]:
    """Recupera los pasajes más similares a `query`."""
    q_emb = embed_text(query)
    
    # Convertir lista Python a string formato pgvector: '[-0.04,0.02,...]'
    q_emb_str = '[' + ','.join(map(str, q_emb)) + ']'

    try:
        # Construir query SQL con placeholders :param
        if scene_id is not None:
            sql = """
                SELECT id, content, category, 
                embedding <=> CAST(:q_vector AS vector) AS distance
                FROM knowledge_base 
                WHERE is_active = true AND scene_id = :scene_id 
                ORDER BY distance ASC 
                LIMIT :top_k
            """
            stmt = text(sql)
            result = db.execute(stmt, {"q_vector": q_emb_str, "scene_id": scene_id, "top_k": top_k})
        else:
            sql = """
                SELECT id, content, category, 
                embedding <=> CAST(:q_vector AS vector) AS distance
                FROM knowledge_base 
                WHERE is_active = true 
                ORDER BY distance ASC 
                LIMIT :top_k
            """
            stmt = text(sql)
            result = db.execute(stmt, {"q_vector": q_emb_str, "top_k": top_k})

        rows = result.mappings().all()
        results = [
            {
                "id": r["id"], 
                "content": r["content"], 
                "category": r["category"], 
                "distance": float(r["distance"])
            } 
            for r in rows
        ]
        
        if distance_threshold is not None:
            results = [r for r in results if r["distance"] <= distance_threshold]
        
        if results:
            for r in results:
                db.query(KnowledgeBase).filter(
                    KnowledgeBase.id == r["id"]
                ).update({"usage_count": KnowledgeBase.usage_count + 1})
            db.commit()

        return results

    except Exception as e:
        # Fallback: calcular distancia en Python
        print(f"⚠️ Error usando pgvector, activando fallback: {e}")
        db.rollback()
        
        query_q = db.query(KnowledgeBase).filter(KnowledgeBase.is_active == True)
        if scene_id is not None:
            query_q = query_q.filter(KnowledgeBase.scene_id == scene_id)
        docs = query_q.all()

        docs_with_emb = [d for d in docs if getattr(d, "embedding", None) is not None]
        out = []
        for d in docs_with_emb:
            dist = _cosine_distance(q_emb, list(d.embedding))
            out.append({"id": d.id, "content": d.content, "category": d.category, "distance": float(dist)})

        out.sort(key=lambda x: x["distance"])
        if distance_threshold is not None:
            out = [r for r in out if r["distance"] <= distance_threshold]
        return out[:top_k]


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