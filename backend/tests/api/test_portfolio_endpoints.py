# backend/tests/api/test_portfolio_endpoints.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock # Keep patch for CRUD and FDS
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from main import app # Corrected import for your FastAPI app instance
from app import models, schemas, crud # Import crud here for clarity
from app.core.config import settings
from app.models.asset import AssetType
from app.auth.dependencies import get_current_active_user, get_db # Import the actual dependencies

# Fixture to provide a mock current user
@pytest.fixture
def mock_current_user_fixture():
    user = models.User(id=1, email="testuser@example.com", is_active=True, hashed_password="fake_hash")
    return user

# Fixture to provide a mock DB session
@pytest.fixture
def mock_db_session_fixture():
    db = MagicMock(spec=Session)
    # You might need to configure query().filter().first() etc. if crud functions are called
    return db


def test_view_user_portfolio_summary_success(
    mock_current_user_fixture: models.User,
    mock_db_session_fixture: Session
):
    # Get a consistent datetime for testing
    now_utc = datetime.now(timezone.utc)

    # Prepare mock data for what CRUD should return
    mock_asset_aapl = models.Asset(
        id=1, symbol="AAPL", name="Apple Inc.", asset_type=AssetType.STOCK,
        created_at=now_utc # Add created_at
    )
    mock_asset_btc = models.Asset(
        id=2, symbol="BTC", name="Bitcoin", asset_type=AssetType.CRYPTO,
        created_at=now_utc # Add created_at
    )

    mock_holding_aapl = models.PortfolioHolding(
        id=101, user_id=mock_current_user_fixture.id, asset_id=1, quantity=10,
        purchase_price=150.0, purchase_date=now_utc, # Using now_utc for purchase_date too
        asset_info=mock_asset_aapl,
        created_at=now_utc # Add created_at
    )
    mock_holding_btc = models.PortfolioHolding(
        id=102, user_id=mock_current_user_fixture.id, asset_id=2, quantity=0.5,
        purchase_price=30000.0, purchase_date=now_utc,
        asset_info=mock_asset_btc,
        created_at=now_utc # Add created_at
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
    with patch("app.api.endpoints.portfolio.crud.get_portfolio_holdings_by_user", return_value=mock_holdings_list) as mock_crud_get_holdings, \
         patch("app.api.endpoints.portfolio.fds.fetch_current_price") as mock_fetch_price:

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

        expected_total_purchase = (10 * 150.0) + (0.5 * 30000.0) # 16500
        expected_total_current = (10 * 170.0) + (0.5 * 35000.0)  # 19200
        expected_total_gain_loss = expected_total_current - expected_total_purchase # 2700

        assert data["total_purchase_value"] == pytest.approx(expected_total_purchase)
        assert data["total_current_value"] == pytest.approx(expected_total_current)
        assert data["total_gain_loss"] == pytest.approx(expected_total_gain_loss)
        
        assert len(data["holdings"]) == 2
        
        aapl_holding_resp = next(h for h in data["holdings"] if h["asset_info"]["symbol"] == "AAPL")
        assert aapl_holding_resp["current_price"] == 170.0
        assert aapl_holding_resp["current_value"] == 1700.0
        assert aapl_holding_resp["gain_loss"] == 200.0

        btc_holding_resp = next(h for h in data["holdings"] if h["asset_info"]["symbol"] == "BTC")
        assert btc_holding_resp["current_price"] == 35000.0
        assert btc_holding_resp["current_value"] == 17500.0
        assert btc_holding_resp["gain_loss"] == 2500.0
        # --- End Assertions ---

        # Verify mocks
        mock_crud_get_holdings.assert_called_once_with(
            db=mock_db_session_fixture, 
            user_id=mock_current_user_fixture.id, 
            skip=0, 
            limit=100
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
