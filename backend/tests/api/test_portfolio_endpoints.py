# backend/tests/api/test_portfolio_endpoints.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from main import app
from app import models
from app.core.config import settings
from app.models.asset import AssetType
from app.auth.dependencies import (
    get_current_active_user,
    get_db,
)  # Import the actual dependencies


# Fixture to provide a mock current user
@pytest.fixture
def mock_current_user_fixture():
    user = models.User(
        id=1, email="testuser@example.com", is_active=True, hashed_password="fake_hash"
    )
    return user


# Fixture to provide a mock DB session
@pytest.fixture
def mock_db_session_fixture():
    db = MagicMock(spec=Session)
    # You might need to configure query().filter().first() etc. if crud functions are called
    return db


@pytest.fixture
def client_with_auth_override(mock_current_user_fixture, mock_db_session_fixture):
    """Fixture to provide TestClient with overridden auth and db dependencies"""

    def override_get_current_active_user():
        return mock_current_user_fixture

    def override_get_db():
        return mock_db_session_fixture

    # Apply overrides
    original_auth_override = app.dependency_overrides.get(get_current_active_user)
    original_db_override = app.dependency_overrides.get(get_db)

    app.dependency_overrides[get_current_active_user] = override_get_current_active_user
    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    yield client  # Yield the client for the test to use

    # Cleanup: Restore original overrides or clear them
    if original_auth_override:
        app.dependency_overrides[get_current_active_user] = original_auth_override
    else:
        del app.dependency_overrides[get_current_active_user]

    if original_db_override:
        app.dependency_overrides[get_db] = original_db_override
    else:
        del app.dependency_overrides[get_db]


def test_view_user_portfolio_summary_success(
    mock_current_user_fixture: models.User, mock_db_session_fixture: Session
):
    # Get a consistent datetime for testing
    now_utc = datetime.now(timezone.utc)

    # Prepare mock data for what CRUD should return
    mock_asset_aapl = models.Asset(
        id=1,
        symbol="AAPL",
        name="Apple Inc.",
        asset_type=AssetType.STOCK,
        created_at=now_utc,  # Add created_at
    )
    mock_asset_btc = models.Asset(
        id=2,
        symbol="BTC",
        name="Bitcoin",
        asset_type=AssetType.CRYPTO,
        created_at=now_utc,  # Add created_at
    )

    mock_holding_aapl = models.PortfolioHolding(
        id=101,
        user_id=mock_current_user_fixture.id,
        asset_id=1,
        quantity=10,
        purchase_price=150.0,
        purchase_date=now_utc,  # Using now_utc for purchase_date too
        asset_info=mock_asset_aapl,
        created_at=now_utc,  # Add created_at
    )
    mock_holding_btc = models.PortfolioHolding(
        id=102,
        user_id=mock_current_user_fixture.id,
        asset_id=2,
        quantity=0.5,
        purchase_price=30000.0,
        purchase_date=now_utc,
        asset_info=mock_asset_btc,
        created_at=now_utc,  # Add created_at
    )
    mock_holdings_list = [mock_holding_aapl, mock_holding_btc]

    # --- Dependency Override Setup ---
    # Override the get_current_active_user dependency for the app
    # This ensures that any call to this dependency during the test client request
    # will return our mock_current_user_fixture.
    # Similarly, override get_db.
    def override_get_current_active_user():
        return mock_current_user_fixture

    def override_get_db():
        return mock_db_session_fixture

    app.dependency_overrides[get_current_active_user] = override_get_current_active_user
    app.dependency_overrides[get_db] = override_get_db
    # --- End Dependency Override Setup ---

    # Client must be created AFTER dependency_overrides are set if they are global to the app
    # Or, ensure TestClient is created within the test function or uses a context manager for overrides.
    # For simplicity now, let's create client here.
    client = TestClient(app)

    # Patch the services that are called *within* the endpoint, after dependencies are resolved.
    # The target for patch is where the function is *looked up*.
    with patch(
        "app.api.endpoints.portfolio.crud.get_portfolio_holdings_by_user",
        return_value=mock_holdings_list,
    ) as mock_crud_get_holdings, patch(
        "app.api.endpoints.portfolio.get_current_price"
    ) as mock_fetch_price:

        # Configure mock_fetch_price side effect
        def side_effect_fetch_price(symbol):
            if symbol == "AAPL":
                return 170.0
            if symbol == "BTC":
                return 35000.0
            return None

        mock_fetch_price.side_effect = side_effect_fetch_price

        # Make the API call - no Authorization header needed now due to dependency override
        response = client.get(f"{settings.API_V1_STR}/portfolio/holdings/")

        # --- Assertions ---
        assert response.status_code == 200
        data = response.json()

        expected_total_purchase = (10 * 150.0) + (0.5 * 30000.0)  # 16500
        expected_total_current = (10 * 170.0) + (0.5 * 35000.0)  # 19200
        expected_total_gain_loss = (
            expected_total_current - expected_total_purchase
        )  # 2700

        assert data["total_purchase_value"] == pytest.approx(expected_total_purchase)
        assert data["total_current_value"] == pytest.approx(expected_total_current)
        assert data["total_gain_loss"] == pytest.approx(expected_total_gain_loss)

        assert len(data["holdings"]) == 2

        aapl_holding_resp = next(
            h for h in data["holdings"] if h["asset_info"]["symbol"] == "AAPL"
        )
        assert aapl_holding_resp["current_price"] == 170.0
        assert aapl_holding_resp["current_value"] == 1700.0
        assert aapl_holding_resp["gain_loss"] == 200.0

        btc_holding_resp = next(
            h for h in data["holdings"] if h["asset_info"]["symbol"] == "BTC"
        )
        assert btc_holding_resp["current_price"] == 35000.0
        assert btc_holding_resp["current_value"] == 17500.0
        assert btc_holding_resp["gain_loss"] == 2500.0
        # --- End Assertions ---

        # Verify mocks
        mock_crud_get_holdings.assert_called_once_with(
            db=mock_db_session_fixture,
            user_id=mock_current_user_fixture.id,
            skip=0,
            limit=100,
        )
        assert mock_fetch_price.call_count == 2
        mock_fetch_price.assert_any_call("AAPL")
        mock_fetch_price.assert_any_call("BTC")

    # --- Cleanup Dependency Overrides ---
    # It's crucial to clean up dependency overrides after the test or test module
    # to avoid interference between tests if the TestClient 'app' instance is shared.
    # A better way is to use a fixture for the client that handles setup/teardown of overrides.
    # For now, manual cleanup:
    app.dependency_overrides.clear()
    # --- End Cleanup ---


def test_view_user_portfolio_summary_no_holdings(
    client_with_auth_override: TestClient,  # Use the client fixture
    # mock_current_user_fixture is implicitly used by client_with_auth_override
    # mock_db_session_fixture is implicitly used by client_with_auth_override
):
    client = client_with_auth_override  # For brevity if preferred

    # Patch the CRUD function that the endpoint calls directly,
    # and the financial data service (though it shouldn't be called).
    # The get_current_active_user and get_db are handled by the client_with_auth_override fixture.
    with patch(
        "app.api.endpoints.portfolio.crud.get_portfolio_holdings_by_user",
        return_value=[],
    ) as mock_crud_get_holdings, patch(
        "app.api.endpoints.portfolio.get_current_price"
    ) as mock_fetch_price:

        response = client.get(f"{settings.API_V1_STR}/portfolio/holdings/")

        assert response.status_code == 200
        data = response.json()
        assert data["total_purchase_value"] == 0.0
        assert data["total_current_value"] == 0.0
        assert data["total_gain_loss"] == 0.0
        assert data["total_gain_loss_percent"] == 0.0  # Check this logic if 0/0
        assert len(data["holdings"]) == 0

        # Verify mocks were called (or not called) as expected
        # mock_crud_get_holdings should be called with current_user.id from the fixture
        # We need to access mock_current_user_fixture here if it's not passed directly
        # For simplicity, let's assume user_id=1 was used in mock_current_user_fixture
        # To do this properly, the fixture client_with_auth_override could also yield the user object
        # or the test function could take mock_current_user_fixture as an argument.
        # For now, let's assume we know the user_id from the fixture.
        # If mock_current_user_fixture is available in this scope:
        # mock_crud_get_holdings.assert_called_once_with(db=ANY, user_id=mock_current_user_fixture.id, skip=0, limit=100)
        # If not, just assert it was called:
        mock_crud_get_holdings.assert_called_once()  # Further refinement needed to check args if mock_db_session_fixture is not passed here

        mock_fetch_price.assert_not_called()  # No holdings, so no price fetching should occur


def test_view_user_portfolio_summary_price_fetch_fails(
    client_with_auth_override: TestClient,
    mock_current_user_fixture: models.User,
    mock_db_session_fixture: Session,
):
    client = client_with_auth_override  # Use the client from the fixture

    now_utc = datetime.now(timezone.utc)  # For consistent timestamps

    # Prepare mock Asset and PortfolioHolding data, including created_at
    mock_asset_aapl = models.Asset(
        id=1,
        symbol="AAPL",
        name="Apple Inc.",
        asset_type=AssetType.STOCK,
        created_at=now_utc,  # Essential for Pydantic validation
    )
    mock_holding_aapl = models.PortfolioHolding(
        id=101,
        user_id=mock_current_user_fixture.id,
        asset_id=1,
        quantity=10,
        purchase_price=150.0,
        purchase_date=now_utc,
        asset_info=mock_asset_aapl,  # Simulate eager loaded data
        created_at=now_utc,  # Essential for Pydantic validation
    )
    mock_holdings_list = [mock_holding_aapl]

    # Patch the dependencies/services called by the endpoint logic
    # get_current_active_user and get_db are handled by the client_with_auth_override fixture
    with patch(
        "app.api.endpoints.portfolio.crud.get_portfolio_holdings_by_user",
        return_value=mock_holdings_list,
    ) as mock_crud_get_holdings, patch(
        "app.api.endpoints.portfolio.get_current_price", return_value=None
    ) as mock_fetch_price:  # Simulate price fetch failure

        # Make the API call
        response = client.get(f"{settings.API_V1_STR}/portfolio/holdings/")

        # Assertions
        assert response.status_code == 200
        data = response.json()

        expected_purchase_value = 10 * 150.0  # 1500.0
        assert data["total_purchase_value"] == pytest.approx(expected_purchase_value)
        assert data["total_current_value"] == pytest.approx(
            0.0
        )  # Price fetch failed, so current value is 0
        assert data["total_gain_loss"] == pytest.approx(
            0.0 - expected_purchase_value
        )  # -1500.0

        # For total_gain_loss_percent
        # Your logic: if total_purchase_value > 0: (total_gain_loss / total_purchase_value) * 100
        # else: (0.0 if total_current_value == 0 else None)
        # Here, total_purchase_value = 1500 > 0. So, (-1500 / 1500) * 100 = -100.0
        expected_gain_loss_percent = (-1500.0 / 1500.0) * 100
        assert data["total_gain_loss_percent"] == pytest.approx(
            expected_gain_loss_percent
        )

        assert len(data["holdings"]) == 1
        aapl_holding_resp = data["holdings"][0]

        assert aapl_holding_resp["asset_info"]["symbol"] == "AAPL"
        assert aapl_holding_resp["current_price"] is None
        assert aapl_holding_resp["current_value"] is None
        assert aapl_holding_resp["gain_loss"] is None
        assert (
            aapl_holding_resp["gain_loss_percent"] is None
        )  # Because current_value is None

        # Verify mocks
        mock_crud_get_holdings.assert_called_once_with(
            db=mock_db_session_fixture,
            user_id=mock_current_user_fixture.id,
            skip=0,
            limit=100,
        )
        mock_fetch_price.assert_called_once_with("AAPL")
