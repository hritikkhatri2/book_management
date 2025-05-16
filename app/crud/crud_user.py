from typing import Optional, List
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.roles import UserRole


class CRUDUser:
    def get(self, db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def get_by_google_id(self, db: Session, google_id: str) -> Optional[User]:
        return db.query(User).filter(User.google_id == google_id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[User]:
        return db.query(User).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        db_obj = User(
            email=obj_in.email,
            full_name=obj_in.full_name,
            google_id=obj_in.google_id,
            is_active=obj_in.is_active if obj_in.is_active is not None else True,
            role=obj_in.role if obj_in.role else UserRole.CUSTOMER
        )
        if db_obj.role == UserRole.SUPERUSER:
            db_obj.is_superuser = True
        else:
            db_obj.is_superuser = False
            
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: User, obj_in: UserUpdate
    ) -> User:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_role(self, db: Session, *, db_obj: User, new_role: UserRole) -> User:
        db_obj.role = new_role
        if new_role == UserRole.SUPERUSER:
            db_obj.is_superuser = True
        else:
            db_obj.is_superuser = False
            
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def is_active(self, user: User) -> bool:
        return user.is_active

    def is_superuser_role(self, user: User) -> bool:
        return user.role == UserRole.SUPERUSER


user = CRUDUser() 