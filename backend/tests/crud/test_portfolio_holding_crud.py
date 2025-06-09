# backend/tests/crud/test_portfolio_holding_crud.py
import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app import crud, models, schemas


@pytest.fixture
def mock_db_session():
    """Reusable mock SQLAlchemy Session."""
    db_session = MagicMock(spec=Session)
    mock_query = db_session.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_options = mock_filter.options.return_value  # For joinedload
    mock_offset = mock_options.offset.return_value  # For pagination
    mock_limit = mock_offset.limit.return_value  # For pagination

    # Default return values
    mock_filter.first.return_value = None  # For get_portfolio_holding by id+user_id
    mock_options.first.return_value = None  # If options is called before first
    mock_limit.all.return_value = []  # For get_portfolio_holdings_by_user
    return db_session


# --- Test for create_portfolio_holding ---
def test_create_portfolio_holding_success(mock_db_session: Session):
    user_id = 1
    purchase_dt = datetime.now(timezone.utc)
    holding_in = schemas.PortfolioHoldingCreate(
        asset_id=1, quantity=10.5, purchase_price=150.25, purchase_date=purchase_dt
    )

    created_holding = crud.create_portfolio_holding(
        db=mock_db_session, holding_in=holding_in, user_id=user_id
    )

    assert created_holding is not None
    assert created_holding.asset_id == holding_in.asset_id
    assert created_holding.quantity == holding_in.quantity
    assert created_holding.purchase_price == holding_in.purchase_price
    assert created_holding.purchase_date == purchase_dt
    assert created_holding.user_id == user_id

    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(created_holding)

    # Check the object passed to db.add
    added_object = mock_db_session.add.call_args[0][0]
    assert isinstance(added_object, models.PortfolioHolding)
    assert added_object.user_id == user_id
    assert added_object.asset_id == holding_in.asset_id


# --- Tests for get_portfolio_holdings_by_user ---
def test_get_portfolio_holdings_by_user_empty(mock_db_session: Session):
    user_id = 1
    # The fixture by default sets .all() to return []
    mock_db_session.query.return_value.filter.return_value.options.return_value.offset.return_value.limit.return_value.all.return_value = (
        []
    )

    holdings = crud.get_portfolio_holdings_by_user(
        db=mock_db_session, user_id=user_id, skip=0, limit=10
    )
    assert holdings == []
    # Check that filter was called with the correct user_id
    # The actual filter object is complex to assert directly, but we can check if query().filter() was called.
    mock_db_session.query.return_value.filter.assert_called()


def test_get_portfolio_holdings_by_user_with_data(mock_db_session: Session):
    user_id = 1
    mock_holding_list = [
        models.PortfolioHolding(
            id=1,
            user_id=user_id,
            asset_id=1,
            quantity=5,
            purchase_price=100,
            purchase_date=datetime.now(timezone.utc),
        ),
        models.PortfolioHolding(
            id=2,
            user_id=user_id,
            asset_id=2,
            quantity=2.5,
            purchase_price=2000,
            purchase_date=datetime.now(timezone.utc),
        ),
    ]
    mock_db_session.query.return_value.filter.return_value.options.return_value.offset.return_value.limit.return_value.all.return_value = (
        mock_holding_list
    )

    holdings = crud.get_portfolio_holdings_by_user(
        db=mock_db_session, user_id=user_id, skip=0, limit=10
    )

    assert len(holdings) == 2
    assert holdings[0].id == 1
    assert holdings[1].asset_id == 2
    mock_db_session.query.assert_called_with(models.PortfolioHolding)
    mock_db_session.query.return_value.filter.return_value.options.return_value.offset.assert_called_with(
        0
    )
    mock_db_session.query.return_value.filter.return_value.options.return_value.offset.return_value.limit.assert_called_with(
        10
    )


# --- Tests for get_portfolio_holding (single holding by id and user_id) ---
def test_get_portfolio_holding_found_and_owned(mock_db_session: Session):
    user_id = 1
    holding_id = 5
    mock_holding_obj = models.PortfolioHolding(
        id=holding_id,
        user_id=user_id,
        asset_id=3,
        quantity=1,
        purchase_price=50,
        purchase_date=datetime.now(timezone.utc),
    )
    # Configure what .first() returns for this specific test
    mock_db_session.query.return_value.filter.return_value.options.return_value.first.return_value = (
        mock_holding_obj
    )

    retrieved_holding = crud.get_portfolio_holding(
        db=mock_db_session, holding_id=holding_id, user_id=user_id
    )

    assert retrieved_holding is not None
    assert retrieved_holding.id == holding_id
    assert retrieved_holding.user_id == user_id
    # Check that filter was called (difficult to assert the exact filter condition with MagicMock easily)
    # For more precise filter checking, you might need more advanced mocking or a helper.
    mock_db_session.query.return_value.filter.assert_called()


def test_get_portfolio_holding_not_found(mock_db_session: Session):
    user_id = 1
    holding_id = 99  # Non-existent
    # .first() is already configured to return None by default in the fixture
    mock_db_session.query.return_value.filter.return_value.options.return_value.first.return_value = (
        None
    )

    retrieved_holding = crud.get_portfolio_holding(
        db=mock_db_session, holding_id=holding_id, user_id=user_id
    )
    assert retrieved_holding is None


def test_get_portfolio_holding_found_not_owned(mock_db_session: Session):
    user_id_requester = 2
    holding_id = 7
    mock_db_session.query.return_value.filter.return_value.options.return_value.first.return_value = (
        None
    )

    retrieved_holding = crud.get_portfolio_holding(
        db=mock_db_session, holding_id=holding_id, user_id=user_id_requester
    )
    assert retrieved_holding is None
