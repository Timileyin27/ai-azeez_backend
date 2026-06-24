from jose import JWTError, jwt
from datetime import datetime, timedelta
import app.models.users
import app.schemas, app.database, app.models
from fastapi import Depends, HTTPException, status,Cookie
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.config import settings
import app.schemas.auth

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
def verify_access_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # print("PAYLOAD =", payload)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = app.schemas.auth.TokenData(id=user_id)
    except JWTError:
        raise credentials_exception
    return token_data 
def get_current_user(access_token: str = Depends(oauth2_scheme), db: Session = Depends(app.database.get_db)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"},)
    access_token = verify_access_token(access_token, credentials_exception)
    # print("TOKEN ID =", access_token.id)
    user = db.query(app.models.users.User).filter(app.models.users.User.id == access_token.id).first()
    # print("USER =", user)
    if user is None:
        raise credentials_exception

    return user