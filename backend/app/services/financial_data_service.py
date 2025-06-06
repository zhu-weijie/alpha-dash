# app/services/financial_data_service.py
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, date

from app.core.config import settings

ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

def fetch_current_price(symbol: str) -> Optional[float]:
    if not settings.ALPHA_VANTAGE_API_KEY:
        print("Warning: ALPHA_VANTAGE_API_KEY not configured.")
        return None

    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol.upper(),
        "apikey": settings.ALPHA_VANTAGE_API_KEY,
    }
    try:
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        data = response.json()
        
        global_quote = data.get("Global Quote")
        if global_quote and "05. price" in global_quote:
            return float(global_quote["05. price"])
        elif "Note" in data: # Handle API limit note
            print(f"Alpha Vantage API Note for {symbol} (current price): {data['Note']}")
            return None
        else:
            print(f"Could not parse current price for {symbol} from Alpha Vantage: {data}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching current price for {symbol} from Alpha Vantage: {e}")
        return None
    except (ValueError, KeyError) as e: # Handles JSON decoding errors or missing keys
        print(f"Error parsing current price data for {symbol}: {e}")
        return None


def fetch_historical_data(symbol: str, outputsize: str = "compact") -> Optional[List[Dict[str, Any]]]:
    """
    Fetches daily historical data.
    outputsize: "compact" for last 100 days, "full" for full history.
    """
    if not settings.ALPHA_VANTAGE_API_KEY:
        print("Warning: ALPHA_VANTAGE_API_KEY not configured.")
        return None

    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol.upper(),
        "outputsize": outputsize, # "compact" or "full"
        "apikey": settings.ALPHA_VANTAGE_API_KEY,
    }
    try:
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

        time_series = data.get("Time Series (Daily)")
        if time_series:
            processed_data = []
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
                except ValueError:
                    print(f"Skipping malformed data point for {symbol} on {date_str}")
                    continue
            # Sort by date ascending if needed (Alpha Vantage usually returns descending)
            return sorted(processed_data, key=lambda x: x["date"])
        elif "Note" in data: # Handle API limit note
            print(f"Alpha Vantage API Note for {symbol} (historical data): {data['Note']}")
            return None
        else:
            print(f"Could not parse historical data for {symbol} from Alpha Vantage: {data}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching historical data for {symbol} from Alpha Vantage: {e}")
        return None
    except (ValueError, KeyError) as e:
        print(f"Error parsing historical data for {symbol}: {e}")
        return None

# You might need similar functions for crypto if Alpha Vantage's structure is different
# or if you choose a different API like CoinGecko for crypto.
