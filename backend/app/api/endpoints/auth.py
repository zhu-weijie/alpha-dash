# app/api/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app import crud, schemas
from app.auth import security
from app.core.config import settings
from app.db.session import get_db

router = APIRouter()

@router.post("/token", response_model=schemas.Token)
# Using OAuth2PasswordRequestForm means the request must be form-data (username=..., password=...)
# 'username' field from OAuth2PasswordRequestForm will be treated as the email here.
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_email(db, email=form_data.username) # form_data.username is the email
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}, # Standard for token-based auth
        )
    if not user.is_active: # Optional: Check if user is active
         raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email}, # 'sub' (subject) is typically user identifier (email or ID)
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
