"""Tests for the Pinergy diagnostics platform."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

from pypinergy import PinergyAPIError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pinergy.const import DOMAIN
from custom_components.pinergy.diagnostics import async_get_config_entry_diagnostics
from homeassistant.components.diagnostics import REDACTED
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant

TEST_USER_INPUT = {
    CONF_EMAIL: "user@example.com",
    CONF_PASSWORD: "super-secret",
}


async def _setup_entry(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="PN123456",
        title=TEST_USER_INPUT[CONF_EMAIL],
        data=TEST_USER_INPUT,
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_diagnostics_redacts_sensitive_data(
    hass: HomeAssistant, mock_pinergy_client: MagicMock
) -> None:
    """Test that diagnostics expose API data with credentials redacted."""
    entry = await _setup_entry(hass)

    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["entry_data"][CONF_EMAIL] == REDACTED
    assert result["entry_data"][CONF_PASSWORD] == REDACTED
    assert result["login"]["auth_token"] == REDACTED
    assert result["login"]["premises_number"] == REDACTED
    # Redaction must reach nested dataclasses too.
    assert result["login"]["user"]["mobile_number"] == REDACTED

    assert result["data"]["balance"]["credit_balance"] == 23.45
    assert result["data"]["usage"]["day"][0]["kwh"] == 8.76
    assert result["data"]["compare"]["day"]["kwh"]["average_home"] == 11.5

    # No sensitive raw value may survive anywhere in the payload.
    dump = json.dumps(result, default=str)
    for secret in ("test-token", "PN123456", "user@example.com", "super-secret"):
        assert secret not in dump


async def test_diagnostics_without_compare_data(
    hass: HomeAssistant, mock_pinergy_client: MagicMock
) -> None:
    """Test that diagnostics work when the compare endpoint is unavailable."""
    mock_pinergy_client.compare_usage.side_effect = PinergyAPIError("not available")
    entry = await _setup_entry(hass)

    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["data"]["compare"] is None
    assert result["data"]["balance"]["credit_balance"] == 23.45
