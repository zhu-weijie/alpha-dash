# app/crud/__init__.py
from .crud_user import create_user, get_user_by_email
from .crud_asset import (
    create_asset,
    get_asset,
    get_asset_by_symbol,
    get_assets,
    update_asset,
    remove_asset,
    update_asset_last_price_timestamp,
)
from .crud_portfolio_holding import (
    create_portfolio_holding,
    get_portfolio_holdings_by_user,
    get_portfolio_holding,
    update_portfolio_holding,
    remove_portfolio_holding,
    get_user_aggregated_asset_summary,
)
from .crud_watchlist import (
    get_watchlist_item_by_user_and_asset,
    add_asset_to_watchlist,
    get_watchlist_items_by_user,
    remove_asset_from_watchlist,
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
    "update_asset_last_price_timestamp",
    "get_user_aggregated_asset_summary",
    "get_watchlist_item_by_user_and_asset",
    "add_asset_to_watchlist",
    "get_watchlist_items_by_user",
    "remove_asset_from_watchlist",
]
