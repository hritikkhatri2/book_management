from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2AuthorizationCodeBearer
from sqlalchemy.orm import Session
import logging
from google.oauth2 import id_token
from google.auth.transport import requests
import requests as http_requests
import json

from app.api import deps
from app.core.config import settings
from app.schemas.user import User, UserCreate
from app.crud.crud_user import user as crud_user
from app.core.security import create_access_token
from app.core.roles import UserRole

# Configure logging
logger = logging.getLogger(__name__)

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
    logger.info("Initiating Google OAuth login flow")
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id={settings.GOOGLE_CLIENT_ID}&redirect_uri={settings.GOOGLE_REDIRECT_URI}&scope=openid%20email%20profile"
    logger.info(f"Generated auth URL with redirect_uri: {settings.GOOGLE_REDIRECT_URI}")
    return {"url": auth_url}

@router.get("/callback")
async def callback(
    code: str,
    db: Session = Depends(deps.get_db),
):
    """
    Google OAuth2 callback endpoint.
    """
    logger.info("=== Starting OAuth Callback Process ===")
    logger.info(f"Received authorization code: {code[:10]}...")  # Log only first 10 chars for security
    
    try:
        # Exchange authorization code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "code": code,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        
        logger.info("Attempting to exchange authorization code for tokens...")
        token_response = http_requests.post(token_url, data=token_data)
        token_response.raise_for_status()
        token_info = token_response.json()
        logger.info("Successfully obtained tokens from Google")
        
        # Verify ID token and get user info
        logger.info("Verifying ID token...")
        idinfo = id_token.verify_oauth2_token(
            token_info["id_token"],
            requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )
        logger.info("Successfully verified ID token")
        logger.debug(f"ID token info: {json.dumps(idinfo, indent=2)}")

        if idinfo["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
            logger.error(f"Invalid token issuer: {idinfo.get('iss')}")
            raise HTTPException(status_code=400, detail="Invalid issuer")

        # Extract user info
        google_id = idinfo["sub"]
        email = idinfo["email"]
        full_name = idinfo.get("name")
        
        logger.info(f"Processing user authentication - Email: {email}, Google ID: {google_id}")

        # Get or create user
        logger.info("Checking if user exists in database...")
        db_user = crud_user.get_by_google_id(db, google_id=google_id)
        
        if not db_user:
            logger.info(f"User not found. Creating new user with email: {email}")
            try:
                user_in_create = UserCreate(
                    email=email,
                    full_name=full_name,
                    google_id=google_id,
                    role=UserRole.CUSTOMER,
                    is_active=True
                )
                logger.debug(f"UserCreate object: {user_in_create.model_dump()}")
                
                db_user = crud_user.create(db, obj_in=user_in_create)
                logger.info(f"Successfully created new user with ID: {db_user.id}")
                logger.debug(f"New user details: ID={db_user.id}, Email={db_user.email}, Role={db_user.role}")
            except Exception as e:
                logger.error(f"Error creating user: {str(e)}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")
        else:
            logger.info(f"Found existing user - ID: {db_user.id}, Email: {db_user.email}, Role: {db_user.role}")

        # Create access token
        logger.info(f"Generating access token for user ID: {db_user.id}")
        access_token = create_access_token(subject=db_user.id)
        logger.info("Successfully generated access token")

        response_data = {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": db_user.id,
                "email": db_user.email,
                "full_name": db_user.full_name,
                "role": db_user.role.value if db_user.role else None,
                "is_active": db_user.is_active
            }
        }
        logger.info("=== OAuth Callback Process Completed Successfully ===")
        return response_data

    except http_requests.RequestException as e:
        logger.error(f"Token exchange failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {str(e)}")
    except ValueError as e:
        logger.error(f"Invalid token: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@router.get("/me", response_model=User)
def read_users_me(
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get current user.
    """
    return current_user 