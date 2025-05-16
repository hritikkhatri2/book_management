from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2AuthorizationCodeBearer
from sqlalchemy.orm import Session
from app.api import deps
from app.core.config import settings
from app.schemas.user import User

router = APIRouter()

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://accounts.google.com/o/oauth2/v2/auth",
    tokenUrl="https://oauth2.googleapis.com/token",
)

@router.get("/login")
def login():
    """
    Google OAuth2 login endpoint.
    """
    return {
        "url": f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"response_type=code&"
        f"client_id={settings.GOOGLE_CLIENT_ID}&"
        f"redirect_uri={settings.GOOGLE_REDIRECT_URI}&"
        f"scope=openid%20email%20profile"
    }

@router.get("/callback")
def callback(
    code: str,
    db: Session = Depends(deps.get_db),
):
    """
    Google OAuth2 callback endpoint.
    """
    # The actual token exchange and user creation/login is handled in deps.py
    # This endpoint just needs to receive the code and return success
    return {"message": "Successfully authenticated"}

@router.get("/me", response_model=User)
def read_users_me(
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get current user.
    """
    return current_user 