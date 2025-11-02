from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Scene(Base):
    __tablename__ = "scenes"

    id = Column(Integer, primary_key=True, index=True)
    scene_key = Column(String(100), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    # Campo que indica si la escena es especialmente relevante/importante
    is_relevant = Column(Boolean, default=False, index=True)

    def __repr__(self):
        return f"<Scene(id={self.id}, key='{self.scene_key}', name='{self.name}', relevant={self.is_relevant})>"