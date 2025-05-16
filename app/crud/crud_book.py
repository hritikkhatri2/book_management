from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_
import json
import logging

from app.db.models.book import Book
from app.schemas.book import BookCreate, BookUpdate
from app.utils.embedding import get_embedding

logger = logging.getLogger(__name__)

class CRUDBook:
    def get(self, db: Session, book_id: int) -> Optional[Book]:
        return db.query(Book).filter(Book.id == book_id).first()

    def get_by_isbn(self, db: Session, isbn: str) -> Optional[Book]:
        return db.query(Book).filter(Book.isbn == isbn).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 10000
    ) -> List[Book]:
        return db.query(Book).offset(skip).limit(limit).all()

    def get_user_checked_out_books(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Book]:
        """Get all books currently checked out by a specific user."""
        return (
            db.query(Book)
            .filter(
                Book.checked_out_by_id == user_id,
                Book.is_available == False
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search(
        self, db: Session, *, query: str, skip: int = 0, limit: int = 100
    ) -> List[Book]:
        return (
            db.query(Book)
            .filter(
                or_(
                    Book.title.ilike(f"%{query}%"),
                    Book.author.ilike(f"%{query}%"),
                    Book.isbn.ilike(f"%{query}%"),
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def _generate_and_set_embedding(self, book_obj: Book):
        text_for_embedding = f"{book_obj.title} {book_obj.author} {book_obj.description or ''}".strip()
        if text_for_embedding:
            try:
                embedding_vector = get_embedding(text_for_embedding)
                book_obj.embedding = json.dumps(embedding_vector)
                logger.info(f"Generated and stored embedding for book ID {book_obj.id}")
            except Exception as e:
                logger.error(f"Error generating embedding for book ID {book_obj.id if hasattr(book_obj, 'id') else 'NEW'}: {e}", exc_info=True)
                book_obj.embedding = None
        else:
            logger.warning(f"No text content to generate embedding for book ID {book_obj.id if hasattr(book_obj, 'id') else 'NEW'}. Setting embedding to None.")
            book_obj.embedding = None

    def create(self, db: Session, *, obj_in: BookCreate) -> Book:
        db_obj = Book(
            title=obj_in.title,
            author=obj_in.author,
            isbn=obj_in.isbn,
            description=obj_in.description,
            publication_year=obj_in.publication_year,
            publisher=obj_in.publisher,
        )
        self._generate_and_set_embedding(db_obj)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: Book, obj_in: BookUpdate
    ) -> Book:
        update_data = obj_in.model_dump(exclude_unset=True)
        needs_embedding_update = False

        for field, value in update_data.items():
            if field in ["title", "author", "description"] and getattr(db_obj, field) != value:
                needs_embedding_update = True
            setattr(db_obj, field, value)
        
        if needs_embedding_update:
            logger.info(f"Book content changed for ID {db_obj.id}. Regenerating embedding.")
            self._generate_and_set_embedding(db_obj)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, *, book_id: int) -> Optional[Book]:
        obj = db.query(Book).get(book_id)
        if obj:
            db.delete(obj)
            db.commit()
            return obj
        return None

    def checkout(
        self, db: Session, *, book_id: int, user_id: int, due_date: datetime
    ) -> Optional[Book]:
        db_obj = self.get(db, book_id)
        if db_obj:
            if not db_obj.is_available:
                logger.warning(f"Attempt to check out already unavailable book ID: {book_id}")
                return db_obj
            db_obj.is_available = False
            db_obj.checked_out_at = datetime.utcnow()
            db_obj.checked_out_by_id = user_id
            db_obj.due_date = due_date
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
        return db_obj

    def checkin(self, db: Session, *, book_id: int) -> Optional[Book]:
        db_obj = self.get(db, book_id)
        if db_obj:
            db_obj.is_available = True
            db_obj.checked_out_at = None
            db_obj.checked_out_by_id = None
            db_obj.due_date = None
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
        return db_obj

book = CRUDBook() 