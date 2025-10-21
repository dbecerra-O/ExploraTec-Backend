from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.knowledge import Event
from app.schemas.event import EventCreate, EventUpdate
from app.services.embeddings import embed_text


class EventCRUD:
    
    def create_event(self, db: Session, event: EventCreate) -> Event:
        """Crear evento y vectorizar título + descripción"""
        text_to_embed = f"{event.title}. {event.description or ''}"
        
        db_event = Event(
            title=event.title,
            description=event.description,
            event_date=event.event_date,
            location=event.location,
            scene_id=event.scene_id,
            is_active=True
        )
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        
        try:
            emb = embed_text(text_to_embed)
            db_event.embedding = emb
            db.commit()
            db.refresh(db_event)
        except Exception as e:
            print(f"⚠️ Error generando embedding: {e}")
            db.rollback()
        
        return db_event
    
    def get_event(self, db: Session, event_id: int) -> Optional[Event]:
        """Obtener evento por ID"""
        return db.query(Event).filter(Event.id == event_id).first()
    
    def get_all_events(self, db: Session, skip: int = 0, limit: int = 50) -> List[Event]:
        """Obtener todos los eventos activos"""
        return db.query(Event).filter(
            Event.is_active == True
        ).order_by(Event.event_date).offset(skip).limit(limit).all()
    
    def get_events_by_scene(self, db: Session, scene_id: int) -> List[Event]:
        """Obtener eventos de una escena"""
        return db.query(Event).filter(
            Event.scene_id == scene_id,
            Event.is_active == True
        ).order_by(Event.event_date).all()
    
    def update_event(self, db: Session, event_id: int, event_update: EventUpdate) -> Optional[Event]:
        """Actualizar evento y re-vectorizar si cambia título/descripción"""
        db_event = self.get_event(db, event_id)
        if not db_event:
            return None
        
        update_data = event_update.model_dump(exclude_unset=True)
        needs_reembed = 'title' in update_data or 'description' in update_data
        
        for field, value in update_data.items():
            setattr(db_event, field, value)
        
        if needs_reembed:
            try:
                text_to_embed = f"{db_event.title}. {db_event.description or ''}"
                emb = embed_text(text_to_embed[:8000])
                db_event.embedding = emb
            except Exception as e:
                print(f"⚠️ Error re-generando embedding: {e}")
        
        db.commit()
        db.refresh(db_event)
        return db_event
    
    def delete_event(self, db: Session, event_id: int) -> bool:
        """Soft delete de evento"""
        db_event = self.get_event(db, event_id)
        if not db_event:
            return False
        
        db_event.is_active = False
        db.commit()
        return True


event_crud = EventCRUD()