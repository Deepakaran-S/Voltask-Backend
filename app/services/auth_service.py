import random
import string
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password, create_access_token
from app.models.company import Company
from app.models.otp import OTPRecord
from app.models.user import User, UserRole
from app.schemas.auth import RegisterRequest

OTP_EXPIRE_MINUTES = 5


def _invalidate_otps(db: Session, user_id: int, purpose: str) -> None:
    db.query(OTPRecord).filter(
        OTPRecord.user_id == user_id,
        OTPRecord.purpose == purpose,
        OTPRecord.is_used == False,
    ).update({"is_used": True})


def _create_otp(db: Session, user_id: int, purpose: str) -> str:
    _invalidate_otps(db, user_id, purpose)
    otp_code = "".join(random.choices(string.digits, k=6))
    record = OTPRecord(user_id=user_id, otp=otp_code, purpose=purpose)
    db.add(record)
    db.commit()
    return otp_code


def _verify_otp(db: Session, user_id: int, otp_code: str, purpose: str) -> OTPRecord:
    expiry_cutoff = datetime.utcnow() - timedelta(minutes=OTP_EXPIRE_MINUTES)
    record = (
        db.query(OTPRecord)
        .filter(
            OTPRecord.user_id == user_id,
            OTPRecord.otp == otp_code,
            OTPRecord.purpose == purpose,
            OTPRecord.is_used == False,
            OTPRecord.created_at >= expiry_cutoff,
        )
        .first()
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid, expired, or already used OTP",
        )
    record.is_used = True
    db.commit()
    return record


async def register_company_and_admin(db: Session, data: RegisterRequest) -> None:
    company = Company(name=data.company_name)
    db.add(company)
    db.flush()

    user = User(
        name=data.name,
        email=data.email,
        password=hash_password(data.password),
        role=UserRole.admin,
        company_id=company.id,
        is_active=False,
    )
    db.add(user)
    db.flush()

    otp_code = _create_otp(db, user.id, "email_verification")
    db.commit()

    from app.core.email import send_otp_email
    await send_otp_email(
        email_to=data.email,
        otp=otp_code,
        subject="Verify your TaskSphere account",
        heading="Welcome to TaskSphere!",
        body_line="Please verify your email address using the OTP below:",
    )


def verify_email_otp(db: Session, email: str, otp_code: str) -> None:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP or email")

    _verify_otp(db, user.id, otp_code, "email_verification")

    user.is_active = True
    db.commit()


async def initiate_login(db: Session, email: str, password: str) -> None:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not verified. Please verify your email first.",
        )

    otp_code = _create_otp(db, user.id, "login")

    from app.core.email import send_otp_email
    await send_otp_email(
        email_to=user.email,
        otp=otp_code,
        subject="Your TaskSphere Login OTP",
        heading="Login Verification",
        body_line="Use the OTP below to complete your login:",
    )


def verify_login_otp(db: Session, email: str, otp_code: str) -> dict:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP or email")

    _verify_otp(db, user.id, otp_code, "login")

    token = create_access_token(data={
        "sub": str(user.id),
        "company_id": user.company_id,
        "role": user.role.value,
    })
    return {
        "access_token": token,
        "token_type": "bearer",
        "must_change_password": user.must_change_password,
    }


async def generate_otp(db: Session, email: str) -> None:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return  # silent — prevent user enumeration

    otp_code = _create_otp(db, user.id, "password_reset")

    from app.core.email import send_otp_email
    await send_otp_email(
        email_to=user.email,
        otp=otp_code,
        subject="Your TaskSphere Password Reset OTP",
        heading="Password Reset",
        body_line="Use the OTP below to reset your password:",
    )


def reset_password_with_token(db: Session, reset_token: str, new_password: str) -> None:
    from app.core.security import decode_access_token
    payload = decode_access_token(reset_token)
    
    if not payload or payload.get("type") != "pw_reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    user.password = hash_password(new_password)
    db.commit()


def verify_reset_otp_and_get_token(db: Session, email: str, otp_code: str) -> str:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP or email")

    _verify_otp(db, user.id, otp_code, "password_reset")

    # Generate a short-lived reset token (15 mins)
    return create_access_token(
        data={"sub": str(user.id), "type": "pw_reset"},
        expires_delta=timedelta(minutes=15)
    )


def change_password(db: Session, user: User, old_password: str, new_password: str) -> None:
    if not verify_password(old_password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password is incorrect",
        )
    user.password = hash_password(new_password)
    user.must_change_password = False
    db.commit()
