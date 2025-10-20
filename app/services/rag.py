"""Servicio RAG (Retrieval-Augmented Generation)."""

from typing import List, Dict, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
import math

from app.models.knowledge import KnowledgeBase
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
            sql = """
                SELECT id, content, category, 
                embedding <=> CAST(:q_vector AS vector) AS distance
                FROM knowledge_base 
                WHERE is_active = true 
                AND (scene_id = :scene_id OR scene_id IS NULL)
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
        vector_results = [
            {
                "id": r["id"], 
                "content": r["content"], 
                "category": r["category"], 
                "distance": float(r["distance"])
            } 
            for r in rows
        ]

        if distance_threshold is not None:
            vector_results = [r for r in vector_results if r["distance"] <= distance_threshold]

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

    # CAMBIO: Keyword search también incluye NULL
    keyword_results = []
    try:
        query_q = db.query(KnowledgeBase).filter(
            KnowledgeBase.is_active == True,
            KnowledgeBase.content.ilike(f"%{query}%")
        )
        if scene_id:
            query_q = query_q.filter(
                (KnowledgeBase.scene_id == scene_id) | (KnowledgeBase.scene_id.is_(None))
            )
        
        for kb in query_q.limit(top_k).all():
            keyword_results.append({
                "id": kb.id,
                "content": kb.content,
                "category": kb.category,
                "distance": 0.5
            })
    except Exception as e:
        print(f"⚠️ Error keyword search: {e}")

    combined = merge_hybrid_results(vector_results, keyword_results, top_k)
    combined = rerank_passages(query, combined)
    
    # CAMBIO: Deduplicar IDs antes de incrementar
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

# Línea ~100 (después de tu función)
def merge_hybrid_results(vector_results: List[Dict], keyword_results: List[Dict], top_k: int) -> List[Dict]:
    """Fusiona y deduplica resultados vector + keyword"""
    seen_ids = set()
    merged = []
    
    # Priorizar vector results
    for r in vector_results:
        if r["id"] not in seen_ids:
            merged.append(r)
            seen_ids.add(r["id"])
    
    # Agregar keyword results no duplicados
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
        
        # Score combinado: distancia vectorial + overlap
        combined_score = (1 - p.get("distance", 0.5)) * 0.7 + (overlap / max(len(query_words), 1)) * 0.3
        scored.append((p, combined_score))
    
    # Ordenar por score descendente
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