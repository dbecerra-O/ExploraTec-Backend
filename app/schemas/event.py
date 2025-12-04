from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    event_date: datetime
    location: Optional[str] = None
    scene_id: Optional[int] = None
    modalidad: Optional[str] = None
    link: Optional[str] = None


class EventResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    event_date: datetime
    location: Optional[str]
    scene_id: Optional[int]
    modalidad: Optional[str]
    link: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    event_date: Optional[datetime] = None
    location: Optional[str] = None
    scene_id: Optional[int] = None
    modalidad: Optional[str] = None
    link: Optional[str] = None
    is_active: Optional[bool] = None