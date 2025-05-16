from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging # Added for logging

from app.api.routes import books, auth, search, users # Added users router
from app.core.config import settings
from app.db.session import SessionLocal # For startup event
from app.services.search_service import search_service # For startup event

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.on_event("startup")
def on_startup():
    logger.info("Application startup: Building FAISS index...")
    db = SessionLocal()
    try:
        search_service.build_index(db)
        logger.info("FAISS index built successfully on startup.")
    except Exception as e:
        logger.error(f"Error building FAISS index on startup: {e}", exc_info=True)
    finally:
        db.close()

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"]) # Added users router
app.include_router(books.router, prefix=f"{settings.API_V1_STR}/books", tags=["books"])
app.include_router(search.router, prefix=f"{settings.API_V1_STR}/search", tags=["search"])

@app.get("/")
def root():
    return {"message": "Welcome to Book Management System API"} 