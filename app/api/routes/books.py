from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.api import deps
from app.crud import crud_book
from app.schemas import book as book_schema
from app.schemas.user import User

router = APIRouter()

@router.get("/", response_model=List[book_schema.Book])
def list_books(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> List[book_schema.Book]:
    """
    Retrieve all books.
    """
    books = crud_book.book.get_multi(db, skip=skip, limit=limit)
    return books

@router.post("/", response_model=book_schema.Book)
def create_book(
    *,
    db: Session = Depends(deps.get_db),
    book_in: book_schema.BookCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> book_schema.Book:
    """
    Create new book.
    """
    book = crud_book.book.create(db, obj_in=book_in)
    return book

@router.get("/{book_id}", response_model=book_schema.Book)
def get_book(
    *,
    db: Session = Depends(deps.get_db),
    book_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> book_schema.Book:
    """
    Get book by ID.
    """
    book = crud_book.book.get(db, book_id=book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@router.put("/{book_id}", response_model=book_schema.Book)
def update_book(
    *,
    db: Session = Depends(deps.get_db),
    book_id: int,
    book_in: book_schema.BookUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> book_schema.Book:
    """
    Update book.
    """
    book = crud_book.book.get(db, book_id=book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    book = crud_book.book.update(db, db_obj=book, obj_in=book_in)
    return book

@router.delete("/{book_id}", response_model=book_schema.Book)
def delete_book(
    *,
    db: Session = Depends(deps.get_db),
    book_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> book_schema.Book:
    """
    Delete book.
    """
    book = crud_book.book.get(db, book_id=book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    book = crud_book.book.delete(db, book_id=book_id)
    return book

@router.post("/{book_id}/checkout", response_model=book_schema.Book)
def checkout_book(
    *,
    db: Session = Depends(deps.get_db),
    book_id: int,
    checkout_data: book_schema.BookCheckout,
    current_user: User = Depends(deps.get_current_active_user),
) -> book_schema.Book:
    """
    Checkout a book.
    """
    book = crud_book.book.get(db, book_id=book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if not book.is_available:
        raise HTTPException(status_code=400, detail="Book is already checked out")
    book = crud_book.book.checkout(
        db,
        book_id=book_id,
        user_id=current_user.id,
        due_date=checkout_data.due_date,
    )
    return book

@router.post("/{book_id}/checkin", response_model=book_schema.Book)
def checkin_book(
    *,
    db: Session = Depends(deps.get_db),
    book_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> book_schema.Book:
    """
    Check in a book.
    """
    book = crud_book.book.get(db, book_id=book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book.is_available:
        raise HTTPException(status_code=400, detail="Book is already checked in")
    if book.checked_out_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to check in this book")
    book = crud_book.book.checkin(db, book_id=book_id)
    return book

@router.get("/search/{query}", response_model=List[book_schema.Book])
def search_books(
    *,
    db: Session = Depends(deps.get_db),
    query: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> List[book_schema.Book]:
    """
    Search books by title, author, or ISBN.
    """
    books = crud_book.book.search(db, query=query, skip=skip, limit=limit)
    return books 