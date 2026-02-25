from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.models.user import UserRole


class InviteUserRequest(BaseModel):
    name: str
    email: EmailStr
    role: UserRole


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: UserRole
    company_id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
