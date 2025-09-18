from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.dependencies import get_current_active_user, get_current_admin_user
from app.schemas.scene import Scene as SceneSchema, SceneCreate, SceneUpdate, SceneSimple
from app.crud.scene import scene_crud
from app.models.user import User

router = APIRouter(prefix="/scenes", tags=["Scenes"])

@router.get("/", response_model=List[SceneSimple])
async def read_scenes(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtiene todas las escenas (vista simple)"""
    scenes = scene_crud.get_scenes(db, skip=skip, limit=limit)
    return scenes

@router.get("/{scene_id}", response_model=SceneSchema)
async def read_scene(
    scene_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtiene una escena específica con todos sus datos"""
    scene = scene_crud.get_scene(db, scene_id=scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Escena no encontrada")
    return scene

@router.get("/key/{scene_key}", response_model=SceneSchema)
async def read_scene_by_key(
    scene_key: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtiene una escena por su key"""
    scene = scene_crud.get_scene_by_key(db, scene_key=scene_key)
    if not scene:
        raise HTTPException(status_code=404, detail="Escena no encontrada")
    return scene

@router.post("/", response_model=SceneSchema)
async def create_scene(
    scene: SceneCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Crea una nueva escena (solo admin)"""
    
    # Verificar si la escena ya existe
    if scene_crud.get_scene_by_key(db, scene_key=scene.scene_key):
        raise HTTPException(
            status_code=400,
            detail="Ya existe una escena con esa key"
        )
    
    return scene_crud.create_scene(db=db, scene=scene)

@router.put("/{scene_id}", response_model=SceneSchema)
async def update_scene(
    scene_id: int,
    scene_update: SceneUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Actualiza una escena (solo admin)"""
    
    # Verificar que la escena existe
    existing_scene = scene_crud.get_scene(db, scene_id=scene_id)
    if not existing_scene:
        raise HTTPException(status_code=404, detail="Escena no encontrada")
    
    # Verificar que la scene_key no esté en uso por otra escena
    if scene_update.scene_key:
        key_scene = scene_crud.get_scene_by_key(db, scene_key=scene_update.scene_key)
        if key_scene and key_scene.id != scene_id:
            raise HTTPException(
                status_code=400,
                detail="Ya existe una escena con esa key"
            )
    
    updated_scene = scene_crud.update_scene(db, scene_id, scene_update)
    return updated_scene

@router.delete("/{scene_id}")
async def delete_scene(
    scene_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Elimina una escena (solo admin)"""
    deleted = scene_crud.delete_scene(db, scene_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Escena no encontrada")
    
    return {"message": "Escena eliminada correctamente"}