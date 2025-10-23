from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Schema para MessageFeedback
class MessageFeedbackBase(BaseModel):
    is_positive: bool  # True = like, False = dislike

class MessageFeedbackCreate(MessageFeedbackBase):
    pass

class MessageFeedbackUpdate(BaseModel):
    is_positive: Optional[bool] = None

class MessageFeedback(MessageFeedbackBase):
    id: int
    message_id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Schema para Message
class MessageBase(BaseModel):
    content: str
    is_from_user: bool
    scene_context: Optional[str] = None

class MessageCreate(BaseModel):
    content: str
    scene_context: Optional[str] = None

class MessageUpdate(BaseModel):
    content: Optional[str] = None

class Message(MessageBase):
    id: int
    conversation_id: int
    tokens_used: Optional[int] = None
    created_at: datetime
    feedback: Optional[MessageFeedback] = None
    intent_category: Optional[str] = None
    intent_confidence: Optional[float] = None
    intent_keywords: Optional[List[str]] = None
    requires_clarification: Optional[bool] = None

    class Config:
        from_attributes = True

# Schema para Conversation
class ConversationBase(BaseModel):
    title: Optional[str] = None
    scene_id: Optional[int] = None
    is_active: bool = True

class ConversationCreate(ConversationBase):
    pass

class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    is_active: Optional[bool] = None

class ConversationSimple(ConversationBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    message_count: Optional[int] = None

    class Config:
        from_attributes = True

class Conversation(ConversationBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    messages: List[Message] = []

    class Config:
        from_attributes = True

# Schema para crear un mensaje nuevo (incluye lógica de conversación)
class ChatMessage(BaseModel):
    content: str
    conversation_id: Optional[int] = None  # Si es None, se crea nueva conversación
    scene_context: Optional[str] = None  # scene_key de la escena actual

class NavigationInfo(BaseModel):
    from_scene: str
    to_scene: str
    to_scene_id: Optional[int] = None
    path: List[str]
    distance: int
    steps: int
    should_navigate: bool
    already_here: bool = False
    from_scene_name: Optional[str] = None
    to_scene_name: Optional[str] = None

# Schema para la respuesta del chatbot
class ChatResponse(BaseModel):
    user_message: Message
    assistant_message: Message
    conversation: ConversationSimple
    is_new_conversation: bool = False
    navigation: Optional[NavigationInfo] = None
    response_time_ms: Optional[int] = None
    
class IntentStats(BaseModel):
    category: str
    count: int
    percentage: float
    avg_confidence: float

# Schema para estadísticas del chatbot
class ChatStats(BaseModel):
    total_conversations: int
    total_messages: int
    active_conversations: int
    total_feedbacks: int
    positive_feedbacks: int
    negative_feedbacks: int
    intent_distribution: Optional[List[IntentStats]] = []