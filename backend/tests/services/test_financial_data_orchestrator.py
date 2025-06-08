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


@patch("app.services.data_providers.yahoo_finance_provider.fetch_yf_current_price")
@patch("app.services.data_providers.alpha_vantage_provider.fetch_av_stock_current_price") 
def test_get_current_price_stock_cache_miss_then_hit(
    mock_fetch_av_stock_price,
    mock_fetch_yf_current_price,
    monkeypatch
):
    monkeypatch.setattr("app.core.config.settings.ALPHA_VANTAGE_API_KEY", "DUMMY_KEY_FOR_TEST")
    
    symbol = "AAPL"
    asset_type = "stock"
    mock_yf_price = 150.75 # This is the price yfinance should return
    
    mock_fetch_yf_current_price.return_value = mock_yf_price
    mock_fetch_av_stock_price.return_value = 999.99 # Different value for AV to ensure it's not called

    price1 = orchestrator.get_current_price(symbol, asset_type)
    assert price1 == mock_yf_price
    mock_fetch_yf_current_price.assert_called_once_with(symbol, asset_type)
    mock_fetch_av_stock_price.assert_not_called() # AV should not be called if yf succeeds

    price2 = orchestrator.get_current_price(symbol, asset_type)
    assert price2 == mock_yf_price
    mock_fetch_yf_current_price.assert_called_once() # Call count remains 1
    mock_fetch_av_stock_price.assert_not_called()


@patch("app.services.data_providers.alpha_vantage_provider.fetch_av_crypto_current_price")
@patch("app.services.data_providers.yahoo_finance_provider.fetch_yf_current_price")
def test_get_current_price_crypto_cache_miss_then_hit(
    mock_fetch_yf_crypto_price: MagicMock,
    mock_fetch_av_crypto_price: MagicMock,
    monkeypatch
):
    monkeypatch.setattr(settings, "ALPHA_VANTAGE_API_KEY", "DUMMY_KEY_FOR_TEST_AV")
    
    symbol = "ETH"
    asset_type = "crypto"
    expected_yf_price = 2500.75

    mock_fetch_yf_crypto_price.return_value = expected_yf_price
    mock_fetch_av_crypto_price.return_value = 9999.99

    price1 = orchestrator.get_current_price(symbol, asset_type)
    
    assert price1 == expected_yf_price, "Price should come from yfinance provider"
    
    mock_fetch_yf_crypto_price.assert_called_once_with(symbol, asset_type)
    
    mock_fetch_av_crypto_price.assert_not_called()
    
    cache_key = f"{symbol.upper()}_{asset_type or 'unknown'}_price"
    assert cache_key in orchestrator._cache["price_cache"]
    assert orchestrator._cache["price_cache"][cache_key][1] == expected_yf_price

    price2 = orchestrator.get_current_price(symbol, asset_type)

    assert price2 == expected_yf_price, "Price should come from cache"
    
    mock_fetch_yf_crypto_price.assert_called_once() 
    mock_fetch_av_crypto_price.assert_not_called()


@patch("app.services.data_providers.alpha_vantage_provider.fetch_av_stock_current_price", return_value=None)
def test_get_current_price_provider_returns_none(mock_fetch_av_stock_price, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ALPHA_VANTAGE_API_KEY", "DUMMY_KEY_FOR_TEST")
    symbol = "FAIL"
    asset_type = "stock"

    price = orchestrator.get_current_price(symbol, asset_type)
    assert price is None
    mock_fetch_av_stock_price.assert_called_once_with(symbol.upper())
    # Ensure None is not cached if that's the desired behavior, or test that it is cached if it should be.
    # Current orchestrator only caches non-None values for price.
    assert not orchestrator._cache["price_cache"] # Cache should be empty if None was returned


def test_get_current_price_cache_expiration(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ALPHA_VANTAGE_API_KEY", "DUMMY_KEY_FOR_TEST")
    # Temporarily shorten cache duration for this test
    monkeypatch.setattr(orchestrator, "CACHE_DURATION_SECONDS", 0.1) 

    symbol = "EXP"
    asset_type = "stock"
    mock_price = 100.00
    
    with patch("app.services.data_providers.alpha_vantage_provider.fetch_av_stock_current_price", return_value=mock_price) as mock_fetch_av_stock_price:
        # 1. First call: Cache miss, sets cache
        price1 = orchestrator.get_current_price(symbol, asset_type)
        assert price1 == mock_price
        mock_fetch_av_stock_price.assert_called_once_with(symbol.upper())

        # 2. Wait for cache to expire
        time.sleep(0.2)

        # 3. Second call: Cache should be expired, call provider again
        price2 = orchestrator.get_current_price(symbol, asset_type)
        assert price2 == mock_price
        assert mock_fetch_av_stock_price.call_count == 2


# --- Tests for get_historical_data ---

@patch("app.services.data_providers.alpha_vantage_provider.fetch_av_stock_historical_data")
def test_get_historical_data_stock_cache_miss_then_hit(mock_fetch_av_stock_hist, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ALPHA_VANTAGE_API_KEY", "DUMMY_KEY_FOR_TEST")
    symbol = "MSFT"
    asset_type = "stock"
    outputsize = "compact"
    mock_hist_data = [{"date": date(2023, 1, 1), "close": 250.0}]
    mock_fetch_av_stock_hist.return_value = mock_hist_data

    # 1. Cache miss
    hist1 = orchestrator.get_historical_data(symbol, asset_type, outputsize)
    assert hist1 == mock_hist_data
    mock_fetch_av_stock_hist.assert_called_once_with(symbol.upper(), outputsize=outputsize)

    # 2. Cache hit
    hist2 = orchestrator.get_historical_data(symbol, asset_type, outputsize)
    assert hist2 == mock_hist_data
    mock_fetch_av_stock_hist.assert_called_once()

@patch("app.services.data_providers.alpha_vantage_provider.fetch_av_crypto_historical_data")
def test_get_historical_data_crypto_cache_miss_then_hit(mock_fetch_av_crypto_hist, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ALPHA_VANTAGE_API_KEY", "DUMMY_KEY_FOR_TEST")
    symbol = "BTC" # Orchestrator expects base symbol
    asset_type = "crypto"
    outputsize = "compact" # Note: AV crypto provider might ignore this and return full
    mock_hist_data = [{"date": date(2023, 1, 1), "close": 30000.0}]
    mock_fetch_av_crypto_hist.return_value = mock_hist_data
    
    # 1. Cache miss
    hist1 = orchestrator.get_historical_data(symbol, asset_type, outputsize)
    assert hist1 == mock_hist_data
    mock_fetch_av_crypto_hist.assert_called_once_with(symbol.upper(), outputsize=outputsize)

    # 2. Cache hit
    hist2 = orchestrator.get_historical_data(symbol, asset_type, outputsize)
    assert hist2 == mock_hist_data
    mock_fetch_av_crypto_hist.assert_called_once()

@patch("app.services.data_providers.alpha_vantage_provider.fetch_av_stock_historical_data", return_value=None)
def test_get_historical_data_provider_returns_none(mock_fetch_av_stock_hist, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ALPHA_VANTAGE_API_KEY", "DUMMY_KEY_FOR_TEST")
    symbol = "FAILHIST"
    asset_type = "stock"

    history = orchestrator.get_historical_data(symbol, asset_type)
    assert history is None
    mock_fetch_av_stock_hist.assert_called_once_with(symbol.upper(), outputsize="compact")
    # Check cache based on your orchestrator's logic for caching None/empty lists
    # Current orchestrator caches empty list, but not None for history
    cache_key = f"{symbol.upper()}_{asset_type or 'unknown'}_compact_hist"
    assert orchestrator._cache["history_cache"].get(cache_key) is None


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
