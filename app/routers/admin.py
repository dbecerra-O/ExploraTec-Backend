from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.dependencies import get_current_admin_user
from app.schemas.user import User as UserSchema, UserCreate, UserUpdate
from app.crud.user import user_crud
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/users", response_model=List[UserSchema])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Obtiene todos los usuarios (solo admin)"""
    users = user_crud.get_user_not_admin(db, skip=skip, limit=limit)
    return users

@router.post("/users", response_model=UserSchema)
async def create_user(
    user: UserCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Crea un nuevo usuario (solo admin)"""
    
    # Verificar si el usuario ya existe
    if user_crud.get_user_by_email(db, email=user.email):
        raise HTTPException(
            status_code=400,
            detail="El email ya está registrado"
        )
    
    if user_crud.get_user_by_username(db, username=user.username):
        raise HTTPException(
            status_code=400,
            detail="El username ya está en uso"
        )
    
    # Crear el usuario
    db_user = user_crud.create_user(db=db, user=user)
    return db_user

@router.get("/users/{user_id}", response_model=UserSchema)
async def read_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Obtiene un usuario específico (solo admin)"""
    user = user_crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

@router.put("/users/{user_id}", response_model=UserSchema)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Actualiza un usuario (solo admin)"""
    
    # Verificar que el usuario existe
    existing_user = user_crud.get_user(db, user_id=user_id)
    if not existing_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Verificar que el email no esté en uso por otro usuario
    if user_update.email:
        email_user = user_crud.get_user_by_email(db, email=user_update.email)
        if email_user and email_user.id != user_id:
            raise HTTPException(
                status_code=400,
                detail="El email ya está en uso"
            )
    
    if user_update.username:
        username_user = user_crud.get_user_by_username(db, username=user_update.username)
        if username_user and username_user.id != user_id:
            raise HTTPException(
                status_code=400,
                detail="El username ya está en uso"
            )
    
    # Actualizar usuario
    updated_user = user_crud.update_user(db, user_id, user_update)
    return updated_user

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Elimina un usuario (solo admin)"""
    
    # No permitir que el admin se elimine a sí mismo
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=400,
            detail="No puedes eliminarte a ti mismo"
        )
    
    # Eliminar usuario
    deleted = user_crud.delete_user(db, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return {"message": "Usuario eliminado correctamente"}

@router.put("/users/{user_id}/toggle-admin")
async def toggle_admin_status(
    user_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Cambia el estado de administrador de un usuario (solo admin)"""
    
    # Obtener el usuario
    user = user_crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # No permitir que el admin se quite a sí mismo los permisos
    if user_id == current_admin.id and user.is_admin:
        raise HTTPException(
            status_code=400,
            detail="No puedes quitarte los permisos de administrador a ti mismo"
        )
    
    # Cambiar estado de admin
    user_update = UserUpdate(is_admin=not user.is_admin)
    updated_user = user_crud.update_user(db, user_id, user_update)
    
    status_message = "promovido a" if updated_user.is_admin else "removido de"
    return {
        "message": f"Usuario {status_message} administrador correctamente",
        "user": updated_user
    }