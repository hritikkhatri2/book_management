from typing import Generator
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from jose import JWTError
from sqlalchemy.orm import Session
from google.oauth2 import id_token
from google.auth.transport import requests

from app.core.config import settings
from app.crud.crud_user import user as crud_user
from app.db.session import SessionLocal
from app.schemas.user import User as UserSchema, UserCreate
from app.db.models.user import User as UserModel
from app.core.roles import UserRole

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

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

def get_current_user_model(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> UserModel:
    logger.info("Starting user authentication process")
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        logger.info("Attempting to verify Google token")
        idinfo = id_token.verify_oauth2_token(
            token, requests.Request(), settings.GOOGLE_CLIENT_ID
        )
        
        if idinfo["iss"] not in [
            "accounts.google.com",
            "https://accounts.google.com",
        ]:
            logger.error(f"Invalid token issuer: {idinfo.get('iss')}")
            raise credentials_exception
            
        google_id = idinfo["sub"]
        email = idinfo["email"]
        logger.info(f"Successfully verified Google token for email: {email}")
        
    except JWTError as e:
        logger.error(f"JWT Error: {str(e)}")
        raise credentials_exception
    except ValueError as e:
        logger.error(f"Token verification error: {str(e)}")
        raise credentials_exception
        
    logger.info(f"Looking up user with Google ID: {google_id}")
    db_user = crud_user.get_by_google_id(db, google_id=google_id)
    
    if not db_user:
        logger.info(f"User not found, creating new user with email: {email}")
        try:
            user_in_create = UserCreate(
                email=email,
                full_name=idinfo.get("name"),
                google_id=google_id,
                role=UserRole.CUSTOMER,  # Explicitly set default role
                is_active=True
            )
            logger.info(f"Created UserCreate object: {user_in_create.model_dump()}")
            
            db_user = crud_user.create(db, obj_in=user_in_create)
            logger.info(f"Successfully created new user with ID: {db_user.id}")
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create user: {str(e)}"
            )
    else:
        logger.info(f"Found existing user with ID: {db_user.id}")
    
    return db_user

def get_current_active_user(
    current_user_db: UserModel = Depends(get_current_user_model),
) -> UserModel:
    if not crud_user.is_active(current_user_db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user_db

def get_current_active_superuser(
    current_user: UserModel = Depends(get_current_active_user),
) -> UserModel:
    if current_user.role != UserRole.SUPERUSER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="The user doesn\'t have enough privileges"
        )
    return current_user

def get_current_active_librarian_or_superuser(
    current_user: UserModel = Depends(get_current_active_user),
) -> UserModel:
    if current_user.role not in [UserRole.LIBRARIAN, UserRole.SUPERUSER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="The user doesn\'t have librarian or superuser privileges"
        )
    return current_user

def get_current_user_schema(
    current_user_db: UserModel = Depends(get_current_active_user),
) -> UserSchema:
    return UserSchema.from_orm(current_user_db) 