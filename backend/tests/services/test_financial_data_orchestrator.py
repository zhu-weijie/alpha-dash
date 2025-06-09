# backend/tests/services/test_financial_data_orchestrator.py
import pytest
import time
from unittest.mock import patch, MagicMock
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timezone
from app.core.config import settings

from app.services import financial_data_orchestrator as orchestrator 

@pytest.fixture(autouse=True)
def clear_orchestrator_cache():
    """Clears the orchestrator's cache before each test."""
    orchestrator._cache["price_cache"].clear()
    orchestrator._cache["history_cache"].clear()


@patch("app.services.financial_data_orchestrator.shared_cache.set_shared_cache")
@patch("app.services.financial_data_orchestrator.shared_cache.get_shared_cache")
@patch("app.services.data_providers.alpha_vantage_provider.fetch_av_stock_current_price") 
@patch("app.services.data_providers.yahoo_finance_provider.fetch_yf_current_price")
def test_get_current_price_stock_cache_miss_then_hit(
    mock_fetch_yf_stock_price: MagicMock,
    mock_fetch_av_stock_price: MagicMock,
    mock_get_shared_cache: MagicMock,
    mock_set_shared_cache: MagicMock,
    monkeypatch
):
    monkeypatch.setattr(settings, "ALPHA_VANTAGE_API_KEY", "DUMMY_KEY_FOR_TEST_AV")
    
    symbol = "AAPL"
    asset_type = "stock"
    expected_yf_price = 150.75 

    cache_key = f"price:{symbol.upper()}_{asset_type or 'unknown'}" 

    mock_get_shared_cache.return_value = None
    mock_fetch_yf_stock_price.return_value = expected_yf_price
    mock_fetch_av_stock_price.return_value = 999.99 

    print(f"\nDEBUG Orchestrator Test: Stock Price - Calling get_current_price for {symbol} (1st time)")
    price1 = orchestrator.get_current_price(symbol, asset_type)
    
    assert price1 == expected_yf_price, "Price should come from yfinance provider"
    
    mock_get_shared_cache.assert_called_once_with(cache_key)
    mock_fetch_yf_stock_price.assert_called_once_with(symbol, asset_type)
    mock_fetch_av_stock_price.assert_not_called()
    mock_set_shared_cache.assert_called_once_with(cache_key, expected_yf_price)

    mock_get_shared_cache.reset_mock()
    mock_set_shared_cache.reset_mock()
    mock_fetch_yf_stock_price.reset_mock()
    mock_fetch_av_stock_price.reset_mock()

    mock_get_shared_cache.return_value = expected_yf_price 

    print(f"DEBUG Orchestrator Test: Stock Price - Calling get_current_price for {symbol} (2nd time)")
    price2 = orchestrator.get_current_price(symbol, asset_type)

    assert price2 == expected_yf_price, "Price should come from shared_cache"
    
    mock_get_shared_cache.assert_called_once_with(cache_key)
    mock_fetch_yf_stock_price.assert_not_called()
    mock_fetch_av_stock_price.assert_not_called()
    mock_set_shared_cache.assert_not_called()


@patch("app.services.financial_data_orchestrator.shared_cache.set_shared_cache")
@patch("app.services.financial_data_orchestrator.shared_cache.get_shared_cache")
@patch("app.services.data_providers.alpha_vantage_provider.fetch_av_crypto_current_price")
@patch("app.services.data_providers.yahoo_finance_provider.fetch_yf_current_price")
def test_get_current_price_crypto_cache_miss_then_hit(
    mock_fetch_yf_crypto_price: MagicMock,
    mock_fetch_av_crypto_price: MagicMock,
    mock_get_shared_cache: MagicMock,
    mock_set_shared_cache: MagicMock,
    monkeypatch
):
    monkeypatch.setattr(settings, "ALPHA_VANTAGE_API_KEY", "DUMMY_KEY_FOR_TEST_AV")
    
    symbol = "ETH"
    asset_type = "crypto"
    expected_yf_price = 2500.75
    cache_key = f"price:{symbol.upper()}_{asset_type or 'unknown'}"

    mock_get_shared_cache.return_value = None 
    mock_fetch_yf_crypto_price.return_value = expected_yf_price
    mock_fetch_av_crypto_price.return_value = 9999.99

    print(f"\nDEBUG Orchestrator Test: Calling get_current_price for {symbol} (1st time, expect shared_cache miss)")
    price1 = orchestrator.get_current_price(symbol, asset_type)
    
    assert price1 == expected_yf_price
    mock_get_shared_cache.assert_called_once_with(cache_key)
    mock_fetch_yf_crypto_price.assert_called_once_with(symbol, asset_type)
    mock_fetch_av_crypto_price.assert_not_called()
    mock_set_shared_cache.assert_called_once_with(cache_key, expected_yf_price)

    mock_get_shared_cache.reset_mock()
    mock_set_shared_cache.reset_mock()
    mock_fetch_yf_crypto_price.reset_mock()
    mock_fetch_av_crypto_price.reset_mock()

    mock_get_shared_cache.return_value = expected_yf_price 

    print(f"DEBUG Orchestrator Test: Calling get_current_price for {symbol} (2nd time, expect shared_cache hit)")
    price2 = orchestrator.get_current_price(symbol, asset_type)

    assert price2 == expected_yf_price
    mock_get_shared_cache.assert_called_once_with(cache_key)
    mock_fetch_yf_crypto_price.assert_not_called()
    mock_fetch_av_crypto_price.assert_not_called()
    mock_set_shared_cache.assert_not_called()


@patch("app.services.data_providers.alpha_vantage_provider.fetch_av_stock_current_price")
@patch("app.services.data_providers.yahoo_finance_provider.fetch_yf_current_price")
def test_get_current_price_provider_returns_none(
    mock_fetch_yf_stock_price: MagicMock,
    mock_fetch_av_stock_price: MagicMock,
    monkeypatch
):
    monkeypatch.setattr(settings, "ALPHA_VANTAGE_API_KEY", "DUMMY_KEY_FOR_TEST_AV")
    
    symbol = "FAIL"
    asset_type = "stock"

    mock_fetch_yf_stock_price.return_value = None
    mock_fetch_av_stock_price.return_value = None

    price = orchestrator.get_current_price(symbol, asset_type)
    
    assert price is None, "Price should be None if all providers fail"
    
    mock_fetch_yf_stock_price.assert_called_once_with(symbol, asset_type)
    
    mock_fetch_av_stock_price.assert_called_once_with(symbol.upper())
    
    cache_key = f"{symbol.upper()}_{asset_type or 'unknown'}_price"
    assert cache_key not in orchestrator._cache["price_cache"], "None should not be cached for price"


@patch("app.services.financial_data_orchestrator.shared_cache.set_shared_cache")
@patch("app.services.financial_data_orchestrator.shared_cache.get_shared_cache")
@patch("app.services.data_providers.alpha_vantage_provider.fetch_av_stock_current_price")
@patch("app.services.data_providers.yahoo_finance_provider.fetch_yf_current_price")
def test_get_current_price_yf_succeeds_av_not_called(
    mock_fetch_yf_stock_price: MagicMock,
    mock_fetch_av_stock_price: MagicMock,
    mock_get_shared_cache: MagicMock,
    mock_set_shared_cache: MagicMock,
    monkeypatch
):
    monkeypatch.setattr(settings, "ALPHA_VANTAGE_API_KEY", "DUMMY_KEY_FOR_TEST_AV")
    symbol = "MSFT"
    asset_type = "stock"
    expected_price = 400.00
    cache_key = f"price:{symbol.upper()}_{asset_type or 'unknown'}"

    mock_get_shared_cache.return_value = None
    mock_fetch_yf_stock_price.return_value = expected_price

    print(f"\nDEBUG Orchestrator Test: YF Succeeds - Calling get_current_price for {symbol}")
    price = orchestrator.get_current_price(symbol, asset_type)
    assert price == expected_price
    
    mock_get_shared_cache.assert_called_once_with(cache_key)
    
    mock_fetch_yf_stock_price.assert_called_once_with(symbol, asset_type)
    
    mock_fetch_av_stock_price.assert_not_called()
    
    mock_set_shared_cache.assert_called_once_with(cache_key, expected_price)



@patch("app.services.financial_data_orchestrator.shared_cache.set_shared_cache")
@patch("app.services.financial_data_orchestrator.shared_cache.get_shared_cache")
@patch("app.services.data_providers.alpha_vantage_provider.fetch_av_stock_current_price")
@patch("app.services.data_providers.yahoo_finance_provider.fetch_yf_current_price")
def test_get_current_price_yf_fails_av_succeeds(
    mock_fetch_yf_stock_price: MagicMock,
    mock_fetch_av_stock_price: MagicMock,
    mock_get_shared_cache: MagicMock,
    mock_set_shared_cache: MagicMock,
    monkeypatch
):
    monkeypatch.setattr(settings, "ALPHA_VANTAGE_API_KEY", "DUMMY_KEY_FOR_TEST_AV")
    symbol = "GOOG"
    asset_type = "stock"
    expected_av_price = 150.00
    cache_key = f"price:{symbol.upper()}_{asset_type or 'unknown'}"

    mock_get_shared_cache.return_value = None
    mock_fetch_yf_stock_price.return_value = None
    mock_fetch_av_stock_price.return_value = expected_av_price

    print(f"\nDEBUG Orchestrator Test: YF Fails, AV Succeeds - Calling get_current_price for {symbol}")
    price = orchestrator.get_current_price(symbol, asset_type)

    assert price == expected_av_price
    
    mock_get_shared_cache.assert_called_once_with(cache_key)

    mock_fetch_yf_stock_price.assert_called_once_with(symbol, asset_type)
    
    mock_fetch_av_stock_price.assert_called_once_with(symbol.upper()) 
    
    mock_set_shared_cache.assert_called_once_with(cache_key, expected_av_price)


@patch("app.services.financial_data_orchestrator.shared_cache.set_shared_cache")
@patch("app.services.financial_data_orchestrator.shared_cache.get_shared_cache")
@patch("app.services.data_providers.alpha_vantage_provider.fetch_av_stock_current_price")
@patch("app.services.data_providers.yahoo_finance_provider.fetch_yf_current_price")
def test_get_current_price_cache_expiration(
    mock_fetch_yf_stock_price: MagicMock,
    mock_fetch_av_stock_price: MagicMock,
    mock_get_shared_cache: MagicMock,
    mock_set_shared_cache: MagicMock,
    monkeypatch
):
    monkeypatch.setattr(settings, "ALPHA_VANTAGE_API_KEY", "DUMMY_KEY_FOR_TEST_AV")
    
    original_cache_duration = orchestrator.CACHE_DURATION_SECONDS
    monkeypatch.setattr("app.cache.shared_cache.CACHE_DURATION_SECONDS", 0.05)
    monkeypatch.setattr(orchestrator, "CACHE_DURATION_SECONDS", 0.05)


    symbol = "EXP"
    asset_type = "stock"
    mock_price_call_1 = 100.00
    mock_price_call_2 = 101.00 # Price after cache expiry
    cache_key = f"price:{symbol.upper()}_{asset_type or 'unknown'}"

    mock_get_shared_cache.return_value = None
    mock_fetch_yf_stock_price.return_value = mock_price_call_1
    mock_fetch_av_stock_price.return_value = 999.99

    print(f"\nDEBUG Orchestrator Test: Cache Expiration - Calling get_current_price for {symbol} (1st time)")
    price1 = orchestrator.get_current_price(symbol, asset_type)
    
    assert price1 == mock_price_call_1
    mock_get_shared_cache.assert_called_once_with(cache_key)
    mock_fetch_yf_stock_price.assert_called_once_with(symbol, asset_type)
    mock_fetch_av_stock_price.assert_not_called()
    mock_set_shared_cache.assert_called_once_with(cache_key, mock_price_call_1)


    mock_get_shared_cache.reset_mock()
    mock_set_shared_cache.reset_mock()
    mock_fetch_yf_stock_price.reset_mock()

    mock_get_shared_cache.return_value = None
    mock_fetch_yf_stock_price.return_value = mock_price_call_2

    time.sleep(0.1) 

    print(f"DEBUG Orchestrator Test: Cache Expiration - Calling get_current_price for {symbol} (2nd time after expiry)")
    price2 = orchestrator.get_current_price(symbol, asset_type)
    
    assert price2 == mock_price_call_2
    
    mock_get_shared_cache.assert_called_once_with(cache_key)
    mock_fetch_yf_stock_price.assert_called_once_with(symbol, asset_type)
    mock_fetch_av_stock_price.assert_not_called()
    mock_set_shared_cache.assert_called_once_with(cache_key, mock_price_call_2)
    
    monkeypatch.setattr(orchestrator, "CACHE_DURATION_SECONDS", original_cache_duration)
    monkeypatch.setattr("app.cache.shared_cache.CACHE_DURATION_SECONDS", original_cache_duration)


# pytest -vv -k "test_get_historical_data_stock_cache_miss_then_hit" tests/services/test_financial_data_orchestrator.py
@patch("app.services.financial_data_orchestrator.shared_cache.set_shared_cache")
@patch("app.services.financial_data_orchestrator.shared_cache.get_shared_cache")
@patch("app.services.data_providers.alpha_vantage_provider.fetch_av_stock_historical_data")
@patch("app.services.data_providers.yahoo_finance_provider.fetch_yf_historical_data")
def test_get_historical_data_stock_cache_miss_then_hit(
    mock_fetch_yf_stock_hist: MagicMock,
    mock_fetch_av_stock_hist: MagicMock,
    mock_get_shared_cache: MagicMock,
    mock_set_shared_cache: MagicMock,
    monkeypatch
):
    monkeypatch.setattr(settings, "ALPHA_VANTAGE_API_KEY", "DUMMY_KEY_FOR_TEST_AV")
    
    symbol = "MSFT"
    asset_type = "stock"
    outputsize = "compact"
    yf_period_expected = "3mo"
    cache_key = f"history:{symbol.upper()}_{asset_type or 'unknown'}_{yf_period_expected}"


    mock_hist_data_from_yf = [{"date": date(2023, 1, 1), "close": 250.0, "open": 248.0, "high": 252.0, "low": 247.0, "volume": 10000}]
    
    mock_get_shared_cache.return_value = None
    mock_fetch_yf_stock_hist.return_value = mock_hist_data_from_yf
    mock_fetch_av_stock_hist.return_value = [{"date": date(2022, 1, 1), "close": 999.0}]

    print(f"\nDEBUG Orchestrator Test: Hist Stock - Calling get_historical_data for {symbol} (1st time)")
    hist1 = orchestrator.get_historical_data(symbol, asset_type, outputsize)
    
    assert hist1 == mock_hist_data_from_yf
    mock_get_shared_cache.assert_called_once_with(cache_key)
    mock_fetch_yf_stock_hist.assert_called_once_with(symbol, asset_type, period=yf_period_expected)
    mock_fetch_av_stock_hist.assert_not_called()
    mock_set_shared_cache.assert_called_once_with(cache_key, mock_hist_data_from_yf)


    mock_get_shared_cache.reset_mock()
    mock_set_shared_cache.reset_mock()
    mock_fetch_yf_stock_hist.reset_mock()
    mock_fetch_av_stock_hist.reset_mock()

    mock_get_shared_cache.return_value = [{"date": "2023-01-01", "close": 250.0, "open": 248.0, "high": 252.0, "low": 247.0, "volume": 10000}]

    print(f"DEBUG Orchestrator Test: Hist Stock - Calling get_historical_data for {symbol} (2nd time)")
    hist2 = orchestrator.get_historical_data(symbol, asset_type, outputsize)
    
    assert hist2 == mock_hist_data_from_yf
    mock_get_shared_cache.assert_called_once_with(cache_key)
    mock_fetch_yf_stock_hist.assert_not_called()
    mock_fetch_av_stock_hist.assert_not_called()
    mock_set_shared_cache.assert_not_called()


@patch("app.services.financial_data_orchestrator.shared_cache.set_shared_cache")
@patch("app.services.financial_data_orchestrator.shared_cache.get_shared_cache")
@patch("app.services.data_providers.alpha_vantage_provider.fetch_av_crypto_historical_data")
@patch("app.services.data_providers.yahoo_finance_provider.fetch_yf_historical_data")
def test_get_historical_data_crypto_cache_miss_then_hit(
    mock_fetch_yf_crypto_hist: MagicMock,
    mock_fetch_av_crypto_hist: MagicMock,
    mock_get_shared_cache: MagicMock,
    mock_set_shared_cache: MagicMock,
    monkeypatch
):
    monkeypatch.setattr(settings, "ALPHA_VANTAGE_API_KEY", "DUMMY_KEY_FOR_TEST_AV")
    
    symbol = "BTC" 
    asset_type = "crypto"
    outputsize = "compact" 
    yf_period_expected = "3mo"
    cache_key = f"history:{symbol.upper()}_{asset_type or 'unknown'}_{yf_period_expected}"


    mock_hist_data_from_yf = [{"date": date(2023, 1, 5), "close": 30000.0, "open": 29000.0, "high": 31000.0, "low": 28000.0, "volume": 12345.0}]
    
    mock_cached_data_with_strings = [{"date": "2023-01-05", "close": 30000.0, "open": 29000.0, "high": 31000.0, "low": 28000.0, "volume": 12345.0}]

    mock_get_shared_cache.return_value = None
    mock_fetch_yf_crypto_hist.return_value = mock_hist_data_from_yf
    mock_fetch_av_crypto_hist.return_value = [{"date": date(2022, 1, 5), "close": 99999.0}]

    print(f"\nDEBUG Orchestrator Test: Hist Crypto - Calling get_historical_data for {symbol} (1st time)")
    hist1 = orchestrator.get_historical_data(symbol, asset_type, outputsize)
    
    assert hist1 == mock_hist_data_from_yf
    mock_get_shared_cache.assert_called_once_with(cache_key)
    mock_fetch_yf_crypto_hist.assert_called_once_with(symbol, asset_type, period=yf_period_expected)
    mock_fetch_av_crypto_hist.assert_not_called()
    mock_set_shared_cache.assert_called_once_with(cache_key, mock_hist_data_from_yf)


    mock_get_shared_cache.reset_mock()
    mock_set_shared_cache.reset_mock()
    mock_fetch_yf_crypto_hist.reset_mock()
    mock_fetch_av_crypto_hist.reset_mock()

    mock_get_shared_cache.return_value = mock_cached_data_with_strings

    print(f"DEBUG Orchestrator Test: Hist Crypto - Calling get_historical_data for {symbol} (2nd time)")
    hist2 = orchestrator.get_historical_data(symbol, asset_type, outputsize)
    
    assert hist2 == mock_hist_data_from_yf 
    
    mock_get_shared_cache.assert_called_once_with(cache_key)
    mock_fetch_yf_crypto_hist.assert_not_called()
    mock_fetch_av_crypto_hist.assert_not_called()
    mock_set_shared_cache.assert_not_called()


@patch("app.services.data_providers.alpha_vantage_provider.fetch_av_stock_historical_data")
@patch("app.services.data_providers.yahoo_finance_provider.fetch_yf_historical_data")
def test_get_historical_data_provider_returns_none(
    mock_fetch_yf_stock_hist: MagicMock,
    mock_fetch_av_stock_hist: MagicMock,
    monkeypatch
):
    monkeypatch.setattr(settings, "ALPHA_VANTAGE_API_KEY", "DUMMY_KEY_FOR_TEST_AV")
    
    symbol = "FAILHIST"
    asset_type = "stock"
    outputsize = "compact"
    yf_period_expected = "3mo"

    mock_fetch_yf_stock_hist.return_value = None
    mock_fetch_av_stock_hist.return_value = None

    history = orchestrator.get_historical_data(symbol, asset_type, outputsize)
    
    assert history is None, "History should be None if all providers fail"
    
    mock_fetch_yf_stock_hist.assert_called_once_with(symbol, asset_type, period=yf_period_expected)
    
    mock_fetch_av_stock_hist.assert_called_once_with(symbol.upper(), outputsize=outputsize) 
    
    cache_key = f"{symbol.upper()}_{asset_type or 'unknown'}_{yf_period_expected}_hist"
    assert cache_key not in orchestrator._cache["history_cache"], "None should not be cached for history"


@patch("app.services.data_providers.alpha_vantage_provider.fetch_av_stock_historical_data")
@patch("app.services.data_providers.yahoo_finance_provider.fetch_yf_historical_data")
def test_get_historical_data_provider_returns_empty_list(
    mock_fetch_yf_stock_hist,
    mock_fetch_av_stock_hist,
    monkeypatch
):
    monkeypatch.setattr("app.core.config.settings.ALPHA_VANTAGE_API_KEY", "DUMMY_KEY_FOR_TEST")
    symbol = "EMPTYHIST"
    asset_type = "stock"
    outputsize = "compact"

    mock_fetch_yf_stock_hist.return_value = None
    mock_fetch_av_stock_hist.return_value = []

    history = orchestrator.get_historical_data(symbol, asset_type, outputsize)
    
    assert history == []
    mock_fetch_yf_stock_hist.assert_called_once_with(symbol, asset_type, period="3mo")
    mock_fetch_av_stock_hist.assert_called_once_with(symbol.upper(), outputsize=outputsize)

    yf_period = "3mo"
    cache_key = f"{symbol.upper()}_{asset_type or 'unknown'}_{yf_period}_hist"
    cached_entry = orchestrator._cache["history_cache"].get(cache_key)
    assert cached_entry is not None, "Empty list should be cached"
    assert cached_entry[1] == [], "Cached value should be an empty list"
