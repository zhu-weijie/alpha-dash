# app/services/financial_data_orchestrator.py
from typing import List, Dict, Any, Optional

from app.core.config import settings
from .data_providers import yahoo_finance_provider as yf_provider
from .data_providers import alpha_vantage_provider as av_provider
from app.cache import shared_cache
from datetime import date


_cache = {"price_cache": {}, "history_cache": {}}
CACHE_DURATION_SECONDS = 15 * 60


def get_current_price(symbol: str, asset_type: Optional[str] = None) -> Optional[float]:
    symbol_upper = symbol.upper()
    cache_key = f"price:{symbol_upper}_{asset_type or 'unknown'}"

    cached_price = shared_cache.get_shared_cache(cache_key)
    if cached_price is not None:
        print(f"ORCHESTRATOR CACHE HIT (Redis): Using cached price for {symbol_upper}")
        return float(cached_price)

    print(
        f"ORCHESTRATOR: Cache miss for current price of {symbol_upper} (type: {asset_type}). Trying yfinance."
    )
    price = yf_provider.fetch_yf_current_price(symbol, asset_type)

    if price is None and settings.ALPHA_VANTAGE_API_KEY:
        print(
            f"ORCHESTRATOR: yfinance failed for current price of {symbol_upper}. Trying AlphaVantage as fallback."
        )
        if asset_type and asset_type.lower() == "crypto":
            base_crypto_symbol = symbol_upper.replace("USDT", "").replace("USD", "")
            if base_crypto_symbol:
                price = av_provider.fetch_av_crypto_current_price(base_crypto_symbol)
        else:
            price = av_provider.fetch_av_stock_current_price(symbol_upper)

    if price is not None:
        shared_cache.set_shared_cache(cache_key, price)
        print(
            f"ORCHESTRATOR: Successfully fetched current price for {symbol_upper}: {price}. Stored in Redis."
        )
    else:
        print(
            f"ORCHESTRATOR: Failed to fetch current price for {symbol_upper} from all providers."
        )

    return price


def _deserialize_history_from_cache(
    cached_data_raw: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Converts date strings in cached history data back to date objects."""
    processed_cached_data = []
    if not isinstance(cached_data_raw, list):
        print(
            f"ORCHESTRATOR CACHE WARNING: Expected list from cache, got {type(cached_data_raw)}"
        )
        return []

    for point_dict in cached_data_raw:
        if not isinstance(point_dict, dict):
            continue
        try:
            point_dict_copy = point_dict.copy()
            date_val = point_dict_copy.get("date")
            if isinstance(date_val, str):
                point_dict_copy["date"] = date.fromisoformat(date_val)
            processed_cached_data.append(point_dict_copy)
        except (ValueError, TypeError) as e:
            print(
                f"ORCHESTRATOR CACHE WARNING: Malformed date string '{point_dict.get('date')}' in cached data. Point: {point_dict} Error: {e}"
            )
            processed_cached_data.append(point_dict.copy())
    return processed_cached_data


def get_historical_data(
    symbol: str, asset_type: Optional[str] = None, outputsize: str = "compact"
) -> Optional[List[Dict[str, Any]]]:
    symbol_upper = symbol.upper()
    period_map = {"compact": "3mo", "full": "max"}
    yf_period = period_map.get(outputsize, "3mo")
    cache_key = f"history:{symbol_upper}_{asset_type or 'unknown'}_{yf_period}"

    cached_data_raw = shared_cache.get_shared_cache(cache_key)
    if cached_data_raw is not None:
        print(
            f"ORCHESTRATOR CACHE HIT (Redis): Using cached history for {symbol.upper()}"
        )
        return _deserialize_history_from_cache(cached_data_raw)

    print(
        f"ORCHESTRATOR: Cache miss for historical data of {symbol_upper} (type: {asset_type}, period: {yf_period}). Trying yfinance."
    )
    history = yf_provider.fetch_yf_historical_data(symbol, asset_type, period=yf_period)

    if history is None and settings.ALPHA_VANTAGE_API_KEY:
        print(
            f"ORCHESTRATOR: yfinance failed for historical {symbol_upper}. Trying AlphaVantage as fallback."
        )
        if asset_type and asset_type.lower() == "crypto":
            base_crypto_symbol = symbol_upper.replace("USDT", "").replace("USD", "")
            if base_crypto_symbol:
                history = av_provider.fetch_av_crypto_historical_data(
                    base_crypto_symbol, outputsize=outputsize
                )
        else:
            history = av_provider.fetch_av_stock_historical_data(
                symbol_upper, outputsize=outputsize
            )

    if history is not None and len(history) > 0:
        shared_cache.set_shared_cache(cache_key, history)
        print(
            f"ORCHESTRATOR: Successfully fetched {len(history)} historical points for {symbol.upper()}. Stored in Redis."
        )
    elif history == []:
        shared_cache.set_shared_cache(cache_key, [])
        print(
            f"ORCHESTRATOR: Fetched empty historical data for {symbol.upper()}. Caching empty list."
        )
    else:
        print(
            f"ORCHESTRATOR: Failed to fetch historical data for {symbol_upper} from all providers."
        )

    return history
