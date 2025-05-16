from typing import Optional
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: Optional[bool] = True


class UserCreate(UserBase):
    google_id: str


class UserUpdate(UserBase):
    email: Optional[EmailStr] = None


class UserInDBBase(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    google_id: Optional[str] = None

    class Config:
        from_attributes = True


class User(UserInDBBase):
    pass


class UserInDB(UserInDBBase):
    pass 