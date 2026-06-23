from sqlalchemy import Column, Integer, String, TIMESTAMP,Float
from sqlalchemy.dialects.postgresql import UUID 
from app.database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import Boolean, DateTime
from sqlalchemy.sql.expression import text
from sqlalchemy import Enum as SqlEnum
from enum import Enum 
import uuid
class Conversation (Base):
    __tablename__ = "conversations"
    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False,default=uuid.uuid4)
    user_id  = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

class MessageRole(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"
class Message (Base):
    __tablename__ = "messages"
    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False,default=uuid.uuid4)
    conversation_id  = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(SqlEnum(MessageRole), nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
