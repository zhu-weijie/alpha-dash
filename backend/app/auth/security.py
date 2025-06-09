# app/auth/security.py
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings
from app import schemas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Default to expiry from settings if not provided
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    print(
        f"DEBUG: Encoding JWT with algorithm: '{settings.ALGORITHM}' and key: '{settings.SECRET_KEY[:5]}...'"
    )
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> schemas.TokenData | None:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        # 'sub' is expected to be the email in our case
        email: str | None = payload.get("sub")
        if email is None:
            return None  # Or raise an exception for missing 'sub'
        return schemas.TokenData(
            sub=email
        )  # Or TokenData(username=username) if you used that
    except (
        JWTError
    ):  # Catches various errors like ExpiredSignatureError, InvalidTokenError
        return None
