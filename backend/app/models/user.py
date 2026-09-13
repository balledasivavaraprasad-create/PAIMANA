from typing import Optional
from pydantic import BaseModel, EmailStr
from enum import Enum
from datetime import datetime

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    MO_SPI_ANALYST = "MO_SPI_ANALYST"
    MINISTRY_OFFICIAL = "MINISTRY_OFFICIAL"
    PROJECT_OFFICER = "PROJECT_OFFICER"
    VIEWER = "VIEWER"

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.PROJECT_OFFICER
    ministry: Optional[str] = None
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    hashed_password: str
    created_at: datetime = datetime.utcnow()

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    username: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None
