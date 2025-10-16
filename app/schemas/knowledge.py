from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class KnowledgeBaseCreate(BaseModel):
    content: str
    category: str
    subcategory: Optional[str] = None
    scene_id: Optional[int] = None


class KnowledgeBase(BaseModel):
    id: int
    content: str
    category: str
    subcategory: Optional[str] = None
    is_active: bool
    usage_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class SearchResult(BaseModel):
    """Lo que retorna la búsqueda vectorial"""
    id: int
    content: str
    category: str
    distance: float  # Qué tan similar es (menor = mejor)