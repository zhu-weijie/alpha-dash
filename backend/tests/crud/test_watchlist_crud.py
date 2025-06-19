# backend/tests/crud/test_watchlist_crud.py
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app import crud, models
from app.models.asset import AssetType


@pytest.fixture
def mock_db_session():
    db = MagicMock(spec=Session)
    mock_query = db.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_options = mock_filter.options.return_value
    mock_order_by = mock_options.order_by.return_value
    mock_offset = mock_order_by.offset.return_value
    mock_limit = mock_offset.limit.return_value

    mock_filter.first.return_value = None
    mock_limit.all.return_value = []
    return db


def test_get_watchlist_item_by_user_and_asset_found(mock_db_session: Session):
    user_id = 1
    asset_id = 101
    mock_item = models.WatchlistItem(id=1, user_id=user_id, asset_id=asset_id)
    mock_db_session.query.return_value.filter.return_value.first.return_value = (
        mock_item
    )

    item = crud.get_watchlist_item_by_user_and_asset(
        db=mock_db_session, user_id=user_id, asset_id=asset_id
    )

    assert item is not None
    assert item.id == 1
    assert item.user_id == user_id
    assert item.asset_id == asset_id
    mock_db_session.query.return_value.filter.assert_called()


def test_get_watchlist_item_by_user_and_asset_not_found(mock_db_session: Session):
    mock_db_session.query.return_value.filter.return_value.first.return_value = None
    item = crud.get_watchlist_item_by_user_and_asset(
        db=mock_db_session, user_id=1, asset_id=999
    )
    assert item is None


def test_add_asset_to_watchlist_new_item(mock_db_session: Session):
    user_id = 1
    asset_id = 101
    mock_asset = models.Asset(id=asset_id, symbol="AAPL", asset_type=AssetType.STOCK)

    mock_db_session.query.return_value.filter.return_value.first.side_effect = [
        mock_asset,
        None,
    ]

    item = crud.add_asset_to_watchlist(
        db=mock_db_session, user_id=user_id, asset_id=asset_id
    )

    assert item is not None
    assert item.user_id == user_id
    assert item.asset_id == asset_id
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(item)
    assert mock_db_session.query.call_args_list[0][0][0] == models.Asset
    assert mock_db_session.query.call_args_list[1][0][0] == models.WatchlistItem


def test_add_asset_to_watchlist_asset_not_found(mock_db_session: Session):
    user_id = 1
    asset_id = 999
    mock_db_session.query.return_value.filter.return_value.first.return_value = None

    item = crud.add_asset_to_watchlist(
        db=mock_db_session, user_id=user_id, asset_id=asset_id
    )

    assert item is None
    mock_db_session.add.assert_not_called()
    mock_db_session.query.assert_called_once_with(models.Asset)


def test_add_asset_to_watchlist_item_already_exists(mock_db_session: Session):
    user_id = 1
    asset_id = 101
    mock_asset = models.Asset(id=asset_id, symbol="AAPL", asset_type=AssetType.STOCK)
    mock_existing_watchlist_item = models.WatchlistItem(
        id=5, user_id=user_id, asset_id=asset_id
    )

    mock_db_session.query.return_value.filter.return_value.first.side_effect = [
        mock_asset,
        mock_existing_watchlist_item,
    ]

    item = crud.add_asset_to_watchlist(
        db=mock_db_session, user_id=user_id, asset_id=asset_id
    )

    assert item is not None
    assert item.id == mock_existing_watchlist_item.id
    mock_db_session.add.assert_not_called()
    mock_db_session.commit.assert_not_called()
    mock_db_session.refresh.assert_not_called()


def test_get_watchlist_items_by_user_empty(mock_db_session: Session):
    user_id = 1
    items = crud.get_watchlist_items_by_user(db=mock_db_session, user_id=user_id)
    assert items == []
    mock_db_session.query.return_value.filter.return_value.options.return_value.order_by.return_value.offset.assert_called_with(
        0
    )
    mock_db_session.query.return_value.filter.return_value.options.return_value.order_by.return_value.offset.return_value.limit.assert_called_with(
        100
    )


def test_get_watchlist_items_by_user_with_data_and_pagination(mock_db_session: Session):
    user_id = 1
    mock_asset1 = models.Asset(id=101, symbol="AAPL", asset_type=AssetType.STOCK)
    mock_asset2 = models.Asset(id=102, symbol="BTC", asset_type=AssetType.CRYPTO)
    mock_items_list = [
        models.WatchlistItem(
            id=1,
            user_id=user_id,
            asset_id=101,
            asset=mock_asset1,
            created_at=datetime.now(timezone.utc),
        ),
        models.WatchlistItem(
            id=2,
            user_id=user_id,
            asset_id=102,
            asset=mock_asset2,
            created_at=datetime.now(timezone.utc),
        ),
    ]
    mock_db_session.query.return_value.filter.return_value.options.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = (
        mock_items_list
    )

    items = crud.get_watchlist_items_by_user(
        db=mock_db_session, user_id=user_id, skip=5, limit=10
    )

    assert len(items) == 2
    assert items[0].asset.symbol == "AAPL"

    mock_db_session.query.assert_called_with(models.WatchlistItem)
    mock_db_session.query.return_value.filter.return_value.options.assert_called_once()  # Check options for joinedload
    mock_db_session.query.return_value.filter.return_value.options.return_value.order_by.assert_called_once()
    mock_db_session.query.return_value.filter.return_value.options.return_value.order_by.return_value.offset.assert_called_with(
        5
    )
    mock_db_session.query.return_value.filter.return_value.options.return_value.order_by.return_value.offset.return_value.limit.assert_called_with(
        10
    )


def test_remove_asset_from_watchlist_item_found(mock_db_session: Session):
    user_id = 1
    asset_id = 101
    mock_item_to_delete = models.WatchlistItem(id=1, user_id=user_id, asset_id=asset_id)

    with patch(
        "app.crud.crud_watchlist.get_watchlist_item_by_user_and_asset",
        return_value=mock_item_to_delete,
    ) as mock_getter:
        deleted_item = crud.remove_asset_from_watchlist(
            db=mock_db_session, user_id=user_id, asset_id=asset_id
        )

        assert deleted_item is not None
        assert deleted_item.id == mock_item_to_delete.id
        mock_getter.assert_called_once_with(
            mock_db_session,
            user_id=user_id,
            asset_id=asset_id,
        )
        mock_db_session.delete.assert_called_once_with(mock_item_to_delete)
        mock_db_session.commit.assert_called_once()


def test_remove_asset_from_watchlist_item_not_found(mock_db_session: Session):
    user_id = 1
    asset_id = 999

    with patch(
        "app.crud.crud_watchlist.get_watchlist_item_by_user_and_asset",
        return_value=None,
    ) as mock_getter:
        deleted_item = crud.remove_asset_from_watchlist(
            db=mock_db_session, user_id=user_id, asset_id=asset_id
        )

        assert deleted_item is None
        mock_getter.assert_called_once_with(
            mock_db_session,
            user_id=user_id,
            asset_id=asset_id,
        )
        mock_db_session.delete.assert_not_called()
        mock_db_session.commit.assert_not_called()
