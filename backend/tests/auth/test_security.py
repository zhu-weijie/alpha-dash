# backend/tests/auth/test_security.py
import pytest
from app.auth.security import get_password_hash, verify_password
from app.auth.security import create_access_token, decode_access_token
from datetime import datetime, timedelta, timezone
from jose import jwt
from app.core.config import settings

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

def test_decode_access_token_valid():
    email = "test@example.com"
    token_data_in = {"sub": email}
    token = create_access_token(token_data_in)
    
    decoded_token_data = decode_access_token(token)
    assert decoded_token_data is not None
    assert decoded_token_data.sub == email

def test_decode_access_token_invalid_signature():
    # Create a token with one key, try to decode with another (or tamper it)
    token_data_in = {"sub": "test@example.com"}
    original_token = create_access_token(token_data_in)
    
    # Simulate decoding with a wrong key by directly calling jwt.decode or by
    # temporarily patching settings.SECRET_KEY if decode_access_token always uses global settings.
    # For simplicity here, we'll test that an invalid token string returns None.
    invalid_token_string = original_token + "tamper" 
    assert decode_access_token(invalid_token_string) is None

def test_decode_access_token_expired():
    # Create a token that expires immediately or in the past
    email = "expired@example.com"
    # Create a token that expired 1 second ago
    token = create_access_token({"sub": email}, expires_delta=timedelta(seconds=-1))
    
    # Depending on system clock and execution speed, direct expiry check can be flaky.
    # A more robust test might involve mocking `datetime.now`.
    # For now, we expect decode_access_token to return None for an expired token.
    assert decode_access_token(token) is None

def test_decode_access_token_missing_sub():
    # Create a token without the 'sub' field (if your create_access_token allows it)
    # Or, more directly, test if decode_access_token handles a valid JWT payload missing 'sub'
    payload_without_sub = {"exp": datetime.now(timezone.utc) + timedelta(minutes=15)}
    token_without_sub = jwt.encode(payload_without_sub, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    assert decode_access_token(token_without_sub) is None
