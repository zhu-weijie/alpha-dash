# app/schemas/token.py
from pydantic import BaseModel
from typing import Optional


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    # 'sub' (subject) is a standard JWT claim for the principal that is the subject of the JWT.
    # It could be user_id or email. Let's use email for now for simplicity.
    sub: Optional[str] = None 
    # You could also use: username: Optional[str] = None
    # Or: user_id: Optional[int] = None
