# backend/tests/auth/test_security.py
import pytest
from app.auth.security import get_password_hash, verify_password

def test_get_password_hash():
    password = "testpassword123"
    hashed_password = get_password_hash(password)
    
    assert hashed_password is not None
    assert isinstance(hashed_password, str)
    assert password != hashed_password # Ensure it's actually hashed
    assert len(hashed_password) > len(password) # Bcrypt hashes are typically longer

def test_verify_password_correct():
    password = "testpassword123"
    hashed_password = get_password_hash(password)
    
    assert verify_password(password, hashed_password) is True

def test_verify_password_incorrect():
    password = "testpassword123"
    wrong_password = "wrongpassword"
    hashed_password = get_password_hash(password)
    
    assert verify_password(wrong_password, hashed_password) is False

def test_verify_password_with_different_hash():
    password = "testpassword123"
    # A known bcrypt hash for a different password or just an invalid string
    # For example, a hash of "anotherpassword"
    different_hashed_password = "$2b$12$D4Jt2qK9yXmJ.2oE5rA9z.Z.y3Y8N4oB/xR6eE7tW1iS8mD2zC6yG" 
    
    assert verify_password(password, different_hashed_password) is False

# Optional: Test with an empty password if your app logic allows/disallows it
# def test_get_password_hash_empty_string():
#     password = ""
#     hashed_password = get_password_hash(password)
#     assert verify_password(password, hashed_password) is True
