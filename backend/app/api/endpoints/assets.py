# app/api/endpoints/assets.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app import crud, models, schemas
from app.db.session import get_db
from app.auth.dependencies import get_current_active_user # For protected routes

router = APIRouter()

@router.post("/", response_model=schemas.Asset, status_code=status.HTTP_201_CREATED)
def create_new_asset(
    *,
    db: Session = Depends(get_db),
    asset_in: schemas.AssetCreate,
    current_user: models.User = Depends(get_current_active_user) # Protected
) -> Any:
    """
    Create new asset. (Requires authentication)
    """
    existing_asset = crud.get_asset_by_symbol(db, symbol=asset_in.symbol)
    if existing_asset:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Asset with symbol '{asset_in.symbol}' already exists.",
        )
    asset = crud.create_asset(db=db, asset_in=asset_in)
    return asset

@router.get("/", response_model=List[schemas.Asset])
def read_assets_list(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    symbol: Optional[str] = Query(None, min_length=1, max_length=50)
    # current_user: models.User = Depends(get_current_active_user) # Public for now
) -> Any:
    """
    Retrieve a list of assets with pagination.
    """
    if symbol:
        asset = crud.get_asset_by_symbol(db, symbol=symbol)
        return [asset] if asset else [] # Return as list or empty list
    assets = crud.get_assets(db, skip=skip, limit=limit)
    return assets

@router.get("/{asset_id}", response_model=schemas.Asset)
def read_single_asset(
    *,
    db: Session = Depends(get_db),
    asset_id: int,
    # current_user: models.User = Depends(get_current_active_user) # Public for now
) -> Any:
    """
    Get a specific asset by ID.
    """
    asset = crud.get_asset(db, asset_id=asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return asset

@router.put("/{asset_id}", response_model=schemas.Asset)
def update_existing_asset(
    *,
    db: Session = Depends(get_db),
    asset_id: int,
    asset_in: schemas.AssetUpdate,
    current_user: models.User = Depends(get_current_active_user) # Protected
) -> Any:
    """
    Update an asset. (Requires authentication)
    """
    db_asset = crud.get_asset(db, asset_id=asset_id)
    if not db_asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    
    if asset_in.symbol and asset_in.symbol.upper() != db_asset.symbol.upper():
        existing_asset_with_new_symbol = crud.get_asset_by_symbol(db, symbol=asset_in.symbol)
        if existing_asset_with_new_symbol and existing_asset_with_new_symbol.id != asset_id:
             raise HTTPException(status_code=400, detail="Another asset with this symbol already exists.")

    asset = crud.update_asset(db=db, db_obj=db_asset, obj_in=asset_in)
    return asset

@router.delete("/{asset_id}", response_model=schemas.Asset) # Or just status_code=204
def delete_asset_by_id(
    *,
    db: Session = Depends(get_db),
    asset_id: int,
    current_user: models.User = Depends(get_current_active_user) # Protected
) -> Any:
    """
    Delete an asset. (Requires authentication)
    """
    asset = crud.remove_asset(db=db, asset_id=asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return asset # Returns the deleted asset
