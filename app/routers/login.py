import logging
from datetime import datetime, timedelta, timezone
 
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
 
import app.models.users
import app.oauth2
import app.schemas.auth
import app.utils.otp_code
import app.utils.rate_limit
from app.database import get_db
from app.utils.email import send_otp_email, send_welcome_email
 
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth/login", tags=["Authentication"])
 
OTP_LIFETIME_MINUTES = 5
 
 
# Plain `def` (not `async def`): the database and email calls are blocking, so
# FastAPI runs the function in a worker thread instead of freezing the event loop.
@router.post("/send_OTP")
def send_otp(
    payload: app.schemas.auth.createOTP,
    request: Request,
    db: Session = Depends(get_db),
):
    # Rate limit FIRST, before any database work, so blocked requests are cheap
    # and the limiter behaves the same whether or not the account exists.
    app.utils.rate_limit.check_send_otp(request, payload.email)
 
    user = (
        db.query(app.models.users.User.id)
        .filter(app.models.users.User.email == payload.email)
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
 
    otp = app.utils.otp_code.create_otp()
 
    # Invalidate any earlier unused codes for this email.
    db.query(app.models.users.OTP).filter(
        app.models.users.OTP.email == payload.email,
        app.models.users.OTP.used == False,  # noqa: E712
    ).update({"used": True})
 
    otp_record = app.models.users.OTP(
        email=payload.email,
        otp_code=otp,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=OTP_LIFETIME_MINUTES),
    )
    db.add(otp_record)
    db.commit()
 
    try:
        send_otp_email(payload.email, otp)
    except Exception:
        logger.exception("OTP email failed")
        # Don't leave a valid code behind that the user never received.
        otp_record.used = True
        db.commit()
        raise HTTPException(
            status_code=503,
            detail="Could not send the verification email. Please try again.",
        )
 
    return {"message": "OTP sent successfully"}
 
 
@router.post("/verify_OTP")
def verify_otp(
    payload: app.schemas.auth.verifyOTP,
    request: Request,
    db: Session = Depends(get_db),
):
    # Counts every attempt: this is what stops brute-forcing the 6-digit code.
    app.utils.rate_limit.check_verify_otp(request, payload.email)
 
    otp_record = (
        db.query(app.models.users.OTP)
        .filter(
            app.models.users.OTP.email == payload.email,
            app.models.users.OTP.used == False,  # noqa: E712
        )
        .order_by(app.models.users.OTP.id.desc())
        .first()
    )
    if not otp_record:
        raise HTTPException(status_code=404, detail="OTP not found")
    if not app.utils.otp_code.verify_otp(payload.otp_code, otp_record.otp_code):
        raise HTTPException(status_code=400, detail="Invalid OTP")
    if otp_record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="OTP expired")
 
    user = (
        db.query(app.models.users.User)
        .filter(app.models.users.User.email == payload.email)
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
 
    otp_record.used = True
    db.commit()
    app.utils.rate_limit.clear_verify_otp(payload.email)  # legitimate user starts fresh
 
    # A failed welcome email must not break a successful login.
    try:
        send_welcome_email(payload.email)
    except Exception:
        logger.warning("Welcome email failed", exc_info=True)
 
    access_token = app.oauth2.create_access_token({"sub": str(user.id)})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }
 