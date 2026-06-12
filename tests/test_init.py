"""Tests for the Pinergy integration setup."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from freezegun.api import FrozenDateTimeFactory
from pypinergy import (
    PinergyAPIError,
    PinergyAuthError,
    PinergyHTTPError,
    PinergyTimeoutError,
)
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.pinergy.const import DEFAULT_SCAN_INTERVAL, DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import (
    CONF_EMAIL,
    CONF_PASSWORD,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .conftest import build_balance_response, build_usage_response

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
    assert hass.states.get("sensor.pinergy_account_this_week_s_usage").state == "54.3"
    assert hass.states.get("sensor.pinergy_account_this_week_s_cost").state == "15.67"
    assert hass.states.get("sensor.pinergy_account_this_month_s_usage").state == "210.4"
    assert hass.states.get("sensor.pinergy_account_this_month_s_cost").state == "60.12"
    assert (
        hass.states.get("sensor.pinergy_account_last_meter_reading").state
        == datetime.fromtimestamp(1765886400, tz=UTC).isoformat()
    )

    # Power is on (supply connected); alert flags are off.
    assert hass.states.get("binary_sensor.pinergy_account_power").state == STATE_ON
    assert (
        hass.states.get("binary_sensor.pinergy_account_emergency_credit").state
        == STATE_OFF
    )
    assert (
        hass.states.get("binary_sensor.pinergy_account_credit_low").state == STATE_OFF
    )
    assert (
        hass.states.get("binary_sensor.pinergy_account_pending_top_up").state
        == STATE_OFF
    )

    # The extras ship disabled; users opt in from the device page.
    entity_registry = er.async_get(hass)
    for unique_id in (
        "PN123456_last_top_up",
        "PN123456_average_home_usage",
        "PN123456_average_home_cost",
    ):
        entity_id = entity_registry.async_get_entity_id("sensor", DOMAIN, unique_id)
        assert entity_id is not None
        assert (
            entity_registry.async_get(entity_id).disabled_by
            is er.RegistryEntryDisabler.INTEGRATION
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
    mock_pinergy_client.close.assert_called_once()


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


@pytest.mark.parametrize(
    "connection_error",
    [PinergyHTTPError("server error"), PinergyTimeoutError("timed out")],
)
async def test_setup_connection_error_retries(
    hass: HomeAssistant,
    mock_pinergy_client: MagicMock,
    connection_error: Exception,
) -> None:
    """Test that a network error during setup leaves the entry in retry state."""
    mock_pinergy_client.login.side_effect = connection_error

    entry = _make_entry()
    entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_RETRY


@pytest.mark.parametrize(
    "token_error",
    [
        PinergyAuthError("Auth token rejected (401)"),
        PinergyAPIError("Auth_token is not correct."),
    ],
)
async def test_refresh_relogins_on_expired_token(
    hass: HomeAssistant,
    mock_pinergy_client: MagicMock,
    freezer: FrozenDateTimeFactory,
    token_error: Exception,
) -> None:
    """Test that a rejected token during refresh self-heals via re-login."""
    entry = _make_entry()
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert mock_pinergy_client.login.call_count == 1

    mock_pinergy_client.get_balance.side_effect = [
        token_error,
        build_balance_response(),
    ]

    freezer.tick(DEFAULT_SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert mock_pinergy_client.login.call_count == 2
    mock_pinergy_client.logout.assert_not_called()
    assert entry.state is ConfigEntryState.LOADED
    assert hass.states.get("sensor.pinergy_account_current_balance").state == "23.45"


async def test_refresh_relogin_failure_starts_reauth(
    hass: HomeAssistant,
    mock_pinergy_client: MagicMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test that a failed re-login after token expiry triggers a reauth flow."""
    entry = _make_entry()
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    mock_pinergy_client.get_balance.side_effect = PinergyAPIError(
        "Auth_token is not correct."
    )
    mock_pinergy_client.login.side_effect = PinergyAuthError("Login failed")

    freezer.tick(DEFAULT_SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert len(flows) == 1
    assert flows[0]["context"]["source"] == "reauth"


async def test_refresh_non_auth_api_error_does_not_relogin(
    hass: HomeAssistant,
    mock_pinergy_client: MagicMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test that an unrelated API error fails the update without re-login."""
    entry = _make_entry()
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    mock_pinergy_client.get_balance.side_effect = PinergyAPIError("Server error")

    freezer.tick(DEFAULT_SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert mock_pinergy_client.login.call_count == 1
    state = hass.states.get("sensor.pinergy_account_current_balance")
    assert state.state == "unavailable"


async def test_today_sensors_unavailable_without_meter_data(
    hass: HomeAssistant, mock_pinergy_client: MagicMock
) -> None:
    """Test that today's sensors are unavailable when the meter has no data yet."""
    mock_pinergy_client.get_usage.return_value = build_usage_response(
        today_available=False
    )

    entry = _make_entry()
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert (
        hass.states.get("sensor.pinergy_account_today_s_usage").state
        == STATE_UNAVAILABLE
    )
    assert (
        hass.states.get("sensor.pinergy_account_today_s_cost").state
        == STATE_UNAVAILABLE
    )
    # Balance-backed sensors are unaffected.
    assert hass.states.get("sensor.pinergy_account_current_balance").state == "23.45"


def _enable_compare_sensors(hass: HomeAssistant) -> None:
    """Pre-register the disabled-by-default compare sensors as enabled."""
    entity_registry = er.async_get(hass)
    for key in ("average_home_usage", "average_home_cost"):
        entity_registry.async_get_or_create(
            "sensor",
            DOMAIN,
            f"PN123456_{key}",
            suggested_object_id=f"pinergy_account_{key}",
        )


async def test_compare_sensors_report_average_home(
    hass: HomeAssistant, mock_pinergy_client: MagicMock
) -> None:
    """Test that the enabled compare sensors expose the average-home values."""
    _enable_compare_sensors(hass)

    entry = _make_entry()
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("sensor.pinergy_account_average_home_usage").state == "11.5"
    assert hass.states.get("sensor.pinergy_account_average_home_cost").state == "3.45"


async def test_compare_endpoint_failure_is_tolerated(
    hass: HomeAssistant, mock_pinergy_client: MagicMock
) -> None:
    """Test that a failing compare endpoint never breaks the refresh."""
    mock_pinergy_client.compare_usage.side_effect = PinergyAPIError(
        "Comparison not available"
    )
    _enable_compare_sensors(hass)

    entry = _make_entry()
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert hass.states.get("sensor.pinergy_account_current_balance").state == "23.45"
    assert (
        hass.states.get("sensor.pinergy_account_average_home_usage").state
        == STATE_UNAVAILABLE
    )
