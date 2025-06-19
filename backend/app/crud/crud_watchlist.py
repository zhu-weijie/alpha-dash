# app/crud/crud_watchlist.py
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app import models


def get_watchlist_item_by_user_and_asset(
    db: Session, *, user_id: int, asset_id: int
) -> Optional[models.WatchlistItem]:
    return (
        db.query(models.WatchlistItem)
        .filter(
            models.WatchlistItem.user_id == user_id,
            models.WatchlistItem.asset_id == asset_id,
        )
        .first()
    )


def add_asset_to_watchlist(
    db: Session, *, asset_id: int, user_id: int
) -> Optional[models.WatchlistItem]:
    asset = db.query(models.Asset).filter(models.Asset.id == asset_id).first()
    if not asset:
        return None

    existing_item = get_watchlist_item_by_user_and_asset(
        db, user_id=user_id, asset_id=asset_id
    )
    if existing_item:
        return existing_item

    db_watchlist_item = models.WatchlistItem(user_id=user_id, asset_id=asset_id)
    db.add(db_watchlist_item)
    db.commit()
    db.refresh(db_watchlist_item)
    return db_watchlist_item


def get_watchlist_items_by_user(
    db: Session, *, user_id: int, skip: int = 0, limit: int = 100
) -> List[models.WatchlistItem]:
    return (
        db.query(models.WatchlistItem)
        .filter(models.WatchlistItem.user_id == user_id)
        .options(joinedload(models.WatchlistItem.asset))
        .order_by(models.WatchlistItem.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def remove_asset_from_watchlist(
    db: Session, *, asset_id: int, user_id: int
) -> Optional[models.WatchlistItem]:
    db_watchlist_item = get_watchlist_item_by_user_and_asset(
        db, user_id=user_id, asset_id=asset_id
    )
    if db_watchlist_item:
        db.delete(db_watchlist_item)
        db.commit()
        return db_watchlist_item
    return None
