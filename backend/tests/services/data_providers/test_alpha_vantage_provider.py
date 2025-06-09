# backend/tests/services/data_providers/test_alpha_vantage_provider.py
import pytest
from datetime import date
import requests

# Import the specific functions from the alpha_vantage_provider module
from app.services.data_providers import alpha_vantage_provider as av_provider
from app.core.config import settings  # To set API key for tests

# Mock Alpha Vantage API base URL (should match what's in the provider)
MOCK_AV_BASE_URL = av_provider.ALPHA_VANTAGE_BASE_URL


# --- Fixtures ---
@pytest.fixture(autouse=True)
def mock_av_api_key(monkeypatch):
    """Ensure ALPHA_VANTAGE_API_KEY is set in settings for provider tests."""
    monkeypatch.setattr(settings, "ALPHA_VANTAGE_API_KEY", "TEST_AV_KEY")


# --- Mock API Responses (copied/adapted from previous service tests) ---
MOCK_AV_STOCK_GLOBAL_QUOTE_SUCCESS = {
    "Global Quote": {
        "01. symbol": "IBM",
        "05. price": "136.99",
        # Add other fields if the parser uses them, otherwise keep minimal
    }
}
MOCK_AV_CRYPTO_EXCHANGE_RATE_SUCCESS = {
    "Realtime Currency Exchange Rate": {
        "1. From_Currency Code": "ETH",
        "3. To_Currency Code": "USD",
        "5. Exchange Rate": "2050.75",
    }
}
MOCK_AV_STOCK_TIME_SERIES_DAILY_SUCCESS = {
    "Meta Data": {"2. Symbol": "IBM"},
    "Time Series (Daily)": {
        "2023-10-27": {
            "1. open": "136.50",
            "2. high": "137.40",
            "3. low": "135.66",
            "4. close": "136.99",
            "5. volume": "2856020",
        },
        "2023-10-26": {
            "1. open": "134.90",
            "2. high": "136.00",
            "3. low": "134.50",
            "4. close": "135.82",
            "5. volume": "3500000",
        },
    },
}
MOCK_AV_CRYPTO_DIGITAL_CURRENCY_DAILY_SUCCESS = {
    "Meta Data": {"2. Digital Currency Code": "ETH", "4. Market Code": "USD"},
    "Time Series (Digital Currency Daily)": {
        "2023-10-27": {
            "1a. open (USD)": "1800.00",
            "2a. high (USD)": "1850.00",
            "3a. low (USD)": "1790.00",
            "4a. close (USD)": "1830.00",
            "5. volume": "12345.678",
        },
        "2023-10-26": {
            "1a. open (USD)": "1750.00",
            "2a. high (USD)": "1780.00",
            "3a. low (USD)": "1700.00",
            "4a. close (USD)": "1760.00",
            "5. volume": "23456.789",
        },
    },
}
MOCK_AV_API_NOTE_RESPONSE = {
    "Note": "Thank you for using Alpha Vantage! Our standard API call frequency is..."
}
MOCK_AV_API_INFORMATION_RESPONSE = (
    {  # Sometimes "Information" is used for errors/limits
        "Information": "API call frequency is 25 calls per day."
    }
)
MOCK_AV_EMPTY_RESPONSE = {}  # For testing parsing of unexpected empty data


# --- Tests for fetch_av_stock_current_price ---
def test_fetch_av_stock_current_price_success(requests_mock):
    symbol = "IBM"
    expected_price = 136.99
    # Construct expected URL
    url = f"{MOCK_AV_BASE_URL}?apikey={settings.ALPHA_VANTAGE_API_KEY}&function=GLOBAL_QUOTE&symbol={symbol.upper()}"
    requests_mock.get(url, json=MOCK_AV_STOCK_GLOBAL_QUOTE_SUCCESS)

    price = av_provider.fetch_av_stock_current_price(symbol)
    assert price == expected_price


def test_fetch_av_stock_current_price_api_note(requests_mock, capsys):
    symbol = "IBM"
    url = f"{MOCK_AV_BASE_URL}?apikey={settings.ALPHA_VANTAGE_API_KEY}&function=GLOBAL_QUOTE&symbol={symbol.upper()}"
    requests_mock.get(url, json=MOCK_AV_API_NOTE_RESPONSE)

    price = av_provider.fetch_av_stock_current_price(symbol)
    assert price is None
    captured = capsys.readouterr()
    assert "AV_PROVIDER API Note/Info" in captured.out


def test_fetch_av_stock_current_price_parsing_error(requests_mock, capsys):
    symbol = "BADPARSE"
    url = f"{MOCK_AV_BASE_URL}?apikey={settings.ALPHA_VANTAGE_API_KEY}&function=GLOBAL_QUOTE&symbol={symbol.upper()}"
    requests_mock.get(
        url, json={"Global Quote": {"wrong_key": "123"}}
    )  # Missing "05. price"

    price = av_provider.fetch_av_stock_current_price(symbol)
    assert price is None
    captured = capsys.readouterr()
    assert f"AV_PROVIDER Could not parse stock price for {symbol}" in captured.out


# --- Tests for fetch_av_crypto_current_price ---
def test_fetch_av_crypto_current_price_success(requests_mock):
    crypto_symbol = "ETH"
    market = "USD"
    expected_price = 2050.75
    url = f"{MOCK_AV_BASE_URL}?apikey={settings.ALPHA_VANTAGE_API_KEY}&function=CURRENCY_EXCHANGE_RATE&from_currency={crypto_symbol.upper()}&to_currency={market.upper()}"
    requests_mock.get(url, json=MOCK_AV_CRYPTO_EXCHANGE_RATE_SUCCESS)

    price = av_provider.fetch_av_crypto_current_price(
        crypto_symbol, market_currency=market
    )
    assert price == expected_price


def test_fetch_av_crypto_current_price_api_information(
    requests_mock, capsys
):  # Test with "Information" key
    crypto_symbol = "ETH"
    market = "USD"
    url = f"{MOCK_AV_BASE_URL}?apikey={settings.ALPHA_VANTAGE_API_KEY}&function=CURRENCY_EXCHANGE_RATE&from_currency={crypto_symbol.upper()}&to_currency={market.upper()}"
    requests_mock.get(url, json=MOCK_AV_API_INFORMATION_RESPONSE)

    price = av_provider.fetch_av_crypto_current_price(
        crypto_symbol, market_currency=market
    )
    assert price is None
    captured = capsys.readouterr()
    assert "AV_PROVIDER API Note/Info" in captured.out


# --- Tests for fetch_av_stock_historical_data ---
def test_fetch_av_stock_historical_data_success(requests_mock):
    symbol = "IBM"
    outputsize = "compact"
    url = f"{MOCK_AV_BASE_URL}?apikey={settings.ALPHA_VANTAGE_API_KEY}&function=TIME_SERIES_DAILY&symbol={symbol.upper()}&outputsize={outputsize}"
    requests_mock.get(url, json=MOCK_AV_STOCK_TIME_SERIES_DAILY_SUCCESS)

    history = av_provider.fetch_av_stock_historical_data(symbol, outputsize=outputsize)
    assert history is not None
    assert len(history) == 2
    assert history[0]["date"] == date(2023, 10, 26)  # Check sorting
    assert history[1]["close"] == 136.99


def test_fetch_av_stock_historical_data_empty_series(requests_mock, capsys):
    symbol = "EMPTY"
    outputsize = "compact"
    url = f"{MOCK_AV_BASE_URL}?apikey={settings.ALPHA_VANTAGE_API_KEY}&function=TIME_SERIES_DAILY&symbol={symbol.upper()}&outputsize={outputsize}"
    requests_mock.get(
        url, json={"Meta Data": {}, "Time Series (Daily)": {}}
    )  # Empty time series

    history = av_provider.fetch_av_stock_historical_data(symbol, outputsize=outputsize)
    assert (
        history is None
    )  # Or [] depending on provider logic for truly empty series after parsing
    captured = capsys.readouterr()
    # This depends on whether your provider returns None or [] for an empty but valid series object
    # If it returns None:
    assert f"AV_PROVIDER Could not parse stock historical for {symbol}" in captured.out
    # If it returns []:
    # assert history == []


# --- Tests for fetch_av_crypto_historical_data ---
def test_fetch_av_crypto_historical_data_success(requests_mock):
    crypto_symbol = "ETH"
    market = "USD"
    outputsize = (
        "compact"  # Note: Provider might ignore this for AV crypto and truncate later
    )
    url = f"{MOCK_AV_BASE_URL}?apikey={settings.ALPHA_VANTAGE_API_KEY}&function=DIGITAL_CURRENCY_DAILY&symbol={crypto_symbol.upper()}&market={market.upper()}"
    requests_mock.get(url, json=MOCK_AV_CRYPTO_DIGITAL_CURRENCY_DAILY_SUCCESS)

    history = av_provider.fetch_av_crypto_historical_data(
        crypto_symbol, market_currency=market, outputsize=outputsize
    )
    assert history is not None
    assert len(history) == 2
    assert history[0]["date"] == date(2023, 10, 26)
    assert history[1]["close"] == 1830.00


# --- General Provider Tests ---
def test_av_provider_no_api_key(monkeypatch, capsys):
    monkeypatch.setattr(settings, "ALPHA_VANTAGE_API_KEY", None)  # Simulate no API key

    assert av_provider.fetch_av_stock_current_price("ANY") is None
    assert av_provider.fetch_av_crypto_current_price("ANY") is None
    assert av_provider.fetch_av_stock_historical_data("ANY") is None
    assert av_provider.fetch_av_crypto_historical_data("ANY") is None

    captured = capsys.readouterr()
    assert (
        captured.out.count("AV_PROVIDER Warning: ALPHA_VANTAGE_API_KEY not configured.")
        >= 4
    )  # Check for multiple calls


def test_av_provider_network_error(requests_mock, capsys):
    symbol = "NETERROR"
    # Any AV endpoint will do for this test
    url = f"{MOCK_AV_BASE_URL}?apikey={settings.ALPHA_VANTAGE_API_KEY}&function=GLOBAL_QUOTE&symbol={symbol.upper()}"
    requests_mock.get(
        url, exc=requests.exceptions.ConnectionError("Simulated network failure")
    )

    price = av_provider.fetch_av_stock_current_price(symbol)
    assert price is None
    captured = capsys.readouterr()
    assert "AV_PROVIDER Error fetching data" in captured.out
    assert "Simulated network failure" in captured.out
