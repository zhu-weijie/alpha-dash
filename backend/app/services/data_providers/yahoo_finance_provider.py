# app/services/data_providers/yahoo_finance_provider.py
import yfinance as yf
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import date


def _map_symbol_for_yfinance(symbol: str, asset_type: Optional[str] = None) -> str:
    """Maps internal symbol to yfinance-compatible ticker."""
    symbol_upper = symbol.upper()
    if asset_type and asset_type.lower() == "crypto":
        known_crypto_bases = [
            "BTC",
            "ETH",
            "SOL",
            "XRP",
            "ADA",
            "DOGE",
            "LTC",
            "BCH",
            "DOT",
            "LINK",
        ]
        if symbol_upper in known_crypto_bases:
            return f"{symbol_upper}-USD"
        base_symbol = symbol_upper.replace("-USD", "").replace("USD", "")
        if base_symbol in known_crypto_bases:
            return f"{base_symbol}-USD"
    return symbol_upper


def fetch_yf_current_price(
    symbol: str, asset_type: Optional[str] = None
) -> Optional[float]:
    yf_symbol = _map_symbol_for_yfinance(symbol, asset_type)
    print(
        f"YF_PROVIDER: Attempting to fetch current price for yf_symbol '{yf_symbol}' (original: '{symbol}')"
    )
    try:
        ticker = yf.Ticker(yf_symbol)
        data = ticker.history(period="5d", interval="1d")
        if not data.empty and "Close" in data and len(data["Close"]) > 0:
            for price_val in reversed(data["Close"].values):
                if price_val == price_val:
                    return float(price_val)
            print(
                f"YF_PROVIDER: Found history for {yf_symbol} but all recent closes were NaN."
            )

        print(
            f"YF_PROVIDER: history call failed for {yf_symbol}, trying ticker.info..."
        )
        info = ticker.info
        price_keys = [
            "regularMarketPrice",
            "currentPrice",
            "previousClose",
            "bid",
            "ask",
            "open",
        ]
        for key in price_keys:
            if info.get(key) is not None:
                return float(info[key])

        print(
            f"YF_PROVIDER: Could not determine current price for {yf_symbol} from history or info. Info: {info}"
        )
        return None
    except Exception as e:
        print(
            f"YF_PROVIDER: Error fetching current price for yf_symbol '{yf_symbol}': {e}"
        )
        return None


def fetch_yf_historical_data(
    symbol: str,
    asset_type: Optional[str] = None,
    period: str = "1mo",
    interval: str = "1d",
) -> Optional[List[Dict[str, Any]]]:
    yf_symbol = _map_symbol_for_yfinance(symbol, asset_type)
    print(
        f"YF_PROVIDER: Attempting to fetch historical for yf_symbol '{yf_symbol}' (original: '{symbol}') period: {period}"
    )
    try:
        ticker = yf.Ticker(yf_symbol)
        hist_df = ticker.history(period=period, interval=interval)

        if hist_df.empty:
            print(
                f"YF_PROVIDER: No historical data found for {yf_symbol} with period {period}."
            )
            return None

        if len(hist_df) >= 20:
            hist_df["sma20"] = hist_df["Close"].rolling(window=20).mean()
        else:
            hist_df["sma20"] = None

        if len(hist_df) >= 50:
            hist_df["sma50"] = hist_df["Close"].rolling(window=50).mean()
        else:
            hist_df["sma50"] = None

        processed_data = []
        for date_index, row in hist_df.iterrows():
            dt_date = (
                date_index.date()
                if hasattr(date_index, "date")
                else date.fromisoformat(str(date_index).split(" ")[0])
            )

            sma20_val = float(row["sma20"]) if pd.notna(row.get("sma20")) else None
            sma50_val = float(row["sma50"]) if pd.notna(row.get("sma50")) else None

            if any(
                pd.isna(row.get(col))
                for col in ["Open", "High", "Low", "Close", "Volume"]
            ):
                print(
                    f"YF_PROVIDER: Skipping data point for {yf_symbol} on {dt_date} due to NaN in OHLCV."
                )
                continue

            processed_data.append(
                {
                    "date": dt_date,
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]),
                    "sma20": sma20_val,
                    "sma50": sma50_val,
                }
            )
        return processed_data if processed_data else None
    except Exception as e:
        print(
            f"YF_PROVIDER: Error fetching/processing historical data for yf_symbol '{yf_symbol}': {e}"
        )
        return None
