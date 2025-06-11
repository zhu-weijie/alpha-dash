# backend/tests/tasks/test_price_tasks.py
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from typing import List

from app.tasks.price_tasks import (
    refresh_all_asset_prices_task,
    PRICE_STALENESS_THRESHOLD_MINUTES,
)
from app import models
from app.models.asset import AssetType


@pytest.fixture
def mock_db_session_for_task():
    """Mocks the SQLAlchemy session used by the task."""
    db_session = MagicMock(spec=Session)
    return db_session


@pytest.fixture
def mock_asset_list():
    """Provides a list of mock AssetModel objects."""
    now = datetime.now(timezone.utc)
    stale_time = now - timedelta(minutes=PRICE_STALENESS_THRESHOLD_MINUTES + 5)
    fresh_time = now - timedelta(minutes=PRICE_STALENESS_THRESHOLD_MINUTES - 5)

    return [
        models.Asset(
            id=1,
            symbol="STALE_STOCK",
            name="Stale Stock Inc",
            asset_type=AssetType.STOCK,
            last_price_updated_at=stale_time,
        ),
        models.Asset(
            id=2,
            symbol="FRESH_CRYPTO",
            name="Fresh Crypto Coin",
            asset_type=AssetType.CRYPTO,
            last_price_updated_at=fresh_time,
        ),
        models.Asset(
            id=3,
            symbol="NEVER_UPDATED",
            name="New Asset",
            asset_type=AssetType.STOCK,
            last_price_updated_at=None,
        ),
        models.Asset(
            id=4,
            symbol="FAIL_FETCH",
            name="Fetch Fail Asset",
            asset_type=AssetType.STOCK,
            last_price_updated_at=None,
        ),
        models.Asset(
            id=5,
            symbol="FAIL_DB_UPDATE",
            name="DB Update Fail Asset",
            asset_type=AssetType.CRYPTO,
            last_price_updated_at=None,
        ),
    ]


@patch("app.tasks.price_tasks.SessionLocal")
@patch("app.tasks.price_tasks.crud.get_assets")
@patch("app.tasks.price_tasks.fds_orchestrator.get_current_price")
@patch("app.tasks.price_tasks.crud.update_asset_last_price_timestamp")
def test_refresh_task_mixed_scenarios(
    mock_update_timestamp: MagicMock,
    mock_get_current_price: MagicMock,
    mock_get_assets_crud: MagicMock,
    mock_session_local: MagicMock,
    mock_db_session_for_task: Session,
    mock_asset_list: List[models.Asset],
    capsys,
):
    mock_session_local.return_value = mock_db_session_for_task
    mock_get_assets_crud.return_value = mock_asset_list

    def get_price_side_effect(symbol, asset_type):
        print(f"MOCK_PRICE_FETCH: Called for {symbol}")
        if symbol == "FAIL_FETCH":
            return None
        if symbol == "FAIL_DB_UPDATE":
            return 200.0
        if symbol in ["STALE_STOCK", "NEVER_UPDATED"]:
            return 100.0
        return 50.0

    mock_get_current_price.side_effect = get_price_side_effect

    def update_timestamp_side_effect(db, asset_model, timestamp):
        if asset_model.symbol == "FAIL_DB_UPDATE":
            print(f"MOCK_DB_UPDATE: Simulating failure for {asset_model.symbol}")
            raise Exception("Simulated DB update error")
        print(f"MOCK_DB_UPDATE: Called for {asset_model.symbol}")
        asset_model.last_price_updated_at = timestamp
        return asset_model

    mock_update_timestamp.side_effect = update_timestamp_side_effect

    result = refresh_all_asset_prices_task.s().apply().get()

    mock_get_assets_crud.assert_called_once_with(mock_db_session_for_task, limit=10000)

    assert mock_get_current_price.call_count == 4
    mock_get_current_price.assert_any_call(
        symbol="STALE_STOCK", asset_type=AssetType.STOCK.value
    )
    mock_get_current_price.assert_any_call(
        symbol="NEVER_UPDATED", asset_type=AssetType.STOCK.value
    )
    mock_get_current_price.assert_any_call(
        symbol="FAIL_FETCH", asset_type=AssetType.STOCK.value
    )
    mock_get_current_price.assert_any_call(
        symbol="FAIL_DB_UPDATE", asset_type=AssetType.CRYPTO.value
    )

    assert mock_update_timestamp.call_count == 3

    symbols_updated = [
        call_args[1]["asset_model"].symbol
        for call_args in mock_update_timestamp.call_args_list
    ]
    assert "STALE_STOCK" in symbols_updated
    assert "NEVER_UPDATED" in symbols_updated
    assert "FAIL_DB_UPDATE" in symbols_updated

    captured = capsys.readouterr()
    assert "CELERY_TASK: Asset FRESH_CRYPTO - Skipping (fresh:" in captured.out
    assert "CELERY_TASK: Failed to get price for FAIL_FETCH" in captured.out
    assert (
        "CELERY_TASK: ERROR processing asset FAIL_DB_UPDATE: Simulated DB update error"
        in captured.out
    )
    assert "Refreshed: 2" in result
    assert "Skipped (fresh): 1" in result
    assert "Failed: 2" in result


@patch("app.tasks.price_tasks.SessionLocal")
@patch("app.tasks.price_tasks.crud.get_assets")
def test_refresh_task_no_assets_in_db(
    mock_get_assets_crud: MagicMock,
    mock_session_local: MagicMock,
    mock_db_session_for_task: Session,
    capsys,
):
    mock_session_local.return_value = mock_db_session_for_task
    mock_get_assets_crud.return_value = []

    result = refresh_all_asset_prices_task.s().apply().get()

    assert result == "No assets to refresh."
    captured = capsys.readouterr()
    assert "CELERY_TASK: No assets found in DB to refresh." in captured.out
    mock_get_assets_crud.assert_called_once()


@patch("app.tasks.price_tasks.SessionLocal")
@patch(
    "app.tasks.price_tasks.crud.get_assets",
    side_effect=Exception("DB connection error"),
)
def test_refresh_task_get_assets_raises_exception(
    mock_get_assets_crud: MagicMock,
    mock_session_local: MagicMock,
    mock_db_session_for_task: Session,
    capsys,
):
    mock_session_local.return_value = mock_db_session_for_task

    result = refresh_all_asset_prices_task.s().apply().get()

    assert "Task failed with critical error: DB connection error" in result
    captured = capsys.readouterr()
    assert (
        "CRITICAL ERROR in refresh_all_asset_prices_task: DB connection error"
        in captured.out
    )
