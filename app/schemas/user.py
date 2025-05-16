from typing import Optional
from pydantic import BaseModel, EmailStr
from app.core.roles import UserRole


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: Optional[bool] = True


class UserCreate(UserBase):
    google_id: str
    role: Optional[UserRole] = UserRole.CUSTOMER


class UserUpdate(UserBase):
    email: Optional[EmailStr] = None


class UserRoleUpdate(BaseModel):
    role: UserRole


class UserInDBBase(UserBase):
    id: int
    is_active: bool
    google_id: Optional[str] = None
    role: UserRole

    class Config:
        from_attributes = True


class User(UserInDBBase):
    pass


class UserInDB(UserInDBBase):
    pass 