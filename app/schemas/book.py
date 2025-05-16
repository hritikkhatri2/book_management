from typing import Optional
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


class BookInDB(BookBase):
    id: int
    is_available: bool
    checked_out_at: Optional[datetime] = None
    checked_out_by_id: Optional[int] = None
    due_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Book(BookInDB):
    pass 