from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY
from pgvector.sqlalchemy import Vector
from app.database import Base


class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)  # El texto que leerá el usuario
    embedding = Column(Vector(1536))  # El vector para buscar similitud
    category = Column(String(100), nullable=False, index=True)  # 'carreras', 'admision', 'costos'
    subcategory = Column(String(100))  # 'mecatronica', 'requisitos'
    
    # Relaciones Escena
    scene_id = Column(Integer, ForeignKey("scenes.id"), nullable=True)
    scene = relationship("Scene", foreign_keys=[scene_id])

    is_active = Column(Boolean, default=True, index=True)
    usage_count = Column(Integer, default=0)  # Para saber qué info se usa más
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<KnowledgeBase(id={self.id}, category='{self.category}', content='{self.content[:50]}...')>"