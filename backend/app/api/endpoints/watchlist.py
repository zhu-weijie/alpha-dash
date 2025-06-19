# app/api/endpoints/watchlist.py
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List, Any

from app import crud, models, schemas
from app.db.session import get_db
from app.auth.dependencies import get_current_active_user

router = APIRouter()


@router.post(
    "/items/",
    response_model=schemas.WatchlistItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_to_user_watchlist(
    *,
    db: Session = Depends(get_db),
    item_in: schemas.WatchlistItemCreate,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    existing_item = crud.get_watchlist_item_by_user_and_asset(
        db, user_id=current_user.id, asset_id=item_in.asset_id
    )
    if existing_item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Asset already in watchlist.",
        )

    asset = crud.get_asset(db, asset_id=item_in.asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset with ID {item_in.asset_id} not found.",
        )

    watchlist_item = crud.add_asset_to_watchlist(
        db=db, asset_id=item_in.asset_id, user_id=current_user.id
    )
    if watchlist_item and not watchlist_item.asset:
        watchlist_item.asset = asset

    return watchlist_item


@router.get("/items/", response_model=List[schemas.WatchlistItemResponse])
def read_user_watchlist(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    items = crud.get_watchlist_items_by_user(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
    return items


@router.delete(
    "/items/{asset_id}", status_code=status.HTTP_204_NO_CONTENT
)  # Or return deleted item
def remove_from_user_watchlist(
    *,
    db: Session = Depends(get_db),
    asset_id: int,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    deleted_item = crud.remove_asset_from_watchlist(
        db=db, asset_id=asset_id, user_id=current_user.id
    )
    if not deleted_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found in watchlist.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
