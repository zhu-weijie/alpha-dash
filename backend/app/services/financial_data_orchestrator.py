# app/services/financial_data_orchestrator.py
import time
from typing import List, Dict, Any, Optional

from app.core.config import settings # Only for API key check if needed here
from .data_providers import alpha_vantage_provider as av_provider

# --- Cache Implementation ---
_cache = {"price_cache": {}, "history_cache": {}}
CACHE_DURATION_SECONDS = 15 * 60 # 15 minutes

def _get_from_cache(cache_type: str, key: str) -> Any:
    cache_store = _cache.get(cache_type)
    if cache_store and key in cache_store:
        timestamp, value = cache_store[key]
        if time.time() - timestamp < CACHE_DURATION_SECONDS:
            print(f"ORCHESTRATOR CACHE HIT: Using cached data for {cache_type} - {key}")
            return value
        else:
            print(f"ORCHESTRATOR CACHE EXPIRED: for {cache_type} - {key}")
            del cache_store[key]
    return None

def _set_to_cache(cache_type: str, key: str, value: Any):
    cache_store = _cache.get(cache_type)
    if cache_store is not None and value is not None: # Only cache valid, non-None data
        cache_store[key] = (time.time(), value)
        print(f"ORCHESTRATOR CACHE SET: for {cache_type} - {key}")
# --- End Cache Implementation ---

def get_current_price(symbol: str, asset_type: Optional[str] = None) -> Optional[float]:
    symbol_upper = symbol.upper()
    # Cache key could include asset_type if providers handle same symbol differently based on type
    cache_key = f"{symbol_upper}_{asset_type or 'unknown'}_price"
    
    cached_price = _get_from_cache("price_cache", cache_key)
    if cached_price is not None:
        return cached_price

    print(f"ORCHESTRATOR: Fetching current price for {symbol_upper} (type: {asset_type}) via AlphaVantage")
    price = None
    if asset_type and asset_type.lower() == 'crypto':
        # Assume symbol is base crypto ticker like ETH, BTC
        base_crypto_symbol = symbol_upper.replace("USDT", "").replace("USD", "")
        if base_crypto_symbol: # Make sure it's not empty after stripping
            price = av_provider.fetch_av_crypto_current_price(base_crypto_symbol)
    else: # Assume stock or unknown, try stock endpoint
        price = av_provider.fetch_av_stock_current_price(symbol_upper)
            
    if price is not None:
        _set_to_cache("price_cache", cache_key, price)
    else:
        print(f"ORCHESTRATOR: Failed to fetch current price for {symbol_upper} from AlphaVantage.")
        
    return price

def get_historical_data(symbol: str, asset_type: Optional[str] = None, 
                          outputsize: str = "compact") -> Optional[List[Dict[str, Any]]]:
    symbol_upper = symbol.upper()
    cache_key_suffix = f"_{outputsize}"
    cache_key = f"{symbol_upper}_{asset_type or 'unknown'}{cache_key_suffix}_hist"

    cached_data = _get_from_cache("history_cache", cache_key)
    if cached_data is not None:
        return cached_data

    print(f"ORCHESTRATOR: Fetching historical for {symbol_upper} (type: {asset_type}, size: {outputsize}) via AlphaVantage")
    history = None
    if asset_type and asset_type.lower() == 'crypto':
        base_crypto_symbol = symbol_upper.replace("USDT", "").replace("USD", "")
        if base_crypto_symbol:
            history = av_provider.fetch_av_crypto_historical_data(base_crypto_symbol, outputsize=outputsize)
    else: # Assume stock or unknown
        history = av_provider.fetch_av_stock_historical_data(symbol_upper, outputsize=outputsize)

    if history is not None and len(history) > 0:
        _set_to_cache("history_cache", cache_key, history)
    else:
        print(f"ORCHESTRATOR: Failed to fetch historical data for {symbol_upper} from AlphaVantage.")
        if history == []: # If AV provider returned empty list meaning parsing success but no data points
             _set_to_cache("history_cache", cache_key, []) # Cache empty list to avoid re-fetch
        
    return history
