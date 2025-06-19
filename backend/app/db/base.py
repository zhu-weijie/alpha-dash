# app/db/base.py
# Import all the models, so that Base has them before being
# imported by Alembic
from app.db.base_class import Base
from app.models.user import User
from app.models.asset import Asset
from app.models.portfolio_holding import PortfolioHolding
from app.models.watchlist_item import WatchlistItem

__all__ = ["Base", "User", "Asset", "PortfolioHolding", "WatchlistItem"]
