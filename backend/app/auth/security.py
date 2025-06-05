# app/auth/security.py
from passlib.context import CryptContext
# from datetime import datetime, timedelta
# from typing import Union, Any
# from jose import jwt
# from app.core.config import settings # For JWT later

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# --- JWT functions will be added here later ---
# def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
#     # ...
#     pass

# def decode_access_token(token: str):
#     # ...
#     pass
