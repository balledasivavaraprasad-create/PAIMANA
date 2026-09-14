from typing import Optional
from pydantic import BaseModel, EmailStr
from enum import Enum
from datetime import datetime, timezone

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
    designation: Optional[str] = None
    is_active: bool = True
    is_verified: bool = True
    dphis_alert_threshold: float = 75.0
    alert_email: Optional[EmailStr] = None
    notify_via_email: bool = True

class UserPreferencesUpdate(BaseModel):
    dphis_alert_threshold: Optional[float] = 75.0
    alert_email: Optional[EmailStr] = None
    notify_via_email: Optional[bool] = True

class UserCreate(UserBase):
    password: str

class UserRegisterRequest(BaseModel):
    fullName: str
    email: EmailStr
    ministry: Optional[str] = None
    ministryId: Optional[int] = None
    designation: Optional[str] = None
    password: str
    termsAccepted: bool = False
    aiAckAccepted: bool = False

class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str

class ResendOtpRequest(BaseModel):
    email: EmailStr
    purpose: str = "signup"

class LoginJsonRequest(BaseModel):
    email: str
    password: str

class MinistryItem(BaseModel):
    id: int
    name: str
    sector: str

class UserInDB(UserBase):
    hashed_password: str
    created_at: datetime = datetime.now(timezone.utc)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    ministry: Optional[str] = None

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None
