# app/schemas/user.py
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

# Shared properties
class UserBase(BaseModel):
    email: EmailStr

# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str

# Properties to receive via API on update (optional, for later)
# class UserUpdate(UserBase):
#     password: Optional[str] = None
#     is_active: Optional[bool] = None

# Properties shared by models stored in DB
class UserInDBBase(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    # updated_at: Optional[datetime] # Not always needed in API responses for user

    model_config = {
        "from_attributes": True
    }

# Properties to return to client
class User(UserInDBBase):
    pass

# Properties stored in DB (including hashed_password)
# class UserInDB(UserInDBBase):
#     hashed_password: str
