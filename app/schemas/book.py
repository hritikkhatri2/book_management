from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class BookBase(BaseModel):
    title: str
    author: str
    isbn: str
    description: Optional[str] = None
    publication_year: Optional[int] = None
    publisher: Optional[str] = None


class BookCreate(BookBase):
    pass


class BookUpdate(BookBase):
    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None


class BookCheckout(BaseModel):
    due_date: datetime


# Schema for detailed book representation, potentially including sensitive/internal fields
class BookInternal(BookBase):
    id: int
    is_available: bool
    checked_out_at: Optional[datetime] = None
    checked_out_by_id: Optional[int] = None
    due_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    embedding: Optional[str] = None # Internal schema can keep embedding

    class Config:
        from_attributes = True


# Schema for public book representation (e.g., in lists, search results)
class BookPublic(BookBase):
    id: int
    is_available: bool
    checked_out_at: Optional[datetime] = None
    # checked_out_by_id: Optional[int] = None # Decide if this is public
    due_date: Optional[datetime] = None
    created_at: datetime # Decide if this is public
    updated_at: datetime # Decide if this is public
    # No embedding field here

    class Config:
        from_attributes = True


# This can be the primary schema for API responses for a single book (if you want to show embedding by default for GET /book/{id})
# If GET /book/{id} should also hide embedding, it should also use BookPublic or a similar schema.
# For now, let's assume Book is the more detailed internal one.
class Book(BookInternal):
    pass


# Schema for the semantic search result item
class BookSearchResultItem(BaseModel):
    book: BookPublic # Uses the BookPublic schema (no embedding)
    score: float

    # No need for Config from_attributes here if BookPublic handles its own SQLAlchemy conversion
    # and the 'book' field in the data passed to this model is already a Pydantic model or a dict
    # However, if search_service directly returns a dict like {'book': SQLAlchemyBookModel, 'score': float},
    # then BookSearchResultItem's Config might still need from_attributes = True, or ensure BookPublic.from_orm is called.
    # For now, assuming the data structure from search_service is compatible or BookPublic handles it.
    class Config:
        from_attributes = True # Keep this for safety if the book object could be a raw model instance 