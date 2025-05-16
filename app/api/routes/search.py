from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api import deps
from app.services.search_service import search_service
from app.schemas.user import User
from app.schemas.book import BookSearchResultItem

router = APIRouter()

@router.get("/semantic/{query}", response_model=List[BookSearchResultItem])
def semantic_search(
    *,
    query: str,
    k: int = 5,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> List[BookSearchResultItem]:
    """
    Perform semantic search on books using FAISS and OpenAI embeddings.
    """
    return search_service.semantic_search(db, query, k) 