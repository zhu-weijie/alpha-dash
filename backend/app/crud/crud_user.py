# app/crud/crud_user.py
from sqlalchemy.orm import Session
from app import models, schemas
from app.auth.security import get_password_hash

def get_user_by_email(db: Session, *, email: str) -> models.User | None:
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, *, user_in: schemas.UserCreate) -> models.User:
    hashed_password = get_password_hash(user_in.password)
    db_user = models.User(
        email=user_in.email,
        hashed_password=hashed_password,
        # is_active can be True by default as per model definition
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
