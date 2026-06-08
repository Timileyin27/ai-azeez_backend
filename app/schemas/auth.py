from pydantic import BaseModel,EmailStr, Field,model_validator
from datetime import datetime
from typing import Optional,List
class Token(BaseModel):
    access_token: str
    token_type: str
class TokenData(BaseModel):
    id: str
class createOTP(BaseModel):
    email: EmailStr
class verifyOTP(BaseModel):
    email: EmailStr
    otp_code: str
class UserOut (BaseModel):
    id:int
    email: EmailStr
    model_config= {
        "from_attributes": True
    }
class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserOut