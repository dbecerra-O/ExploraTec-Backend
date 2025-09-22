from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional, List
from app.models.chat import Conversation, Message, MessageFeedback
from app.models.scene import Scene
from app.schemas.chat import (
    ConversationCreate, ConversationUpdate, MessageCreate, 
    MessageFeedbackCreate, MessageFeedbackUpdate, ChatStats
)

class ConversationCRUD:
    def get_conversation(self, db: Session, conversation_id: int) -> Optional[Conversation]:
        """Obtiene una conversación por ID"""
        return db.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    def get_user_conversations(self, db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """Obtiene las conversaciones de un usuario"""
        return db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).order_by(desc(Conversation.updated_at)).offset(skip).limit(limit).all()
    
    def get_active_conversation(self, db: Session, user_id: int) -> Optional[Conversation]:
        """Obtiene la conversación activa más reciente de un usuario"""
        return db.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.is_active == True
        ).order_by(desc(Conversation.updated_at)).first()
    
    def create_conversation(self, db: Session, conversation: ConversationCreate, user_id: int) -> Conversation:
        """Crea una nueva conversación"""
        db_conversation = Conversation(
            user_id=user_id,
            title=conversation.title,
            scene_id=conversation.scene_id,
            is_active=conversation.is_active
        )
        db.add(db_conversation)
        db.commit()
        db.refresh(db_conversation)
        return db_conversation
    
    def update_conversation(self, db: Session, conversation_id: int, conversation_update: ConversationUpdate) -> Optional[Conversation]:
        """Actualiza una conversación"""
        db_conversation = self.get_conversation(db, conversation_id)
        if not db_conversation:
            return None
        
        update_data = conversation_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_conversation, field, value)
        
        db.commit()
        db.refresh(db_conversation)
        return db_conversation
    
    def delete_conversation(self, db: Session, conversation_id: int) -> bool:
        """Elimina una conversación"""
        db_conversation = self.get_conversation(db, conversation_id)
        if not db_conversation:
            return False
        
        db.delete(db_conversation)
        db.commit()
        return True

class MessageCRUD:
    def get_message(self, db: Session, message_id: int) -> Optional[Message]:
        """Obtiene un mensaje por ID"""
        return db.query(Message).filter(Message.id == message_id).first()
    
    def get_conversation_messages(self, db: Session, conversation_id: int, skip: int = 0, limit: int = 100) -> List[Message]:
        """Obtiene los mensajes de una conversación"""
        return db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at).offset(skip).limit(limit).all()
    
    def create_message(self, db: Session, message: MessageCreate, conversation_id: int, is_from_user: bool, tokens_used: Optional[int] = None) -> Message:
        """Crea un nuevo mensaje"""
        db_message = Message(
            conversation_id=conversation_id,
            content=message.content,
            is_from_user=is_from_user,
            scene_context_id=message.scene_context_id,
            tokens_used=tokens_used
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        return db_message
    
    def create_user_message(self, db: Session, content: str, conversation_id: int, scene_context_id: Optional[int] = None) -> Message:
        """Crea un mensaje de usuario"""
        message_data = MessageCreate(content=content, scene_context_id=scene_context_id)
        return self.create_message(db, message_data, conversation_id, True)  # True = es del usuario
    
    def create_assistant_message(self, db: Session, content: str, conversation_id: int, scene_context_id: Optional[int] = None, tokens_used: Optional[int] = None) -> Message:
        """Crea un mensaje del asistente"""
        message_data = MessageCreate(content=content, scene_context_id=scene_context_id)
        return self.create_message(db, message_data, conversation_id, False, tokens_used)  # False = es del asistente

class MessageFeedbackCRUD:
    def get_message_feedback(self, db: Session, message_id: int) -> Optional[MessageFeedback]:
        """Obtiene el feedback de un mensaje"""
        return db.query(MessageFeedback).filter(MessageFeedback.message_id == message_id).first()
    
    def create_feedback(self, db: Session, feedback: MessageFeedbackCreate, message_id: int, user_id: int) -> MessageFeedback:
        """Crea feedback para un mensaje"""
        
        # Verificar si ya existe feedback para este mensaje
        existing_feedback = self.get_message_feedback(db, message_id)
        if existing_feedback:
            # Actualizar feedback existente
            return self.update_feedback(db, message_id, MessageFeedbackUpdate(
                is_positive=feedback.is_positive,
                comment=feedback.comment
            ))
        
        db_feedback = MessageFeedback(
            message_id=message_id,
            user_id=user_id,
            is_positive=feedback.is_positive,
            comment=feedback.comment
        )
        db.add(db_feedback)
        db.commit()
        db.refresh(db_feedback)
        return db_feedback
    
    def update_feedback(self, db: Session, message_id: int, feedback_update: MessageFeedbackUpdate) -> Optional[MessageFeedback]:
        """Actualiza el feedback de un mensaje"""
        db_feedback = self.get_message_feedback(db, message_id)
        if not db_feedback:
            return None
        
        update_data = feedback_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_feedback, field, value)
        
        db.commit()
        db.refresh(db_feedback)
        return db_feedback
    
    def delete_feedback(self, db: Session, message_id: int) -> bool:
        """Elimina el feedback de un mensaje"""
        db_feedback = self.get_message_feedback(db, message_id)
        if not db_feedback:
            return False
        
        db.delete(db_feedback)
        db.commit()
        return True

class ChatStatsCRUD:
    def get_chat_stats(self, db: Session) -> ChatStats:
        """Obtiene estadísticas generales del chat"""
        
        # Estadísticas básicas
        total_conversations = db.query(Conversation).count()
        total_messages = db.query(Message).count()
        active_conversations = db.query(Conversation).filter(Conversation.is_active == True).count()
        total_feedbacks = db.query(MessageFeedback).count()
        positive_feedbacks = db.query(MessageFeedback).filter(MessageFeedback.is_positive == True).count()
        negative_feedbacks = db.query(MessageFeedback).filter(MessageFeedback.is_positive == False).count()
        
        # Escenas más activas (donde se envían más mensajes)
        most_active_scenes = db.query(
            Scene.name,
            func.count(Message.id).label('message_count')
        ).join(
            Message, Message.scene_context_id == Scene.id
        ).group_by(
            Scene.id, Scene.name
        ).order_by(
            func.count(Message.id).desc()
        ).limit(5).all()
        
        most_active_scenes_list = [
            {"scene_name": scene_name, "message_count": count} 
            for scene_name, count in most_active_scenes
        ]
        
        return ChatStats(
            total_conversations=total_conversations,
            total_messages=total_messages,
            active_conversations=active_conversations,
            total_feedbacks=total_feedbacks,
            positive_feedbacks=positive_feedbacks,
            negative_feedbacks=negative_feedbacks,
            most_active_scenes=most_active_scenes_list
        )

# Instancias de los CRUD
conversation_crud = ConversationCRUD()
message_crud = MessageCRUD()
feedback_crud = MessageFeedbackCRUD()
stats_crud = ChatStatsCRUD()