from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import logging

from app.api import deps
from app.crud import crud_book
from app.schemas import book as book_schema
from app.db.models.user import User as UserModel
from app.core.roles import UserRole
from app.services.search_service import search_service
from app.db.models.book import Book

logger = logging.getLogger(__name__)
router = APIRouter()

def update_faiss_index_background(db_session: Session):
    logger.info("Scheduling FAISS index rebuild in background.")
    try:
        search_service.build_index(db_session)
        logger.info("FAISS index rebuild completed in background.")
    except Exception as e:
        logger.error(f"Error rebuilding FAISS index in background: {e}", exc_info=True)
    finally:
        pass

@router.get("/", response_model=List[book_schema.BookPublic])
def list_books(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(deps.get_current_active_user),
) -> List[book_schema.BookPublic]:
    """
    Retrieve all books.
    """
    books_db = crud_book.book.get_multi(db, skip=skip, limit=limit)
    return books_db

@router.post("/", response_model=book_schema.Book)
def create_book(
    *,
    db: Session = Depends(deps.get_db),
    book_in: book_schema.BookCreate,
    background_tasks: BackgroundTasks,
    current_user: UserModel = Depends(deps.get_current_active_librarian_or_superuser),
) -> book_schema.Book:
    """
    Create new book.
    """
    book = crud_book.book.create(db, obj_in=book_in)
    background_tasks.add_task(update_faiss_index_background, db)
    return book

@router.get("/my-books", response_model=List[book_schema.BookPublic])
def get_my_checked_out_books(
    *,
    db: Session = Depends(deps.get_db),
    current_user: UserModel = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 100,
) -> List[book_schema.BookPublic]:
    """
    Get all books currently checked out by the authenticated user.
    """
    return crud_book.book.get_user_checked_out_books(
        db, user_id=current_user.id, skip=skip, limit=limit
    )

@router.get("/search/{query}", response_model=List[book_schema.BookPublic])
def search_books(
    *,
    db: Session = Depends(deps.get_db),
    query: str,
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(deps.get_current_active_user),
) -> List[book_schema.BookPublic]:
    """
    Search books by title, author, or ISBN.
    """
    books_db = crud_book.book.search(db, query=query, skip=skip, limit=limit)
    return books_db

@router.get("/{book_id}", response_model=book_schema.BookPublic)
def get_book(
    *,
    db: Session = Depends(deps.get_db),
    book_id: int,
    current_user: UserModel = Depends(deps.get_current_active_user),
) -> book_schema.BookPublic:
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
    background_tasks: BackgroundTasks,
    current_user: UserModel = Depends(deps.get_current_active_librarian_or_superuser),
) -> book_schema.Book:
    """
    Update book.
    """
    book = crud_book.book.get(db, book_id=book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    updated_book = crud_book.book.update(db, db_obj=book, obj_in=book_in)
    background_tasks.add_task(update_faiss_index_background, db)
    return updated_book

@router.delete("/{book_id}", response_model=book_schema.Book)
def delete_book(
    *,
    db: Session = Depends(deps.get_db),
    book_id: int,
    background_tasks: BackgroundTasks,
    current_user: UserModel = Depends(deps.get_current_active_librarian_or_superuser),
) -> book_schema.Book:
    """
    Delete book.
    """
    book = crud_book.book.get(db, book_id=book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    deleted_book = crud_book.book.delete(db, book_id=book_id)
    if deleted_book is None:
        raise HTTPException(status_code=404, detail="Book not found during deletion attempt")
    background_tasks.add_task(update_faiss_index_background, db)
    return deleted_book

@router.post("/{book_id}/checkout", response_model=book_schema.BookPublic)
def checkout_book(
    *,
    db: Session = Depends(deps.get_db),
    book_id: int,
    checkout_data: book_schema.BookCheckout,
    current_user: UserModel = Depends(deps.get_current_active_user),
) -> book_schema.BookPublic:
    """
    Checkout a book.
    """
    book = crud_book.book.get(db, book_id=book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if not book.is_available:
        raise HTTPException(status_code=400, detail="Book is already checked out")
    checked_out_book = crud_book.book.checkout(
        db,
        book_id=book_id,
        user_id=current_user.id,
        due_date=checkout_data.due_date,
    )
    if not checked_out_book:
        raise HTTPException(status_code=500, detail="Failed to checkout book")
    return checked_out_book

@router.post("/{book_id}/checkin", response_model=book_schema.BookPublic)
def checkin_book(
    *,
    db: Session = Depends(deps.get_db),
    book_id: int,
    current_user: UserModel = Depends(deps.get_current_active_user),
) -> book_schema.BookPublic:
    """
    Check in a book.
    """
    book = crud_book.book.get(db, book_id=book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book.is_available:
        raise HTTPException(status_code=400, detail="Book is already checked in")
    if book.checked_out_by_id != current_user.id and current_user.role != UserRole.SUPERUSER and current_user.role != UserRole.LIBRARIAN:
        raise HTTPException(status_code=403, detail="Not authorized to check in this book")
    checked_in_book = crud_book.book.checkin(db, book_id=book_id)
    if not checked_in_book:
        raise HTTPException(status_code=500, detail="Failed to checkin book")
    return checked_in_book 