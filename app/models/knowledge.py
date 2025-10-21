from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from datetime import datetime
from app.database import Base


class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536))
    category = Column(String(100), nullable=False, index=True)
    subcategory = Column(String(100))
    
    # Relaciones Escena
    scene_id = Column(Integer, ForeignKey("scenes.id"), nullable=True)
    scene = relationship("Scene", foreign_keys=[scene_id])

    is_active = Column(Boolean, default=True, index=True)
    usage_count = Column(Integer, default=0) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<KnowledgeBase(id={self.id}, category='{self.category}', content='{self.content[:50]}...')>"
    
# Modelo Event
class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    event_date = Column(DateTime, nullable=False)
    location = Column(String(200))
    scene_id = Column(Integer, ForeignKey("scenes.id"))
    
    # Para búsqueda
    embedding = Column(Vector(1536))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    scene = relationship("Scene")