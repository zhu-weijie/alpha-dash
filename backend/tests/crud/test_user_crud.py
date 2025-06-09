# backend/tests/crud/test_user_crud.py
import pytest
from unittest.mock import MagicMock, patch # For mocking
from sqlalchemy.orm import Session

from app import crud, models, schemas

@pytest.fixture
def mock_db_session():
    # Create a MagicMock object that behaves like a SQLAlchemy Session
    db_session = MagicMock(spec=Session)
    
    # Mock the query method and its chained calls
    mock_query = db_session.query.return_value
    mock_filter = mock_query.filter.return_value
    
    # Configure what .first() returns by default (None for user not found)
    mock_filter.first.return_value = None 
    return db_session

def test_create_user_success(mock_db_session: Session):
    user_email = "test@example.com"
    user_password = "password123"
    user_in = schemas.UserCreate(email=user_email, password=user_password)

    # Mock get_password_hash to control its output and not rely on the actual hashing
    with patch("app.crud.crud_user.get_password_hash") as mock_get_hash:
        mock_get_hash.return_value = "hashed_password_from_mock"

        created_user = crud.create_user(db=mock_db_session, user_in=user_in)

        # Assertions
        assert created_user is not None
        assert created_user.email == user_email
        assert created_user.hashed_password == "hashed_password_from_mock"
        
        # Check if db methods were called
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(created_user)
        
        # Check the object passed to db.add
        added_object = mock_db_session.add.call_args[0][0]
        assert isinstance(added_object, models.User)
        assert added_object.email == user_email
        assert added_object.hashed_password == "hashed_password_from_mock"

def test_get_user_by_email_found(mock_db_session: Session):
    user_email = "exists@example.com"
    mock_user = models.User(id=1, email=user_email, hashed_password="somehash")
    
    # Configure the mock for this specific test case
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
    
    found_user = crud.get_user_by_email(db=mock_db_session, email=user_email)
    
    assert found_user is not None
    assert found_user.email == user_email
    mock_db_session.query.assert_called_once_with(models.User)
    # You can add more specific assertions on the filter call if needed

def test_get_user_by_email_not_found(mock_db_session: Session):
    user_email = "nonexistent@example.com"
    
    # .first() is already configured to return None by default in the fixture
    # mock_db_session.query.return_value.filter.return_value.first.return_value = None (default)

    found_user = crud.get_user_by_email(db=mock_db_session, email=user_email)
    
    assert found_user is None
