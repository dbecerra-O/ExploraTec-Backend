from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_active_user
from app.schemas.user import User as UserSchema
from app.schemas.scene import Scene as SceneSchema
from app.crud.user import user_crud
from app.crud.scene import scene_crud
from app.models.user import User

router = APIRouter(prefix="/user", tags=["User Navigation"])

@router.post("/enter-scene/{scene_key}", response_model=UserSchema)
async def enter_scene(
    scene_key: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """El usuario entra a una escena específica"""
    
    # Verificar que la escena existe
    scene = scene_crud.get_scene_by_key(db, scene_key=scene_key)
    if not scene:
        raise HTTPException(status_code=404, detail="Escena no encontrada")
    
    # Actualizar la escena actual del usuario
    from app.schemas.user import UserUpdate
    user_update = UserUpdate(current_scene_id=scene.id)
    updated_user = user_crud.update_user(db, current_user.id, user_update)
    
    return updated_user

@router.get("/current-scene", response_model=SceneSchema)
async def get_current_scene(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtiene la escena actual del usuario"""
    
    if not current_user.current_scene_id:
        raise HTTPException(
            status_code=404, 
            detail="El usuario no está en ninguna escena actualmente"
        )
    
    scene = scene_crud.get_scene(db, scene_id=current_user.current_scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="La escena actual no existe")
    
    return scene

@router.post("/leave-scene", response_model=UserSchema)
async def leave_scene(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """El usuario sale de la escena actual"""
    
    from app.schemas.user import UserUpdate
    user_update = UserUpdate(current_scene_id=None)
    updated_user = user_crud.update_user(db, current_user.id, user_update)
    
    return updated_user