from pydantic import BaseModel, field_validator, EmailStr
from typing import Optional
from datetime import datetime

class User(BaseModel):
    id: str
    username: Optional[str] = None
    student_id: Optional[str] = None
    email: str
    hashed_password: str
    created_at: datetime

class UserCreate(BaseModel):
    username: Optional[str] = None
    student_id: Optional[str] = None
    email: EmailStr
    password: str

    
    @field_validator('password')
    def password_must_be_strong(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class UserLogin(BaseModel):
    login_id: str  # 可以是username或student_id
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str