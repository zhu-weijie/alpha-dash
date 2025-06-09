# backend/tests/services/data_providers/test_yahoo_finance_provider.py
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd  # yfinance returns pandas DataFrames
from datetime import date

from app.services.data_providers import yahoo_finance_provider as yf_provider


# --- Fixture for yfinance.Ticker mock ---
@pytest.fixture
def mock_yf_ticker():
    mock_ticker_instance = MagicMock()
    # Default empty DataFrame for history
    mock_ticker_instance.history.return_value = pd.DataFrame()
    # Default empty dict for info
    mock_ticker_instance.info = {}
    with patch(
        "app.services.data_providers.yahoo_finance_provider.yf.Ticker",
        return_value=mock_ticker_instance,
    ) as mock_ticker_class:
        yield mock_ticker_instance, mock_ticker_class


# --- Tests for _map_symbol_for_yfinance ---
def test_map_symbol_for_yfinance_stock():
    assert yf_provider._map_symbol_for_yfinance("AAPL", "stock") == "AAPL"
    assert yf_provider._map_symbol_for_yfinance("aapl", "stock") == "AAPL"


def test_map_symbol_for_yfinance_crypto():
    assert yf_provider._map_symbol_for_yfinance("BTC", "crypto") == "BTC-USD"
    assert yf_provider._map_symbol_for_yfinance("eth", "crypto") == "ETH-USD"
    assert (
        yf_provider._map_symbol_for_yfinance("XYZ", "crypto") == "XYZ"
    )  # Unknown crypto, returns original


def test_map_symbol_for_yfinance_no_type():
    assert yf_provider._map_symbol_for_yfinance("GOOG") == "GOOG"  # Assumes stock-like


# --- Tests for fetch_yf_current_price ---
def test_fetch_yf_current_price_from_history(mock_yf_ticker):
    mock_ticker_instance, _ = mock_yf_ticker
    # Simulate yf.history() returning a DataFrame with a valid Close price
    mock_history_df = pd.DataFrame(
        {
            "Open": [150.0],
            "High": [152.0],
            "Low": [149.0],
            "Close": [151.25],
            "Volume": [100000],
        },
        index=[pd.Timestamp("2023-10-27")],
    )
    mock_ticker_instance.history.return_value = mock_history_df

    price = yf_provider.fetch_yf_current_price("AAPL", asset_type="stock")
    assert price == 151.25
    mock_ticker_instance.history.assert_called_once_with(period="5d", interval="1d")


def test_fetch_yf_current_price_from_info(mock_yf_ticker):
    mock_ticker_instance, _ = mock_yf_ticker
    mock_ticker_instance.history.return_value = (
        pd.DataFrame()
    )  # Simulate history failing
    mock_ticker_instance.info = {"regularMarketPrice": 175.50}

    price = yf_provider.fetch_yf_current_price("MSFT", asset_type="stock")
    assert price == 175.50


def test_fetch_yf_current_price_not_found(mock_yf_ticker, capsys):
    mock_ticker_instance, _ = mock_yf_ticker
    mock_ticker_instance.history.return_value = pd.DataFrame()
    mock_ticker_instance.info = {}  # No price keys in info

    price = yf_provider.fetch_yf_current_price("NONEXIST", asset_type="stock")
    assert price is None
    captured = capsys.readouterr()
    assert "YF_PROVIDER: Could not determine current price" in captured.out


def test_fetch_yf_current_price_yfinance_exception(mock_yf_ticker, capsys):
    mock_ticker_instance, _ = mock_yf_ticker
    mock_ticker_instance.history.side_effect = Exception("yfinance API error")

    price = yf_provider.fetch_yf_current_price("ERROR", asset_type="stock")
    assert price is None
    captured = capsys.readouterr()
    assert "YF_PROVIDER: Error fetching current price" in captured.out


# --- Tests for fetch_yf_historical_data ---
def test_fetch_yf_historical_data_success(mock_yf_ticker):
    mock_ticker_instance, _ = mock_yf_ticker
    mock_history_df = pd.DataFrame(
        {
            "Open": [150.0, 151.0],
            "High": [152.0, 153.0],
            "Low": [149.0, 150.0],
            "Close": [151.25, 152.50],
            "Volume": [100000, 120000],
        },
        index=[pd.Timestamp("2023-10-26"), pd.Timestamp("2023-10-27")],
    )
    mock_ticker_instance.history.return_value = mock_history_df

    history = yf_provider.fetch_yf_historical_data(
        "AAPL", asset_type="stock", period="1mo"
    )
    assert history is not None
    assert len(history) == 2
    assert history[0]["date"] == date(2023, 10, 26)
    assert history[0]["close"] == 151.25
    assert history[1]["date"] == date(2023, 10, 27)
    assert history[1]["close"] == 152.50
    mock_ticker_instance.history.assert_called_once_with(period="1mo", interval="1d")


def test_fetch_yf_historical_data_empty(mock_yf_ticker, capsys):
    mock_ticker_instance, _ = mock_yf_ticker
    mock_ticker_instance.history.return_value = pd.DataFrame()  # Empty DataFrame

    history = yf_provider.fetch_yf_historical_data("EMPTY", asset_type="stock")
    assert (
        history is None
    )  # Or [] depending on how your provider handles truly empty DF
    captured = capsys.readouterr()
    assert "YF_PROVIDER: No historical data found" in captured.out


# (Add more tests for yfinance exceptions, NaN values in data, etc.)
