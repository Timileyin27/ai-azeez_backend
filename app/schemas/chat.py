from pydantic import BaseModel,EmailStr, Field,model_validator
from uuid import UUID
from datetime import datetime
from typing import Optional,List
from app.models.chat import MessageRole
class conversationIN(BaseModel):
    title: str
class conversationOUT(BaseModel):
    id: UUID
    title: str
    model_config= {
        "from_attributes": True
    }
class messageIN(BaseModel):
    role: MessageRole
    content: str
class messageOUT(BaseModel):
    id: UUID
    conversation_id: UUID
    role: MessageRole
    content: str
    model_config= {
        "from_attributes": True
    }