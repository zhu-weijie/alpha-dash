# app/auth/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth import security
from app.core.config import settings
from app import crud, models
from app.db.session import get_db

# Define the OAuth2 scheme. tokenUrl points to your login endpoint.
# Ensure this path matches how you access your login endpoint (including /api/v1 prefix).
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = security.decode_access_token(token)
    if not token_data or not token_data.sub: # Check if sub (email) is present
        raise credentials_exception
    
    user = crud.get_user_by_email(db, email=token_data.sub)
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user
