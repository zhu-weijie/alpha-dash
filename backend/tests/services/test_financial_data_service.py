# backend/tests/services/test_financial_data_service.py
import pytest
import requests_mock # For mocking HTTP requests
import requests # For actual HTTP requests
from datetime import date, datetime

from app.services import financial_data_service as fds
from app.core.config import settings # To potentially override API key for tests

# Sample successful Alpha Vantage responses
MOCK_GLOBAL_QUOTE_SUCCESS = {
    "Global Quote": {
        "01. symbol": "IBM",
        "02. open": "136.5000",
        "03. high": "137.4000",
        "04. low": "135.6600",
        "05. price": "136.9900", # This is what we want
        "06. volume": "2856020",
        "07. latest trading day": "2023-10-27",
        "08. previous close": "135.8200",
        "09. change": "1.1700",
        "10. change percent": "0.8614%"
    }
}

MOCK_TIME_SERIES_DAILY_SUCCESS = {
    "Meta Data": {
        "1. Information": "Daily Prices (open, high, low, close) and Volumes",
        "2. Symbol": "IBM",
        "3. Last Refreshed": "2023-10-27",
        "4. Output Size": "Compact",
        "5. Time Zone": "US/Eastern"
    },
    "Time Series (Daily)": {
        "2023-10-27": {
            "1. open": "136.50",
            "2. high": "137.40",
            "3. low": "135.66",
            "4. close": "136.99",
            "5. volume": "2856020"
        },
        "2023-10-26": {
            "1. open": "134.90",
            "2. high": "136.00",
            "3. low": "134.50",
            "4. close": "135.82",
            "5. volume": "3500000"
        }
    }
}

MOCK_ALPHA_VANTAGE_RATE_LIMIT_NOTE = {
    "Note": "Thank you for using Alpha Vantage! Our standard API call frequency is X calls per minute and Y calls per day..."
}


@pytest.fixture(autouse=True)
def mock_settings_api_key(monkeypatch):
    """Ensure API key is set for tests to prevent early exit."""
    monkeypatch.setattr(settings, "ALPHA_VANTAGE_API_KEY", "TEST_API_KEY_FOR_PYTEST")


# --- Tests for fetch_current_price ---
def test_fetch_current_price_success(requests_mock):
    symbol = "IBM"
    expected_price = 136.99
    requests_mock.get(
        f"{fds.ALPHA_VANTAGE_BASE_URL}?function=GLOBAL_QUOTE&symbol={symbol.upper()}&apikey={settings.ALPHA_VANTAGE_API_KEY}",
        json=MOCK_GLOBAL_QUOTE_SUCCESS
    )
    
    price = fds.fetch_current_price(symbol)
    assert price == expected_price

def test_fetch_current_price_api_note(requests_mock, capsys): # capsys to capture print
    symbol = "IBM"
    requests_mock.get(
        f"{fds.ALPHA_VANTAGE_BASE_URL}?function=GLOBAL_QUOTE&symbol={symbol.upper()}&apikey={settings.ALPHA_VANTAGE_API_KEY}",
        json=MOCK_ALPHA_VANTAGE_RATE_LIMIT_NOTE
    )
    
    price = fds.fetch_current_price(symbol)
    assert price is None
    captured = capsys.readouterr()
    assert "Alpha Vantage API Note" in captured.out # Check if the warning was printed

def test_fetch_current_price_key_error(requests_mock, capsys):
    symbol = "IBM"
    malformed_response = {"Global Quote": {"unexpected_key": "123.45"}}
    requests_mock.get(
        f"{fds.ALPHA_VANTAGE_BASE_URL}?function=GLOBAL_QUOTE&symbol={symbol.upper()}&apikey={settings.ALPHA_VANTAGE_API_KEY}",
        json=malformed_response
    )
    price = fds.fetch_current_price(symbol)
    assert price is None
    captured = capsys.readouterr()
    assert "Error parsing current price data" in captured.out

def test_fetch_current_price_request_exception(requests_mock, capsys):
    symbol = "IBM"
    requests_mock.get(
        f"{fds.ALPHA_VANTAGE_BASE_URL}?function=GLOBAL_QUOTE&symbol={symbol.upper()}&apikey={settings.ALPHA_VANTAGE_API_KEY}",
        exc=requests.exceptions.ConnectTimeout # Simulate a network error
    )
    price = fds.fetch_current_price(symbol)
    assert price is None
    captured = capsys.readouterr()
    assert "Error fetching current price" in captured.out


# --- Tests for fetch_historical_data ---
def test_fetch_historical_data_success(requests_mock):
    symbol = "IBM"
    outputsize = "compact"
    requests_mock.get(
        f"{fds.ALPHA_VANTAGE_BASE_URL}?function=TIME_SERIES_DAILY&symbol={symbol.upper()}&outputsize={outputsize}&apikey={settings.ALPHA_VANTAGE_API_KEY}",
        json=MOCK_TIME_SERIES_DAILY_SUCCESS
    )
    
    history = fds.fetch_historical_data(symbol, outputsize=outputsize)
    assert history is not None
    assert len(history) == 2
    assert history[0]["date"] == date(2023, 10, 26) # Check sorting
    assert history[0]["close"] == 135.82
    assert history[1]["date"] == date(2023, 10, 27)
    assert history[1]["close"] == 136.99

def test_fetch_historical_data_api_note(requests_mock, capsys):
    symbol = "IBM"
    outputsize = "compact"
    requests_mock.get(
        f"{fds.ALPHA_VANTAGE_BASE_URL}?function=TIME_SERIES_DAILY&symbol={symbol.upper()}&outputsize={outputsize}&apikey={settings.ALPHA_VANTAGE_API_KEY}",
        json=MOCK_ALPHA_VANTAGE_RATE_LIMIT_NOTE
    )
    history = fds.fetch_historical_data(symbol, outputsize=outputsize)
    assert history is None
    captured = capsys.readouterr()
    assert "Alpha Vantage API Note" in captured.out

def test_fetch_historical_data_malformed_date(requests_mock, capsys):
    symbol = "IBM"
    outputsize = "compact"
    mock_response_malformed_date = {
        "Time Series (Daily)": {
            "NOT_A_DATE": { # Malformed date string
                "1. open": "136.50", "2. high": "137.40", 
                "3. low": "135.66", "4. close": "136.99", "5. volume": "2856020"
            },
             "2023-10-26": {
                "1. open": "134.90", "2. high": "136.00",
                "3. low": "134.50", "4. close": "135.82", "5. volume": "3500000"
            }
        }
    }
    requests_mock.get(
         f"{fds.ALPHA_VANTAGE_BASE_URL}?function=TIME_SERIES_DAILY&symbol={symbol.upper()}&outputsize={outputsize}&apikey={settings.ALPHA_VANTAGE_API_KEY}",
        json=mock_response_malformed_date
    )
    history = fds.fetch_historical_data(symbol, outputsize=outputsize)
    assert history is not None
    assert len(history) == 1 # Malformed date should be skipped
    assert history[0]["date"] == date(2023, 10, 26)
    captured = capsys.readouterr()
    assert f"Skipping malformed data point for {symbol} on NOT_A_DATE" in captured.out

def test_no_api_key_configured(monkeypatch, capsys):
    # Temporarily remove the API key for this test
    monkeypatch.setattr(settings, "ALPHA_VANTAGE_API_KEY", None)
    
    price = fds.fetch_current_price("ANY")
    assert price is None
    history = fds.fetch_historical_data("ANY")
    assert history is None
    
    captured = capsys.readouterr()
    # Check that the warning was printed twice
    assert captured.out.count("Warning: ALPHA_VANTAGE_API_KEY not configured.") == 2
