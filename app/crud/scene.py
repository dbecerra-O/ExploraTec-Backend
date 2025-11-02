from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.scene import Scene
from app.schemas.scene import SceneCreate, SceneUpdate

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
            is_relevant=getattr(scene, 'is_relevant', False)
        )
        db.add(db_scene)
        db.commit()
        db.refresh(db_scene)
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

# Instancia del CRUD
scene_crud = SceneCRUD()