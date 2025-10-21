from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class NoteCreate(BaseModel):
    name: str
    lastname: str
    dni: str
    phone: Optional[str]
    reason: Optional[str]
    visit_date: Optional[datetime]
    speciality_id: int
    # Datos del familiar (opcional)
    family_dni: Optional[str]
    family_lastname: Optional[str]
    family_name: Optional[str]
    gender: Optional[str]


class NoteResponse(BaseModel):
    id: int
    name: str
    lastname: str
    dni: str
    phone: Optional[str]
    reason: Optional[str]
    is_accepted: bool
    created_at: datetime
    visit_date: Optional[datetime]
    speciality_id: int
    user_id: int
    
    class Config:
        from_attributes = True


class NoteUpdate(BaseModel):
    is_accepted: Optional[bool]
    visit_date: Optional[datetime]
    reason: Optional[str]


class NoteStats(BaseModel):
    total_notes: int
    pending_notes: int
    accepted_notes: int
    rejected_notes: int
    notes_by_speciality: dict
    recent_notes: list