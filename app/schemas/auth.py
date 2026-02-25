from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.models.user import UserRole


# ── Register ──────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    company_name: str
    name: str
    email: EmailStr
    password: str


class RegisterResponse(BaseModel):
    message: str


# ── Email Verification (after register) ───────────────────────────────────────

class VerifyEmailRequest(BaseModel):
    email: EmailStr
    otp: str


# ── Login ─────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginOTPSentResponse(BaseModel):
    message: str


# ── Verify Login OTP → JWT ────────────────────────────────────────────────────

class VerifyLoginRequest(BaseModel):
    email: EmailStr
    otp: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    must_change_password: bool = False


# ── Forgot / Reset Password ───────────────────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str


class VerifyOTPResponse(BaseModel):
    reset_token: str
    message: str = "OTP verified successfully"


# ── Current User ──────────────────────────────────────────────────────────────

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class UserMeResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: UserRole
    company_id: int
    is_active: bool
    must_change_password: bool
    created_at: datetime

    class Config:
        from_attributes = True
