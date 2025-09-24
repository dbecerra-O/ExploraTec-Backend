from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.dependencies import get_current_active_user
from app.schemas.user import User as UserSchema, UserUpdate
from app.crud.user import user_crud
from app.models.user import User

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserSchema)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Obtiene la información del usuario actual"""
    return current_user

@router.put("/me", response_model=UserSchema)
async def update_users_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Actualiza la información del usuario actual"""
    
    # Verificar que el email no esté en uso por otro usuario
    if user_update.email:
        existing_user = user_crud.get_user_by_email(db, email=user_update.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=400,
                detail="El email ya está en uso"
            )
    
    # Verificar que el username no esté en uso por otro usuario
    if user_update.username:
        existing_user = user_crud.get_user_by_username(db, username=user_update.username)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=400,
                detail="El username ya está en uso"
            )
    
    # Actualizar usuario
    updated_user = user_crud.update_user(db, current_user.id, user_update)
    if not updated_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return updated_user