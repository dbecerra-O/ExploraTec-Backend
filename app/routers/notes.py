from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.dependencies import get_current_active_user, get_current_admin_user
from app.models.user import User
from app.schemas.note import NoteCreate, NoteResponse, NoteUpdate, NoteStats
from app.crud.note import note_crud

router = APIRouter(prefix="/notes", tags=["Notes"])

@router.post("/", response_model=NoteResponse)
def create_note(
    note: NoteCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Crear nueva nota/cita"""
    return note_crud.create_note(db, note, current_user.id)


@router.get("/my-notes", response_model=List[NoteResponse])
def get_my_notes(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener mis notas/citas"""
    return note_crud.get_user_notes(db, current_user.id, skip, limit)


@router.get("/{note_id}", response_model=NoteResponse)
def get_note(
    note_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener nota específica"""
    note = note_crud.get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Nota no encontrada")
    
    # Verificar que sea del usuario
    if note.User_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes acceso a esta nota")
    
    return note

@router.get("/admin/all", response_model=List[NoteResponse])
def get_all_notes(
    skip: int = 0,
    limit: int = 100,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Obtener todas las notas (admin)"""
    return note_crud.get_all_notes(db, skip, limit)


@router.patch("/admin/{note_id}", response_model=NoteResponse)
def update_note(
    note_id: int,
    note_update: NoteUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Actualizar nota (admin)"""
    updated = note_crud.update_note(db, note_id, note_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Nota no encontrada")
    return updated


@router.get("/admin/stats", response_model=NoteStats)
def get_notes_stats(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Obtener estadísticas de notas (admin)"""
    return note_crud.get_stats(db)

@router.get("/admin/today", response_model=List[NoteResponse])
def get_today_appointments(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Obtener citas programadas para hoy (admin)"""
    return note_crud.get_today_notes(db)