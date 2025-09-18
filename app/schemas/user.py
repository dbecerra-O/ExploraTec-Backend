from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# Schema base para User
class UserBase(BaseModel):
    email: EmailStr
    username: str
    is_active: bool = True

# Schema para crear usuario
class UserCreate(UserBase):
    password: str

# Schema para actualizar usuario
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    current_scene_id: Optional[int] = None

# Schema para respuesta de usuario (sin password)
class User(UserBase):
    id: int
    is_admin: bool
    current_scene_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Schema para login
class UserLogin(BaseModel):
    username: str  # Puede ser username o email
    password: str

# Schema para usuario en token
class UserInToken(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool
    current_scene_id: Optional[int] = None