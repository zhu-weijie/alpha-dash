# app/api/endpoints/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import crud, schemas, models
from app.db.session import get_db
from app.auth.dependencies import get_current_active_user

router = APIRouter()

@router.post("/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_new_user(
    *,
    db: Session = Depends(get_db),
    user_in: schemas.UserCreate
):
    """
    Create new user.
    """
    user = crud.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )
    new_user = crud.create_user(db=db, user_in=user_in)
    return new_user


@router.get("/me", response_model=schemas.User)
async def read_users_me(
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get current user.
    """
    return current_user
