"""Enable the custom integration for Home Assistant platform tests."""

import pytest


@pytest.fixture(autouse=True)
def _enable_custom_integrations(enable_custom_integrations):
    """Allow Home Assistant to load the repository integration."""
    yield
