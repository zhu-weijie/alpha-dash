# backend/tests/conftest.py
import pytest


@pytest.fixture(autouse=True)  # autouse=True makes it apply to all tests in the session
def override_settings(monkeypatch):
    """
    Fixture to override application settings for tests.
    This ensures tests run with predictable configuration.
    """
    # Override specific settings by patching the 'settings' object from app.core.config
    # Make sure the path to 'settings' is correct for your project structure
    # when 'app.core.config' is imported by test modules.

    # Example: If your tests import 'app.auth.security' which imports 'app.core.config.settings'
    monkeypatch.setattr(
        "app.core.config.settings.SECRET_KEY",
        "test_secret_key_for_pytest_0123456789abcdef",
    )
    monkeypatch.setattr("app.core.config.settings.ALGORITHM", "HS256")  # Clean value
    monkeypatch.setattr("app.core.config.settings.ACCESS_TOKEN_EXPIRE_MINUTES", 30)

    # If settings are used in other modules imported by tests, you might need to patch them there too,
    # or ensure this conftest.py is loaded before those modules try to access settings.
    # For example, if app.auth.security directly imports settings:
    # monkeypatch.setattr("app.auth.security.settings.ALGORITHM", "HS256")

    # It's generally best to patch where the setting is *used* or its source.
    # Patching app.core.config.settings should be effective if other modules import it.
