from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.scene import Scene, LinkHotspot, InfoHotspot, SceneLevel
from app.schemas.scene import SceneCreate, SceneUpdate, LinkHotspotCreate, InfoHotspotCreate, SceneLevelCreate

class SceneCRUD:
    def get_scene(self, db: Session, scene_id: int) -> Optional[Scene]:
        """Obtiene una escena por ID"""
        return db.query(Scene).filter(Scene.id == scene_id).first()
    
    def get_scene_by_key(self, db: Session, scene_key: str) -> Optional[Scene]:
        """Obtiene una escena por su key"""
        return db.query(Scene).filter(Scene.scene_key == scene_key).first()
    
    def get_scenes(self, db: Session, skip: int = 0, limit: int = 100) -> List[Scene]:
        """Obtiene una lista de escenas"""
        return db.query(Scene).offset(skip).limit(limit).all()
    
    def create_scene(self, db: Session, scene: SceneCreate) -> Scene:
        """Crea una nueva escena"""
        db_scene = Scene(
            scene_key=scene.scene_key,
            name=scene.name,
            face_size=scene.face_size,
            initial_yaw=scene.initial_yaw,
            initial_pitch=scene.initial_pitch,
            initial_fov=scene.initial_fov,
        )
        db.add(db_scene)
        db.commit()
        db.refresh(db_scene)
        
        # Crear hotspots y levels si se proporcionan
        if scene.link_hotspots:
            for hotspot_data in scene.link_hotspots:
                self.create_link_hotspot(db, hotspot_data, db_scene.id)
        
        if scene.info_hotspots:
            for hotspot_data in scene.info_hotspots:
                self.create_info_hotspot(db, hotspot_data, db_scene.id)
        
        if scene.levels:
            for level_data in scene.levels:
                self.create_scene_level(db, level_data, db_scene.id)
        
        return db_scene
    
    def update_scene(self, db: Session, scene_id: int, scene_update: SceneUpdate) -> Optional[Scene]:
        """Actualiza una escena"""
        db_scene = self.get_scene(db, scene_id)
        if not db_scene:
            return None
        
        update_data = scene_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_scene, field, value)
        
        db.commit()
        db.refresh(db_scene)
        return db_scene
    
    def delete_scene(self, db: Session, scene_id: int) -> bool:
        """Elimina una escena"""
        db_scene = self.get_scene(db, scene_id)
        if not db_scene:
            return False
        
        db.delete(db_scene)
        db.commit()
        return True
    
    # CRUD para LinkHotspot
    def create_link_hotspot(self, db: Session, hotspot: LinkHotspotCreate, scene_id: int) -> LinkHotspot:
        """Crea un link hotspot"""
        db_hotspot = LinkHotspot(
            yaw=hotspot.yaw,
            pitch=hotspot.pitch,
            rotation=hotspot.rotation,
            target_scene_id=hotspot.target_scene_id,
            scene_id=scene_id
        )
        db.add(db_hotspot)
        db.commit()
        db.refresh(db_hotspot)
        return db_hotspot
    
    def delete_link_hotspot(self, db: Session, hotspot_id: int) -> bool:
        """Elimina un link hotspot"""
        hotspot = db.query(LinkHotspot).filter(LinkHotspot.id == hotspot_id).first()
        if not hotspot:
            return False
        db.delete(hotspot)
        db.commit()
        return True
    
    # CRUD para InfoHotspot
    def create_info_hotspot(self, db: Session, hotspot: InfoHotspotCreate, scene_id: int) -> InfoHotspot:
        """Crea un info hotspot"""
        db_hotspot = InfoHotspot(
            yaw=hotspot.yaw,
            pitch=hotspot.pitch,
            title=hotspot.title,
            text=hotspot.text,
            scene_id=scene_id
        )
        db.add(db_hotspot)
        db.commit()
        db.refresh(db_hotspot)
        return db_hotspot
    
    def delete_info_hotspot(self, db: Session, hotspot_id: int) -> bool:
        """Elimina un info hotspot"""
        hotspot = db.query(InfoHotspot).filter(InfoHotspot.id == hotspot_id).first()
        if not hotspot:
            return False
        db.delete(hotspot)
        db.commit()
        return True
    
    # CRUD para SceneLevel
    def create_scene_level(self, db: Session, level: SceneLevelCreate, scene_id: int) -> SceneLevel:
        """Crea un scene level"""
        db_level = SceneLevel(
            tile_size=level.tile_size,
            size=level.size,
            fallback_only=level.fallback_only,
            scene_id=scene_id
        )
        db.add(db_level)
        db.commit()
        db.refresh(db_level)
        return db_level
    
    def delete_scene_level(self, db: Session, level_id: int) -> bool:
        """Elimina un scene level"""
        level = db.query(SceneLevel).filter(SceneLevel.id == level_id).first()
        if not level:
            return False
        db.delete(level)
        db.commit()
        return True

# Instancia del CRUD
scene_crud = SceneCRUD()