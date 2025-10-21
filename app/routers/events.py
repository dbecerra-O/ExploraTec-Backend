from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.dependencies import get_current_admin_user
from app.models.user import User
from app.schemas.event import EventCreate, EventResponse, EventUpdate
from app.crud.event import event_crud

router = APIRouter(prefix="/events", tags=["Events"])


@router.post("/", response_model=EventResponse)
def create_event(
    event: EventCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Crear evento (admin)"""
    return event_crud.create_event(db, event)


@router.get("/", response_model=List[EventResponse])
def get_events(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Obtener todos los eventos"""
    return event_crud.get_all_events(db, skip, limit)


@router.get("/{event_id}", response_model=EventResponse)
def get_event(
    event_id: int,
    db: Session = Depends(get_db)
):
    """Obtener evento por ID"""
    event = event_crud.get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return event


@router.patch("/{event_id}", response_model=EventResponse)
def update_event(
    event_id: int,
    event_update: EventUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Actualizar evento (admin)"""
    updated = event_crud.update_event(db, event_id, event_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return updated


@router.delete("/{event_id}")
def delete_event(
    event_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Eliminar evento (admin)"""
    success = event_crud.delete_event(db, event_id)
    if not success:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return {"message": "Evento eliminado"}