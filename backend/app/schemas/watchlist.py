# app/schemas/watchlist.py
from pydantic import BaseModel
from datetime import datetime
from .asset import Asset as AssetSchema


class WatchlistItemBase(BaseModel):
    asset_id: int


class WatchlistItemCreate(WatchlistItemBase):
    pass


class WatchlistItemResponse(WatchlistItemBase):
    id: int
    user_id: int
    created_at: datetime
    asset: AssetSchema

    model_config = {"from_attributes": True}
