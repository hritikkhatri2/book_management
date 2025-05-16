from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.crud.crud_user import user as crud_user
from app.schemas.user import User as UserSchema, UserRoleUpdate
from app.db.models.user import User as UserModel
from app.core.roles import UserRole

router = APIRouter()

@router.get("/", response_model=List[UserSchema])
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    # current_user: UserModel = Depends(deps.get_current_active_superuser) # Or specific role
    current_user: UserModel = Depends(deps.get_current_active_librarian_or_superuser)
) -> List[UserModel]: # Type hint with UserModel as CRUD returns it, Pydantic handles response_model
    """
    Retrieve users. (Protected for LIBRARIAN or SUPERUSER)
    """
    users = crud_user.get_multi(db, skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=UserSchema)
def read_user_by_id(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: UserModel = Depends(deps.get_current_active_librarian_or_superuser)
) -> UserModel:
    """
    Get a specific user by ID. (Protected for LIBRARIAN or SUPERUSER)
    """
    user = crud_user.get(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}/role", response_model=UserSchema)
def update_user_role(
    user_id: int,
    role_in: UserRoleUpdate,
    db: Session = Depends(deps.get_db),
    current_user: UserModel = Depends(deps.get_current_active_superuser) # Only SUPERUSER can change roles
) -> UserModel:
    """
    Update a user's role. (Protected for SUPERUSER only)
    """
    user_to_update = crud_user.get(db, user_id=user_id)
    if not user_to_update:
        raise HTTPException(status_code=404, detail="User to update not found")

    # Business logic: A superuser cannot have their own role changed by this endpoint to prevent self-demotion.
    # Also, cannot promote another user to superuser if the current superuser is the only one (optional)
    if user_to_update.id == current_user.id and role_in.role != UserRole.SUPERUSER:
        raise HTTPException(status_code=403, detail="Superuser cannot change their own role to a non-superuser role via this endpoint.")

    # Prevent changing role to SUPERUSER if target is not already a superuser
    # This is a design choice: only initial setup or direct DB change can make a superuser
    # or a more complex logic is needed. For now, let's say superusers can only be demoted to librarian.
    # if role_in.role == UserRole.SUPERUSER and user_to_update.role != UserRole.SUPERUSER:
    #     raise HTTPException(status_code=403, detail="Cannot promote user to superuser via this endpoint.")

    # Allow superuser to change others to librarian or customer.
    # Allow superuser to change librarian to customer, or customer to librarian.
    if role_in.role == UserRole.SUPERUSER and current_user.role != UserRole.SUPERUSER:
        raise HTTPException(status_code=403, detail="Only a superuser can assign the superuser role.")

    updated_user = crud_user.update_role(db, db_obj=user_to_update, new_role=role_in.role)
    return updated_user 