"""Tests for the Pinergy integration setup."""

from __future__ import annotations

from unittest.mock import MagicMock

from pypinergy import PinergyAuthError, PinergyHTTPError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from custom_components.pinergy.const import DOMAIN

TEST_USER_INPUT = {
    CONF_EMAIL: "user@example.com",
    CONF_PASSWORD: "super-secret",
}


def _make_entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id="PN123456",
        title=TEST_USER_INPUT[CONF_EMAIL],
        data=TEST_USER_INPUT,
    )


async def test_setup_creates_device_and_entities(
    hass: HomeAssistant, mock_pinergy_client: MagicMock
) -> None:
    """Test that setup creates the account device and all entities."""
    entry = _make_entry()
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED

    device_registry = dr.async_get(hass)
    device = device_registry.async_get_device(identifiers={(DOMAIN, "PN123456")})
    assert device is not None
    assert device.manufacturer == "Pinergy"

    assert hass.states.get("sensor.pinergy_account_current_balance").state == "23.45"
    assert hass.states.get("sensor.pinergy_account_days_remaining").state == "7"
    assert hass.states.get("sensor.pinergy_account_last_top_up_amount").state == "20.0"
    assert hass.states.get("sensor.pinergy_account_today_s_usage").state == "8.76"
    assert hass.states.get("sensor.pinergy_account_today_s_cost").state == "2.34"

    # Power is on (supply connected); alert flags are off.
    assert hass.states.get("binary_sensor.pinergy_account_power").state == STATE_ON
    assert (
        hass.states.get("binary_sensor.pinergy_account_emergency_credit").state
        == STATE_OFF
    )
    assert (
        hass.states.get("binary_sensor.pinergy_account_credit_low").state == STATE_OFF
    )


async def test_unload_entry(
    hass: HomeAssistant, mock_pinergy_client: MagicMock
) -> None:
    """Test that the entry unloads cleanly."""
    entry = _make_entry()
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_setup_auth_error_starts_reauth(
    hass: HomeAssistant, mock_pinergy_client: MagicMock
) -> None:
    """Test that invalid credentials during setup trigger a reauth flow."""
    mock_pinergy_client.login.side_effect = PinergyAuthError("Login failed")

    entry = _make_entry()
    entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_ERROR

    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert len(flows) == 1
    assert flows[0]["context"]["source"] == "reauth"


async def test_setup_connection_error_retries(
    hass: HomeAssistant, mock_pinergy_client: MagicMock
) -> None:
    """Test that a network error during setup leaves the entry in retry state."""
    mock_pinergy_client.login.side_effect = PinergyHTTPError("timeout")

    entry = _make_entry()
    entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_RETRY
