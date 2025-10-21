from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, BigInteger
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class Speciality(Base):
    __tablename__ = 'specialties'
    
    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(45), nullable=False)
    
    notes = relationship("Note", back_populates="speciality")

class Note(Base):
    __tablename__ = 'notes'
    
    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    lastname = Column(String(100), nullable=False)
    dni = Column(String(9), nullable=False)
    phone = Column(String(9))
    reason = Column(Text)
    is_accepted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    visit_date = Column(DateTime)
    family_dni = Column(String(9))
    family_lastname = Column(String(100))
    family_name = Column(String(100))
    gender = Column(String(100))
    
    # Claves foráneas
    User_id = Column(Integer, ForeignKey('user.id'))
    Speciality_id = Column(BigInteger, ForeignKey('speciality.id'))
    
    # Relaciones
    user = relationship("User", back_populates="notes")
    speciality = relationship("Speciality", back_populates="notes")