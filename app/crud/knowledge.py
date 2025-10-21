from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.knowledge import KnowledgeBase
from app.schemas.knowledge import KnowledgeBaseCreate, SearchResult
from app.services.embeddings import embed_text
from app.services.rag import retrieve_similar_passages


def add_knowledge(db: Session, kb: KnowledgeBaseCreate) -> KnowledgeBase:
    """Crear una entrada en knowledge_base y calcular su embedding."""
    new = KnowledgeBase(
        content=kb.content,
        category=kb.category,
        subcategory=kb.subcategory,
        scene_id=kb.scene_id,
        is_active=True
    )
    db.add(new)
    db.commit()
    db.refresh(new)

    try:
        emb = embed_text(kb.content)
        new.embedding = emb
        db.add(new)
        db.commit()
        db.refresh(new)
    except Exception:
        db.rollback()

    return new


def get_knowledge(db: Session, kb_id: int) -> Optional[KnowledgeBase]:
    return db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()


def search_similar_knowledge(db: Session, query: str, top_k: int = 4, scene_id: Optional[int] = None, distance_threshold: Optional[float] = None) -> List[SearchResult]:
    """Buscar pasajes similares y mapear a SearchResult schema."""
    rows = retrieve_similar_passages(db, query, top_k=top_k, scene_id=scene_id, distance_threshold=distance_threshold)
    results: List[SearchResult] = []
    for r in rows:
        results.append(SearchResult(id=r["id"], content=r["content"], category=r.get("category", ""), distance=r.get("distance", 0.0)))
    return results
