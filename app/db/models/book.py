from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base


class Book(Base):
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    author = Column(String(255), nullable=False, index=True)
    isbn = Column(String(13), unique=True, index=True)
    description = Column(Text, nullable=True)
    publication_year = Column(Integer, nullable=True)
    publisher = Column(String(255), nullable=True)
    
    # Book status
    is_available = Column(Boolean, default=True)
    checked_out_at = Column(DateTime, nullable=True)
    checked_out_by_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    due_date = Column(DateTime, nullable=True)
    
    # Vector embedding for semantic search
    embedding = Column(Text, nullable=True)
    
    # Relationships
    checked_out_by = relationship("User", back_populates="checked_out_books") 