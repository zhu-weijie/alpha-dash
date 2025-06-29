# app/models/asset.py
from sqlalchemy import Column, Integer, String, Enum as SAEnum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base
import enum


class AssetType(enum.Enum):
    STOCK = "stock"
    CRYPTO = "crypto"


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, index=True)
    asset_type = Column(SAEnum(AssetType), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    last_price_updated_at = Column(DateTime(timezone=True), nullable=True, default=None)

    holdings = relationship("PortfolioHolding", back_populates="asset_info")
    watched_by_users_items = relationship("WatchlistItem", back_populates="asset")
