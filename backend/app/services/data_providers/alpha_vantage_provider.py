# app/services/data_providers/alpha_vantage_provider.py
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, date

from app.core.config import settings # For API Key

ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

def _make_av_request(params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """ Helper function to make Alpha Vantage request and basic error handling. """
    if not settings.ALPHA_VANTAGE_API_KEY:
        print("AV_PROVIDER Warning: ALPHA_VANTAGE_API_KEY not configured.")
        return None
    
    all_params = {"apikey": settings.ALPHA_VANTAGE_API_KEY, **params}
    try:
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=all_params)
        response.raise_for_status()
        data = response.json()
        if "Note" in data or "Information" in data: # Handle API limit/info messages
            note_or_info = data.get("Note", data.get("Information"))
            print(f"AV_PROVIDER API Note/Info for params {params}: {note_or_info}")
            return None # Indicate an issue, not valid data
        return data
    except requests.exceptions.RequestException as e:
        print(f"AV_PROVIDER Error fetching data for params {params}: {e}")
        return None
    except ValueError as e: # JSON decoding error
        print(f"AV_PROVIDER Error decoding JSON for params {params}: {e}")
        return None

def fetch_av_stock_current_price(symbol: str) -> Optional[float]:
    params = {"function": "GLOBAL_QUOTE", "symbol": symbol.upper()}
    data = _make_av_request(params)
    if data:
        global_quote = data.get("Global Quote")
        if global_quote and "05. price" in global_quote:
            try:
                return float(global_quote["05. price"])
            except (ValueError, TypeError):
                print(f"AV_PROVIDER Error parsing stock price for {symbol} from: {global_quote}")
    print(f"AV_PROVIDER Could not parse stock price for {symbol} from: {data}")
    return None

def fetch_av_crypto_current_price(crypto_symbol: str, market_currency: str = "USD") -> Optional[float]:
    params = {
        "function": "CURRENCY_EXCHANGE_RATE",
        "from_currency": crypto_symbol.upper(),
        "to_currency": market_currency.upper()
    }
    data = _make_av_request(params)
    if data:
        rate_data = data.get("Realtime Currency Exchange Rate")
        if rate_data and "5. Exchange Rate" in rate_data:
            try:
                return float(rate_data["5. Exchange Rate"])
            except (ValueError, TypeError):
                 print(f"AV_PROVIDER Error parsing crypto price for {crypto_symbol}/{market_currency} from: {rate_data}")
    print(f"AV_PROVIDER Could not parse crypto price for {crypto_symbol}/{market_currency} from: {data}")
    return None

def fetch_av_stock_historical_data(symbol: str, outputsize: str = "compact") -> Optional[List[Dict[str, Any]]]:
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol.upper(),
        "outputsize": outputsize
    }
    data = _make_av_request(params)
    processed_data = []
    if data:
        time_series = data.get("Time Series (Daily)")
        if time_series:
            for date_str, daily_data in time_series.items():
                try:
                    processed_data.append({
                        "date": datetime.strptime(date_str, "%Y-%m-%d").date(),
                        "open": float(daily_data["1. open"]),
                        "high": float(daily_data["2. high"]),
                        "low": float(daily_data["3. low"]),
                        "close": float(daily_data["4. close"]),
                        "volume": int(daily_data["5. volume"]),
                    })
                except (ValueError, KeyError) as parse_err:
                    print(f"AV_PROVIDER Skipping malformed stock data for {symbol} on {date_str}: {parse_err}")
                    continue
            return sorted(processed_data, key=lambda x: x["date"]) if processed_data else None
    print(f"AV_PROVIDER Could not parse stock historical for {symbol} from: {data}")
    return None

def fetch_av_crypto_historical_data(crypto_symbol: str, market_currency: str = "USD", outputsize: str = "compact") -> Optional[List[Dict[str, Any]]]:
    params = {
        "function": "DIGITAL_CURRENCY_DAILY",
        "symbol": crypto_symbol.upper(),
        "market": market_currency.upper()
    }
    data = _make_av_request(params)
    processed_data = []
    if data:
        time_series = data.get("Time Series (Digital Currency Daily)")
        if time_series:
            for date_str, daily_data in time_series.items():
                try:
                    processed_data.append({
                        "date": datetime.strptime(date_str, "%Y-%m-%d").date(),
                        "open": float(daily_data[f"1a. open ({market_currency.upper()})"]),
                        "high": float(daily_data[f"2a. high ({market_currency.upper()})"]),
                        "low": float(daily_data[f"3a. low ({market_currency.upper()})"]),
                        "close": float(daily_data[f"4a. close ({market_currency.upper()})"]),
                        "volume": float(daily_data["5. volume"]),
                    })
                except (ValueError, KeyError) as parse_err:
                    print(f"AV_PROVIDER Skipping malformed crypto data for {crypto_symbol} on {date_str}: {parse_err}")
                    continue
            
            sorted_data = sorted(processed_data, key=lambda x: x["date"]) if processed_data else []
            if outputsize == "compact" and len(sorted_data) > 100:
                return sorted_data[-100:]
            return sorted_data if sorted_data else None # Return None if list is empty after processing
    print(f"AV_PROVIDER Could not parse crypto historical for {crypto_symbol} from: {data}")
    return None

# Update data_providers/__init__.py
# from . import alpha_vantage_provider
# (This is optional, depends on how you want to import elsewhere)