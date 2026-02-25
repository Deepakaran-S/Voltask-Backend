from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    TokenResponse,
    UserMeResponse,
    VerifyEmailRequest,
    VerifyLoginRequest,
    VerifyOTPRequest,
    VerifyOTPResponse,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    await auth_service.register_company_and_admin(db, data)
    return {"message": "Registered successfully! Please check your email for the verification OTP."}


@router.post("/verify-email")
def verify_email(data: VerifyEmailRequest, db: Session = Depends(get_db)):
    auth_service.verify_email_otp(db, data.email, data.otp)
    return {"message": "Email verified successfully! You can now log in."}


@router.post("/login")
async def login(data: LoginRequest, db: Session = Depends(get_db)):
    await auth_service.initiate_login(db, data.email, data.password)
    return {"message": "OTP sent to your email. Please verify to complete login."}


@router.post("/verify-login", response_model=TokenResponse)
def verify_login(data: VerifyLoginRequest, db: Session = Depends(get_db)):
    return auth_service.verify_login_otp(db, data.email, data.otp)


@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    await auth_service.generate_otp(db, data.email)
    return {"message": "If an account with that email exists, a password reset OTP has been sent."}


@router.post("/verify-reset-otp", response_model=VerifyOTPResponse)
def verify_reset_otp(data: VerifyOTPRequest, db: Session = Depends(get_db)):
    token = auth_service.verify_reset_otp_and_get_token(db, data.email, data.otp)
    return {"reset_token": token, "message": "OTP verified! You can now reset your password."}


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    auth_service.reset_password_with_token(db, data.reset_token, data.new_password)
    return {"message": "Password reset successfully. You can now log in."}


@router.get("/me", response_model=UserMeResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/change-password")
def change_password(
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    auth_service.change_password(db, current_user, data.old_password, data.new_password)
    return {"message": "Password changed successfully."}
