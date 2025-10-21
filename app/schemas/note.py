from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class NoteCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    lastname: str = Field(..., min_length=2, max_length=100)
    dni: str = Field(..., min_length=8, max_length=9)
    phone: Optional[str] = Field(None, max_length=9)
    reason: Optional[str] = None
    visit_date: Optional[datetime] = None
    speciality_id: int
    
    # Datos del familiar (opcional)
    family_dni: Optional[str] = Field(None, max_length=9)
    family_lastname: Optional[str] = Field(None, max_length=100)
    family_name: Optional[str] = Field(None, max_length=100)
    gender: Optional[str] = Field(None, max_length=100)


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
    is_accepted: Optional[bool] = None
    visit_date: Optional[datetime] = None
    reason: Optional[str] = None


class NoteStats(BaseModel):
    total_notes: int
    pending_notes: int
    accepted_notes: int
    rejected_notes: int
    notes_by_speciality: dict
    recent_notes: list