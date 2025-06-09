# backend/tests/services/data_providers/test_yahoo_finance_provider.py
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from datetime import date

from app.services.data_providers import yahoo_finance_provider as yf_provider


@pytest.fixture
def mock_yf_ticker():
    mock_ticker_instance = MagicMock()
    mock_ticker_instance.history.return_value = pd.DataFrame()
    mock_ticker_instance.info = {}
    with patch(
        "app.services.data_providers.yahoo_finance_provider.yf.Ticker",
        return_value=mock_ticker_instance,
    ) as mock_ticker_class:
        yield mock_ticker_instance, mock_ticker_class


def test_map_symbol_for_yfinance_stock():
    assert yf_provider._map_symbol_for_yfinance("AAPL", "stock") == "AAPL"
    assert yf_provider._map_symbol_for_yfinance("aapl", "stock") == "AAPL"


def test_map_symbol_for_yfinance_crypto():
    assert yf_provider._map_symbol_for_yfinance("BTC", "crypto") == "BTC-USD"
    assert yf_provider._map_symbol_for_yfinance("eth", "crypto") == "ETH-USD"
    assert yf_provider._map_symbol_for_yfinance("XYZ", "crypto") == "XYZ"


def test_map_symbol_for_yfinance_no_type():
    assert yf_provider._map_symbol_for_yfinance("GOOG") == "GOOG"


def test_fetch_yf_current_price_from_history(mock_yf_ticker):
    mock_ticker_instance, _ = mock_yf_ticker
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
    mock_ticker_instance.history.return_value = pd.DataFrame()
    mock_ticker_instance.info = {"regularMarketPrice": 175.50}

    price = yf_provider.fetch_yf_current_price("MSFT", asset_type="stock")
    assert price == 175.50


def test_fetch_yf_current_price_not_found(mock_yf_ticker, capsys):
    mock_ticker_instance, _ = mock_yf_ticker
    mock_ticker_instance.history.return_value = pd.DataFrame()
    mock_ticker_instance.info = {}

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
    mock_ticker_instance.history.return_value = pd.DataFrame()

    history = yf_provider.fetch_yf_historical_data("EMPTY", asset_type="stock")
    assert history is None
    captured = capsys.readouterr()
    assert "YF_PROVIDER: No historical data found" in captured.out


def test_fetch_yf_historical_data_calculates_sma(mock_yf_ticker):
    mock_ticker_instance, _ = mock_yf_ticker
    dates = pd.to_datetime([f"2023-01-{i:02d}" for i in range(1, 25)])
    close_prices = [
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32,
        33,
    ]

    mock_history_df = pd.DataFrame(
        {
            "Open": [p - 0.5 for p in close_prices],
            "High": [p + 0.5 for p in close_prices],
            "Low": [p - 1 for p in close_prices],
            "Close": close_prices,
            "Volume": [1000] * 24,
        },
        index=dates,
    )
    mock_ticker_instance.history.return_value = mock_history_df

    history = yf_provider.fetch_yf_historical_data(
        "SMA_TEST", asset_type="stock", period="1mo"
    )

    assert history is not None
    assert len(history) == 24

    for i in range(19):
        assert history[i]["sma20"] is None, f"SMA20 at index {i} should be None"

    expected_sma20_at_idx19 = sum(close_prices[0:20]) / 20
    assert history[19]["sma20"] == pytest.approx(expected_sma20_at_idx19)
    assert history[19]["date"] == date(2023, 1, 20)

    for item in history:
        assert item["sma50"] is None, "SMA50 should be None with insufficient data"


def test_fetch_yf_historical_data_sma_with_insufficient_data(mock_yf_ticker):
    mock_ticker_instance, _ = mock_yf_ticker
    dates = pd.to_datetime([f"2023-01-{i:02d}" for i in range(1, 10)])
    close_prices = [10, 11, 12, 13, 14, 15, 16, 17, 18]

    mock_history_df = pd.DataFrame(
        {
            "Close": close_prices,
            "Open": close_prices,
            "High": close_prices,
            "Low": close_prices,
            "Volume": [1000] * 9,
        },
        index=dates,
    )
    mock_ticker_instance.history.return_value = mock_history_df

    history = yf_provider.fetch_yf_historical_data("SHORT_HIST", asset_type="stock")
    assert history is not None
    for item in history:
        assert item["sma20"] is None
        assert item["sma50"] is None
