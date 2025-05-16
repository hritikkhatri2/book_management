from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.models.book import Book
from app.schemas.book import BookCreate, BookUpdate


class CRUDBook:
    def get(self, db: Session, book_id: int) -> Optional[Book]:
        return db.query(Book).filter(Book.id == book_id).first()

    def get_by_isbn(self, db: Session, isbn: str) -> Optional[Book]:
        return db.query(Book).filter(Book.isbn == isbn).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Book]:
        return db.query(Book).offset(skip).limit(limit).all()

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

    def create(self, db: Session, *, obj_in: BookCreate) -> Book:
        db_obj = Book(
            title=obj_in.title,
            author=obj_in.author,
            isbn=obj_in.isbn,
            description=obj_in.description,
            publication_year=obj_in.publication_year,
            publisher=obj_in.publisher,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: Book, obj_in: BookUpdate
    ) -> Book:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, *, book_id: int) -> Book:
        obj = db.query(Book).get(book_id)
        db.delete(obj)
        db.commit()
        return obj

    def checkout(
        self, db: Session, *, book_id: int, user_id: int, due_date: datetime
    ) -> Book:
        db_obj = self.get(db, book_id)
        if db_obj:
            db_obj.is_available = False
            db_obj.checked_out_at = datetime.utcnow()
            db_obj.checked_out_by_id = user_id
            db_obj.due_date = due_date
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
        return db_obj

    def checkin(self, db: Session, *, book_id: int) -> Book:
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