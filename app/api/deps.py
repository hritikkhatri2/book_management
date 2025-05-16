from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from jose import JWTError
from sqlalchemy.orm import Session
from google.oauth2 import id_token
from google.auth.transport import requests

from app.core.config import settings
from app.crud.crud_user import user
from app.db.session import SessionLocal
from app.schemas.user import User

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://accounts.google.com/o/oauth2/v2/auth",
    tokenUrl="https://oauth2.googleapis.com/token",
)

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        idinfo = id_token.verify_oauth2_token(
            token, requests.Request(), settings.GOOGLE_CLIENT_ID
        )
        
        if idinfo["iss"] not in [
            "accounts.google.com",
            "https://accounts.google.com",
        ]:
            raise credentials_exception
            
        google_id = idinfo["sub"]
        email = idinfo["email"]
        
    except JWTError:
        raise credentials_exception
        
    db_user = user.get_by_google_id(db, google_id=google_id)
    if not db_user:
        from app.schemas.user import UserCreate
        user_in = UserCreate(
            email=email,
            full_name=idinfo.get("name"),
            google_id=google_id,
        )
        db_user = user.create(db, obj_in=user_in)
    return db_user

def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not user.is_active(current_user):
        raise HTTPException(
            status_code=400, detail="Inactive user"
        )
    return current_user 