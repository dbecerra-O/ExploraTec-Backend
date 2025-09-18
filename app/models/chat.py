from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=True)  # Título generado automáticamente o definido por el usuario
    scene_id = Column(Integer, ForeignKey("scenes.id"), nullable=True)  # Escena donde se inició la conversación
    is_active = Column(Boolean, default=True)  # Si la conversación está activa
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    user = relationship("User", back_populates="conversations")
    scene = relationship("Scene")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, user_id={self.user_id}, title='{self.title}')>"

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    content = Column(Text, nullable=False)
    is_from_user = Column(Boolean, nullable=False, default=True)  # True = usuario, False = asistente
    scene_context_id = Column(Integer, ForeignKey("scenes.id"), nullable=True)  # Escena donde se envió el mensaje
    tokens_used = Column(Integer, nullable=True)  # Para tracking de uso de API
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    conversation = relationship("Conversation", back_populates="messages")
    scene_context = relationship("Scene")
    feedback = relationship("MessageFeedback", back_populates="message", uselist=False)
    
    def __repr__(self):
        msg_type = "user" if self.is_from_user else "assistant"
        return f"<Message(id={self.id}, type={msg_type}, conversation_id={self.conversation_id})>"

class MessageFeedback(Base):
    __tablename__ = "message_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_positive = Column(Boolean, nullable=False)  # True = like, False = dislike
    comment = Column(Text, nullable=True)  # Comentario opcional del usuario
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    message = relationship("Message", back_populates="feedback")
    user = relationship("User")
    
    def __repr__(self):
        feedback_type = "like" if self.is_positive else "dislike"
        return f"<MessageFeedback(id={self.id}, message_id={self.message_id}, type={feedback_type})>"