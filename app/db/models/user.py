from sqlalchemy import Column, Integer, String, Boolean, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.core.roles import UserRole


class User(Base):
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    google_id = Column(String(255), unique=True, nullable=True)
    
    role = Column(SAEnum(UserRole), default=UserRole.CUSTOMER, nullable=False)
    
    # Relationships
    checked_out_books = relationship("Book", back_populates="checked_out_by")

    # Property to align is_superuser with role, if desired
    @property
    def is_admin_level(self) -> bool:
        return self.role == UserRole.SUPERUSER
    
    @property
    def is_librarian_level(self) -> bool:
        return self.role in [UserRole.LIBRARIAN, UserRole.SUPERUSER] 