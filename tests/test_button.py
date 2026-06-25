"""Tests for the Pinergy button platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pinergy.const import DOMAIN
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from .conftest import build_balance_response

_ENTRY_DATA = {CONF_EMAIL: "user@example.com", CONF_PASSWORD: "super-secret"}


def _make_entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id="PN123456",
        title="user@example.com",
        data=_ENTRY_DATA,
    )


async def _setup_entry(hass: HomeAssistant) -> MockConfigEntry:
    entry = _make_entry()
    entry.add_to_hass(hass)

    # Define a mock refresh that sets the required properties
    async def mock_first_refresh(self):
        self.login_response = MagicMock(
            premises_number="PN123456", account_type="Smart Meter"
        )
        self.data = MagicMock()
        self.data.balance = build_balance_response()

    with patch(
        "custom_components.pinergy.coordinator.PinergyDataUpdateCoordinator.async_config_entry_first_refresh",
        new=mock_first_refresh,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    return entry


async def test_button_setup(
    hass: HomeAssistant, mock_pinergy_client: MagicMock
) -> None:
    """Test that the refresh button entity is created on the account device."""
    await _setup_entry(hass)

    assert hass.states.get("button.pinergy_account_refresh") is not None


async def test_button_press_calls_refresh(
    hass: HomeAssistant, mock_pinergy_client: MagicMock
) -> None:
    """Test that pressing the button requests a single coordinator refresh."""
    entry = await _setup_entry(hass)

    coordinator = entry.runtime_data
    coordinator.async_request_refresh = AsyncMock()

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.pinergy_account_refresh"},
        blocking=True,
    )
    await hass.async_block_till_done()

    coordinator.async_request_refresh.assert_awaited_once()
