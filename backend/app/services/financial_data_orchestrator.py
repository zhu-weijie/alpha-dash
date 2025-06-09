# app/services/financial_data_orchestrator.py
from typing import List, Dict, Any, Optional

from app.core.config import settings
from .data_providers import yahoo_finance_provider as yf_provider
from .data_providers import alpha_vantage_provider as av_provider
from app.cache import shared_cache


_cache = {
    "price_cache": {},
    "history_cache": {}
}
CACHE_DURATION_SECONDS = 15 * 60 


def get_current_price(symbol: str, asset_type: Optional[str] = None) -> Optional[float]:
    symbol_upper = symbol.upper()
    cache_key = f"price:{symbol_upper}_{asset_type or 'unknown'}"
    
    cached_price = shared_cache.get_shared_cache(cache_key)
    if cached_price is not None:
        print(f"ORCHESTRATOR CACHE HIT (Redis): Using cached price for {symbol_upper}")
        return float(cached_price)

    print(f"ORCHESTRATOR: Cache miss for current price of {symbol_upper} (type: {asset_type}). Trying yfinance.")
    price = yf_provider.fetch_yf_current_price(symbol, asset_type)

    if price is None and settings.ALPHA_VANTAGE_API_KEY:
        print(f"ORCHESTRATOR: yfinance failed for current price of {symbol_upper}. Trying AlphaVantage as fallback.")
        if asset_type and asset_type.lower() == 'crypto':
            base_crypto_symbol = symbol_upper.replace("USDT", "").replace("USD", "")
            if base_crypto_symbol:
                price = av_provider.fetch_av_crypto_current_price(base_crypto_symbol)
        else:
            price = av_provider.fetch_av_stock_current_price(symbol_upper)
            
    if price is not None:
        shared_cache.set_shared_cache(cache_key, price)
        print(f"ORCHESTRATOR: Successfully fetched current price for {symbol_upper}: {price}. Stored in Redis.")
    else:
        print(f"ORCHESTRATOR: Failed to fetch current price for {symbol_upper} from all providers.")
        
    return price


def get_historical_data(symbol: str, asset_type: Optional[str] = None, 
                          outputsize: str = "compact") -> Optional[List[Dict[str, Any]]]:
    symbol_upper = symbol.upper()
    period_map = {"compact": "3mo", "full": "max"}
    yf_period = period_map.get(outputsize, "3mo")
    cache_key = f"history:{symbol_upper}_{asset_type or 'unknown'}_{yf_period}"

    cached_data = shared_cache.get_shared_cache(cache_key)
    if cached_data is not None:
        print(f"ORCHESTRATOR CACHE HIT (Redis): Using cached history for {symbol_upper}")
        return cached_data

    print(f"ORCHESTRATOR: Cache miss for historical data of {symbol_upper} (type: {asset_type}, period: {yf_period}). Trying yfinance.")
    history = yf_provider.fetch_yf_historical_data(symbol, asset_type, period=yf_period)

    if history is None and settings.ALPHA_VANTAGE_API_KEY:
        print(f"ORCHESTRATOR: yfinance failed for historical {symbol_upper}. Trying AlphaVantage as fallback.")
        if asset_type and asset_type.lower() == 'crypto':
            base_crypto_symbol = symbol_upper.replace("USDT", "").replace("USD", "")
            if base_crypto_symbol:
                history = av_provider.fetch_av_crypto_historical_data(base_crypto_symbol, outputsize=outputsize)
        else:
            history = av_provider.fetch_av_stock_historical_data(symbol_upper, outputsize=outputsize)

    if history is not None:
        shared_cache.set_shared_cache(cache_key, history) 
        print(f"ORCHESTRATOR: Successfully fetched historical data for {symbol_upper}. Stored in Redis.")
    else:
        print(f"ORCHESTRATOR: Failed to fetch historical data for {symbol_upper} from all providers.")
        
    return history
