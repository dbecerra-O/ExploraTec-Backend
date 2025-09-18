from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Scene(Base):
    __tablename__ = "scenes"
    
    id = Column(Integer, primary_key=True, index=True)
    scene_key = Column(String(100), unique=True, nullable=False)  # ej: "0-entrada"
    name = Column(String(255), nullable=False)  # ej: "Entrada"
    face_size = Column(Integer, nullable=False)
    initial_yaw = Column(Float, nullable=True)
    initial_pitch = Column(Float, nullable=True)
    initial_fov = Column(Float, nullable=True)
    
    # Relaciones
    link_hotspots = relationship("LinkHotspot", back_populates="scene")
    info_hotspots = relationship("InfoHotspot", back_populates="scene")
    levels = relationship("SceneLevel", back_populates="scene")

class LinkHotspot(Base):
    __tablename__ = "link_hotspots"
    
    id = Column(Integer, primary_key=True, index=True)
    yaw = Column(Float, nullable=False)
    pitch = Column(Float, nullable=False)
    rotation = Column(Float, nullable=True)
    target_scene_id = Column(String(100), nullable=False)  # referencia a otra escena
    scene_id = Column(Integer, ForeignKey("scenes.id"))
    
    scene = relationship("Scene", back_populates="link_hotspots")

class InfoHotspot(Base):
    __tablename__ = "info_hotspots"
    
    id = Column(Integer, primary_key=True, index=True)
    yaw = Column(Float, nullable=False)
    pitch = Column(Float, nullable=False)
    title = Column(String(255), nullable=False)
    text = Column(Text, nullable=False)
    scene_id = Column(Integer, ForeignKey("scenes.id"))
    
    scene = relationship("Scene", back_populates="info_hotspots")

class SceneLevel(Base):
    __tablename__ = "scene_levels"
    
    id = Column(Integer, primary_key=True, index=True)
    tile_size = Column(Integer, nullable=False)
    size = Column(Integer, nullable=False)
    fallback_only = Column(Boolean, default=False)
    scene_id = Column(Integer, ForeignKey("scenes.id"))
    
    scene = relationship("Scene", back_populates="levels")