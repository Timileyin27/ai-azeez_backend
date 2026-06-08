from app.database import get_db
from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy.orm import Session
from sqlalchemy import func
import app.models.users
import app.oauth2
import app.schemas.auth
import app.schemas,app.utils
import app.models
from fastapi import Request,Form,Depends
from datetime import datetime,timedelta,timezone
from app.utils.email import send_otp_email,send_welcome_email
import app.utils.otp_code

router = APIRouter(prefix="/auth/login",tags=["Authentication"])
@router.post("/send_OTP")
async def send_otp(payload:app.schemas.auth.createOTP, db: Session = Depends(get_db)):
    user=(
        db.query(app.models.users.User.id).filter(app.models.users.User.email == payload.email).first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    otp = app.utils.otp_code.create_otp()
    db.query(app.models.users.OTP).filter(
    app.models.users.OTP.email == payload.email,
    app.models.users.OTP.used == False
).update({"used": True})

    otp_record = app.models.users.OTP(

        email=payload.email,
        otp_code=otp,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5)
    )
    db.add(otp_record)
    db.commit()

    print(otp)
    send_otp_email(payload.email, otp)

    return {
        "message": "OTP sent successfully"
    }
@router.post("/verify_OTP")
async def verify_otp(payload:app.schemas.auth.verifyOTP,db:Session=Depends(get_db)):
    otp_record =  db.query(app.models.users.OTP).filter(app.models.users.OTP.email == payload.email, app.models.users.OTP.used==False).order_by(app.models.users.OTP.id.desc()).first()
    if not otp_record:
        raise HTTPException(status_code=404, detail="OTP not found")
    if not app.utils.otp_code.verify_otp(payload.otp_code, otp_record.otp_code):
        raise HTTPException(status_code=400,  detail="Invalid OTP" )
    if otp_record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(  status_code=400,detail="OTP expired")
    user =(
        db.query(app.models.users.User).filter(app.models.users.User.email == payload.email).first()
        )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    otp_record.used = True

    db.commit()
    send_welcome_email(payload.email)
    access_token = app.oauth2.create_access_token({"sub": str(user.id)})
    return {
    "access_token": access_token,
    "token_type": "bearer",
    "user": user
}