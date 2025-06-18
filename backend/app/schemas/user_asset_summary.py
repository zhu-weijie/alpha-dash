# app/schemas/user_asset_summary.py
from pydantic import BaseModel
from typing import Optional
from app.models.asset import AssetType


class UserAssetSummaryItem(BaseModel):
    asset_id: int
    symbol: str
    name: Optional[str] = None
    asset_type: AssetType
    total_quantity: float
    weighted_average_purchase_price: float
