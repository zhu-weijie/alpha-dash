# backend/tests/crud/test_portfolio_holding_crud.py
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from app import crud, models, schemas
from app.models.asset import AssetType


@pytest.fixture
def mock_db_session():
    """Reusable mock SQLAlchemy Session."""
    db_session = MagicMock(spec=Session)
    mock_query_obj = db_session.query.return_value
    mock_join_obj = mock_query_obj.join.return_value
    mock_filter_obj = mock_join_obj.filter.return_value

    mock_options_obj = mock_filter_obj.options.return_value
    mock_offset_obj = mock_options_obj.offset.return_value
    mock_limit_obj = mock_offset_obj.limit.return_value

    mock_group_by_obj = mock_filter_obj.group_by.return_value
    mock_order_by_obj = mock_group_by_obj.order_by.return_value

    mock_options_obj.first.return_value = None
    mock_limit_obj.all.return_value = []
    mock_order_by_obj.all.return_value = []

    return db_session


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

    added_object = mock_db_session.add.call_args[0][0]
    assert isinstance(added_object, models.PortfolioHolding)
    assert added_object.user_id == user_id
    assert added_object.asset_id == holding_in.asset_id


def test_get_portfolio_holdings_by_user_empty(mock_db_session: Session):
    user_id = 1
    mock_db_session.query.return_value.filter.return_value.options.return_value.offset.return_value.limit.return_value.all.return_value = (
        []
    )

    holdings = crud.get_portfolio_holdings_by_user(
        db=mock_db_session, user_id=user_id, skip=0, limit=10
    )
    assert holdings == []
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
    mock_db_session.query.return_value.filter.return_value.options.return_value.first.return_value = (
        mock_holding_obj
    )

    retrieved_holding = crud.get_portfolio_holding(
        db=mock_db_session, holding_id=holding_id, user_id=user_id
    )

    assert retrieved_holding is not None
    assert retrieved_holding.id == holding_id
    assert retrieved_holding.user_id == user_id
    mock_db_session.query.return_value.filter.assert_called()


def test_get_portfolio_holding_not_found(mock_db_session: Session):
    user_id = 1
    holding_id = 99
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


def test_update_portfolio_holding_success(mock_db_session: Session):
    initial_purchase_date = datetime.now(timezone.utc) - timedelta(days=10)
    db_holding_to_update = models.PortfolioHolding(
        id=1,
        user_id=1,
        asset_id=1,
        quantity=10.0,
        purchase_price=100.0,
        purchase_date=initial_purchase_date,
    )

    new_quantity = 12.0
    new_price = 110.0
    new_purchase_date_obj = datetime.now(timezone.utc)

    holding_update_schema = schemas.PortfolioHoldingUpdate(
        quantity=new_quantity,
        purchase_price=new_price,
        purchase_date=new_purchase_date_obj,
    )

    updated_holding = crud.update_portfolio_holding(
        db=mock_db_session,
        db_holding=db_holding_to_update,
        holding_in=holding_update_schema,
    )

    assert updated_holding is not None
    assert updated_holding.id == 1
    assert updated_holding.quantity == new_quantity
    assert updated_holding.purchase_price == new_price
    assert updated_holding.purchase_date == new_purchase_date_obj

    assert db_holding_to_update.quantity == new_quantity

    mock_db_session.add.assert_called_once_with(db_holding_to_update)
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(db_holding_to_update)


def test_update_portfolio_holding_partial_update(mock_db_session: Session):
    db_holding_to_update = models.PortfolioHolding(
        id=2,
        user_id=1,
        asset_id=2,
        quantity=5.0,
        purchase_price=200.0,
        purchase_date=datetime.now(timezone.utc),
    )
    original_price = db_holding_to_update.purchase_price

    holding_update_schema = schemas.PortfolioHoldingUpdate(quantity=7.5)

    updated_holding = crud.update_portfolio_holding(
        db=mock_db_session,
        db_holding=db_holding_to_update,
        holding_in=holding_update_schema,
    )

    assert updated_holding.quantity == 7.5
    assert updated_holding.purchase_price == original_price
    mock_db_session.add.assert_called_once()


def test_remove_portfolio_holding_success(mock_db_session: Session):
    user_id = 1
    holding_id_to_delete = 3

    mock_holding_to_delete = models.PortfolioHolding(
        id=holding_id_to_delete,
        user_id=user_id,
        asset_id=1,
        quantity=1,
        purchase_price=1,
        purchase_date=datetime.now(timezone.utc),
    )

    with patch(
        "app.crud.crud_portfolio_holding.get_portfolio_holding",
        return_value=mock_holding_to_delete,
    ) as mock_get_holding:
        deleted_holding = crud.remove_portfolio_holding(
            db=mock_db_session, holding_id=holding_id_to_delete, user_id=user_id
        )

        assert deleted_holding is not None
        assert deleted_holding.id == holding_id_to_delete

        mock_get_holding.assert_called_once_with(
            db=mock_db_session, holding_id=holding_id_to_delete, user_id=user_id
        )
        mock_db_session.delete.assert_called_once_with(mock_holding_to_delete)
        mock_db_session.commit.assert_called_once()


def test_remove_portfolio_holding_not_found_or_not_owned(mock_db_session: Session):
    user_id = 1
    holding_id_to_delete = 99

    with patch(
        "app.crud.crud_portfolio_holding.get_portfolio_holding", return_value=None
    ) as mock_get_holding:
        deleted_holding = crud.remove_portfolio_holding(
            db=mock_db_session, holding_id=holding_id_to_delete, user_id=user_id
        )

        assert deleted_holding is None
        mock_get_holding.assert_called_once_with(
            db=mock_db_session, holding_id=holding_id_to_delete, user_id=user_id
        )
        mock_db_session.delete.assert_not_called()
        mock_db_session.commit.assert_not_called()


def test_get_user_aggregated_asset_summary_no_holdings(mock_db_session: Session):
    user_id = 1
    mock_db_session.query.return_value.join.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = (
        []
    )

    summary = crud.get_user_aggregated_asset_summary(
        db=mock_db_session, user_id=user_id
    )
    assert summary == []


def test_get_user_aggregated_asset_summary_single_asset_single_holding(
    mock_db_session: Session,
):
    user_id = 1
    mock_row = MagicMock()
    mock_row.asset_id = 101
    mock_row.symbol = "AAPL"
    mock_row.name = "Apple Inc."
    mock_row.asset_type = AssetType.STOCK
    mock_row.total_quantity = 10.0
    mock_row.weighted_average_purchase_price = 150.0

    mock_db_session.query.return_value.join.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = [
        mock_row
    ]

    summary = crud.get_user_aggregated_asset_summary(
        db=mock_db_session, user_id=user_id
    )

    assert len(summary) == 1
    item = summary[0]
    assert item["asset_id"] == 101
    assert item["symbol"] == "AAPL"
    assert item["name"] == "Apple Inc."
    assert item["asset_type"] == AssetType.STOCK
    assert item["total_quantity"] == 10.0
    assert item["weighted_average_purchase_price"] == 150.0


def test_get_user_aggregated_asset_summary_single_asset_multiple_holdings(
    mock_db_session: Session,
):
    user_id = 1
    mock_row_aggregated_aapl = MagicMock()
    mock_row_aggregated_aapl.asset_id = 101
    mock_row_aggregated_aapl.symbol = "AAPL"
    mock_row_aggregated_aapl.name = "Apple Inc."
    mock_row_aggregated_aapl.asset_type = AssetType.STOCK
    mock_row_aggregated_aapl.total_quantity = 15.0
    mock_row_aggregated_aapl.weighted_average_purchase_price = 153.33333333333334

    mock_db_session.query.return_value.join.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = [
        mock_row_aggregated_aapl
    ]

    summary = crud.get_user_aggregated_asset_summary(
        db=mock_db_session, user_id=user_id
    )

    assert len(summary) == 1
    item = summary[0]
    assert item["asset_id"] == 101
    assert item["symbol"] == "AAPL"
    assert item["total_quantity"] == 15.0
    assert item["weighted_average_purchase_price"] == pytest.approx(153.33333333333334)


def test_get_user_aggregated_asset_summary_multiple_distinct_assets(
    mock_db_session: Session,
):
    user_id = 1
    mock_row_aapl = MagicMock()
    mock_row_aapl.asset_id = 101
    mock_row_aapl.symbol = "AAPL"
    mock_row_aapl.name = "Apple Inc."
    mock_row_aapl.asset_type = AssetType.STOCK
    mock_row_aapl.total_quantity = 15.0
    mock_row_aapl.weighted_average_purchase_price = 153.33
    mock_row_btc = MagicMock()
    mock_row_btc.asset_id = 102
    mock_row_btc.symbol = "BTC"
    mock_row_btc.name = "Bitcoin"
    mock_row_btc.asset_type = AssetType.CRYPTO
    mock_row_btc.total_quantity = 0.5
    mock_row_btc.weighted_average_purchase_price = 30000.0
    mock_db_session.query.return_value.join.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = [
        mock_row_aapl,
        mock_row_btc,
    ]

    summary = crud.get_user_aggregated_asset_summary(
        db=mock_db_session, user_id=user_id
    )

    assert len(summary) == 2

    mock_join_method = mock_db_session.query.return_value.join
    mock_join_method.assert_called_once()

    args_called, kwargs_called = mock_join_method.call_args

    assert args_called[0] == models.Asset

    expected_join_condition_str = str(
        models.PortfolioHolding.asset_id == models.Asset.id
    )
    actual_join_condition_str = str(args_called[1])
    assert actual_join_condition_str == expected_join_condition_str

    mock_db_session.query.return_value.join.return_value.filter.assert_called()
    mock_db_session.query.return_value.join.return_value.filter.return_value.group_by.assert_called()
    mock_db_session.query.return_value.join.return_value.filter.return_value.group_by.return_value.order_by.assert_called()
