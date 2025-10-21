from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from app.models.note import Note , Speciality
from app.schemas.note import NoteCreate, NoteUpdate
from datetime import date


class NoteCRUD:
    
    def create_note(self, db: Session, note: NoteCreate, user_id: int) -> Note:
        """Crear nueva nota/cita"""
        db_note = Note(
            name=note.name,
            lastname=note.lastname,
            dni=note.dni,
            phone=note.phone,
            reason=note.reason,
            visit_date=note.visit_date,
            Speciality_id=note.speciality_id,
            User_id=user_id,
            family_dni=note.family_dni,
            family_lastname=note.family_lastname,
            family_name=note.family_name,
            gender=note.gender,
            is_accepted=False
        )
        db.add(db_note)
        db.commit()
        db.refresh(db_note)
        return db_note
    
    def get_note(self, db: Session, note_id: int) -> Optional[Note]:
        """Obtener nota por ID"""
        return db.query(Note).filter(Note.id == note_id).first()
    
    def get_user_notes(self, db: Session, user_id: int, skip: int = 0, limit: int = 50) -> List[Note]:
        """Obtener notas de un usuario"""
        return db.query(Note).filter(
            Note.User_id == user_id
        ).order_by(desc(Note.created_at)).offset(skip).limit(limit).all()
    
    def get_all_notes(self, db: Session, skip: int = 0, limit: int = 100) -> List[Note]:
        """Obtener todas las notas (admin)"""
        return db.query(Note).order_by(desc(Note.created_at)).offset(skip).limit(limit).all()
    
    def update_note(self, db: Session, note_id: int, note_update: NoteUpdate) -> Optional[Note]:
        """Actualizar nota (admin)"""
        db_note = self.get_note(db, note_id)
        if not db_note:
            return None
        
        update_data = note_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_note, field, value)
        
        db.commit()
        db.refresh(db_note)
        return db_note
    
    def get_stats(self, db: Session) -> dict:
        """Obtener estadísticas (admin)"""
        total = db.query(Note).count()
        pending = db.query(Note).filter(Note.is_accepted == False).count()
        accepted = db.query(Note).filter(Note.is_accepted == True).count()
        
        # Notas por especialidad
        by_speciality = db.query(
            Speciality.name,
            func.count(Note.id).label('count')
        ).join(Note).group_by(Speciality.name).all()
        
        # Notas recientes
        recent = db.query(Note).order_by(desc(Note.created_at)).limit(5).all()
        
        return {
            "total_notes": total,
            "pending_notes": pending,
            "accepted_notes": accepted,
            "rejected_notes": total - accepted - pending,
            "notes_by_speciality": {s.name: s.count for s in by_speciality},
            "recent_notes": [
                {
                    "id": n.id,
                    "name": f"{n.name} {n.lastname}",
                    "speciality_id": n.Speciality_id,
                    "is_accepted": n.is_accepted,
                    "created_at": n.created_at
                }
                for n in recent
            ]
        }
    
    def get_today_notes(self, db: Session) -> List[Note]:
        """Obtener citas programadas para hoy"""
        today = date.today()
        return db.query(Note).filter(
            func.date(Note.visit_date) == today,
            Note.is_accepted == True
        ).order_by(Note.visit_date).all()


note_crud = NoteCRUD()