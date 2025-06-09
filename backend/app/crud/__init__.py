# app/crud/__init__.py
from .crud_user import create_user, get_user_by_email
from .crud_asset import (
    create_asset,
    get_asset,
    get_asset_by_symbol,
    get_assets,
    update_asset,
    remove_asset,
)
from .crud_portfolio_holding import (
    create_portfolio_holding,
    get_portfolio_holdings_by_user,
    get_portfolio_holding,
    update_portfolio_holding,
    remove_portfolio_holding,
)

__all__ = [
    "create_user",
    "get_user_by_email",
    "create_asset",
    "get_asset",
    "get_asset_by_symbol",
    "get_assets",
    "update_asset",
    "remove_asset",
    "create_portfolio_holding",
    "get_portfolio_holdings_by_user",
    "get_portfolio_holding",
    "update_portfolio_holding",
    "remove_portfolio_holding",
]
