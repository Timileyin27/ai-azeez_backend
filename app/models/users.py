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

class User (Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False,default=uuid.uuid4)
    email  = Column(String, nullable=False, unique=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
class OTP(Base):
    __tablename__ = "otp"
    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False,default=uuid.uuid4)
    email  = Column(String, nullable=False)
    used = Column(Boolean, default=False)
    otp_code = Column(String, nullable=False)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)