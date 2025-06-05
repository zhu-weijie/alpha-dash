# backend/tests/crud/test_asset_crud.py
import pytest
from unittest.mock import MagicMock, call # Import call for checking multiple calls
from sqlalchemy.orm import Session
from typing import List

from app import crud, models, schemas
from app.models.asset import AssetType # For creating test data

@pytest.fixture
def mock_db_session():
    """Reusable mock SQLAlchemy Session."""
    db_session = MagicMock(spec=Session)
    # Configure the query method and its chained calls
    mock_query = db_session.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_offset = mock_query.offset.return_value # For pagination
    mock_limit = mock_offset.limit.return_value # For pagination
    
    # Default return values
    mock_filter.first.return_value = None
    mock_limit.all.return_value = [] 
    db_session.get.return_value = None # For get_asset by PK
    return db_session

# --- Tests for get_asset ---
def test_get_asset_found(mock_db_session: Session):
    asset_id = 1
    mock_asset_obj = models.Asset(id=asset_id, symbol="AAPL", asset_type=AssetType.STOCK)
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_asset_obj
    # Alternative for get by PK if you prefer to mock .get() directly:
    # mock_db_session.get.return_value = mock_asset_obj

    retrieved_asset = crud.get_asset(db=mock_db_session, asset_id=asset_id)

    assert retrieved_asset is not None
    assert retrieved_asset.id == asset_id
    assert retrieved_asset.symbol == "AAPL"
    mock_db_session.query.assert_called_once_with(models.Asset)
    # mock_db_session.get.assert_called_once_with(models.Asset, asset_id) # If testing .get()

def test_get_asset_not_found(mock_db_session: Session):
    asset_id = 99
    mock_db_session.query.return_value.filter.return_value.first.return_value = None
    # mock_db_session.get.return_value = None # If testing .get()

    retrieved_asset = crud.get_asset(db=mock_db_session, asset_id=asset_id)
    assert retrieved_asset is None

# --- Tests for get_asset_by_symbol ---
def test_get_asset_by_symbol_found(mock_db_session: Session):
    symbol = "MSFT"
    mock_asset_obj = models.Asset(id=2, symbol=symbol.upper(), asset_type=AssetType.STOCK)
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_asset_obj

    retrieved_asset = crud.get_asset_by_symbol(db=mock_db_session, symbol=symbol)

    assert retrieved_asset is not None
    assert retrieved_asset.symbol == symbol.upper()

def test_get_asset_by_symbol_not_found(mock_db_session: Session):
    symbol = "NONEXIST"
    mock_db_session.query.return_value.filter.return_value.first.return_value = None
    retrieved_asset = crud.get_asset_by_symbol(db=mock_db_session, symbol=symbol)
    assert retrieved_asset is None

# --- Tests for get_assets (list) ---
def test_get_assets_empty(mock_db_session: Session):
    mock_db_session.query.return_value.offset.return_value.limit.return_value.all.return_value = []
    assets = crud.get_assets(db=mock_db_session, skip=0, limit=10)
    assert assets == []

def test_get_assets_with_data(mock_db_session: Session):
    mock_asset_list = [
        models.Asset(id=1, symbol="AAPL", asset_type=AssetType.STOCK),
        models.Asset(id=2, symbol="GOOGL", asset_type=AssetType.STOCK)
    ]
    mock_db_session.query.return_value.offset.return_value.limit.return_value.all.return_value = mock_asset_list
    
    assets = crud.get_assets(db=mock_db_session, skip=0, limit=10)
    
    assert len(assets) == 2
    assert assets[0].symbol == "AAPL"
    mock_db_session.query.assert_called_with(models.Asset)
    mock_db_session.query.return_value.offset.assert_called_with(0)
    mock_db_session.query.return_value.offset.return_value.limit.assert_called_with(10)

# --- Tests for create_asset ---
def test_create_asset_success(mock_db_session: Session):
    asset_in = schemas.AssetCreate(symbol="TSLA", name="Tesla Inc.", asset_type=AssetType.STOCK)
    
    created_asset = crud.create_asset(db=mock_db_session, asset_in=asset_in)
    
    assert created_asset is not None
    assert created_asset.symbol == "TSLA" # Should be uppercased by CRUD
    assert created_asset.name == "Tesla Inc."
    assert created_asset.asset_type == AssetType.STOCK
    
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(created_asset)
    
    # Check the object passed to db.add
    added_object = mock_db_session.add.call_args[0][0]
    assert isinstance(added_object, models.Asset)
    assert added_object.symbol == "TSLA"

# --- Tests for update_asset ---
def test_update_asset_success(mock_db_session: Session):
    db_asset = models.Asset(id=1, symbol="OLD", name="Old Name", asset_type=AssetType.CRYPTO)
    update_data_schema = schemas.AssetUpdate(symbol="NEW", name="New Name")

    updated_asset = crud.update_asset(db=mock_db_session, db_obj=db_asset, obj_in=update_data_schema)
    
    assert updated_asset.symbol == "NEW" # Uppercased
    assert updated_asset.name == "New Name"
    assert updated_asset.asset_type == AssetType.CRYPTO # Type not changed
    
    mock_db_session.add.assert_called_once_with(db_asset)
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(db_asset)

def test_update_asset_partial_update(mock_db_session: Session):
    db_asset = models.Asset(id=1, symbol="PART", name="Partial Name", asset_type=AssetType.STOCK)
    update_data_dict = {"name": "Updated Partial Name"} # Using dict for partial

    updated_asset = crud.update_asset(db=mock_db_session, db_obj=db_asset, obj_in=update_data_dict)
    
    assert updated_asset.symbol == "PART" # Symbol not changed
    assert updated_asset.name == "Updated Partial Name"
    mock_db_session.add.assert_called_once_with(db_asset)

# --- Tests for remove_asset ---
def test_remove_asset_found_and_deleted(mock_db_session: Session):
    asset_id_to_delete = 1
    mock_asset_to_delete = models.Asset(id=asset_id_to_delete, symbol="DEL", asset_type=AssetType.STOCK)
    mock_db_session.query.return_value.get.return_value = mock_asset_to_delete

    deleted_asset = crud.remove_asset(db=mock_db_session, asset_id=asset_id_to_delete)

    assert deleted_asset is not None
    assert deleted_asset.id == asset_id_to_delete
    mock_db_session.query.assert_called_once_with(models.Asset) # Check query for .get()
    mock_db_session.query.return_value.get.assert_called_once_with(asset_id_to_delete)
    mock_db_session.delete.assert_called_once_with(mock_asset_to_delete)
    mock_db_session.commit.assert_called_once()

def test_remove_asset_not_found(mock_db_session: Session):
    asset_id_to_delete = 99
    mock_db_session.query.return_value.get.return_value = None # Asset not found by .get()

    deleted_asset = crud.remove_asset(db=mock_db_session, asset_id=asset_id_to_delete)

    assert deleted_asset is None
    mock_db_session.delete.assert_not_called()
    mock_db_session.commit.assert_not_called()
