# app/schemas/asset.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.asset import AssetType


# Shared properties
class AssetBase(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=50)
    name: Optional[str] = Field(None, max_length=100)
    asset_type: AssetType


# Properties to receive via API on creation
class AssetCreate(AssetBase):
    pass


# Properties to receive via API on update
class AssetUpdate(BaseModel):  # Or inherit AssetBase and make fields optional
    symbol: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, max_length=100)
    asset_type: Optional[AssetType] = None


# Properties shared by models stored in DB
class AssetInDBBase(AssetBase):
    id: int
    created_at: datetime
    # updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


# Properties to return to client
class Asset(AssetInDBBase):
    pass
