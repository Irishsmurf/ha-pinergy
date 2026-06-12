"""Tests for the Pinergy event platform."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_capture_events,
)

from custom_components.pinergy.const import DOMAIN
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from .conftest import build_balance_response


async def _setup_entry(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="PN123456",
        title="user@example.com",
        data={CONF_EMAIL: "user@example.com", CONF_PASSWORD: "super-secret"},
    )
    entry.add_to_hass(hass)
    
    # Define a mock refresh that sets the required properties
    async def mock_first_refresh(self):
        self.login_response = MagicMock(premises_number="PN123456", account_type="Smart Meter")
        self.data = MagicMock()
        self.data.balance = build_balance_response()
    
    with patch("custom_components.pinergy.coordinator.PinergyDataUpdateCoordinator.async_config_entry_first_refresh", new=mock_first_refresh):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    
    return entry


async def test_event_setup(
    hass: HomeAssistant, mock_pinergy_client: MagicMock
) -> None:
    """Test that event entities are created."""
    await _setup_entry(hass)

    assert hass.states.get("event.pinergy_account_top_up") is not None
    assert hass.states.get("event.pinergy_account_meter_reading") is not None


async def test_top_up_event_triggers(
    hass: HomeAssistant, mock_pinergy_client: MagicMock
) -> None:
    """Test that a new top-up triggers an event."""
    entry = await _setup_entry(hass)
    events = async_capture_events(hass, "state_changed")

    coordinator = entry.runtime_data
    entity = hass.data["entity_registry"].async_get("event.pinergy_account_top_up")
    
    # We must retrieve the actual entity instance from hass.data
    # This is slightly brittle but needed since we're bypassing normal poll logic
    entity_id = "event.pinergy_account_top_up"
    entity_instance = hass.data["entity_components"]["event"].get_entity(entity_id)
    
    # Initialize _last_seen_ts
    entity_instance._handle_coordinator_update()
    
    # Simulate a new top-up
    coordinator.data.balance.last_top_up_ts += 3600
    coordinator.data.balance.last_top_up_amount = 50.0
    
    # Trigger the update logic directly
    entity_instance._handle_coordinator_update()
    await hass.async_block_till_done()

    # Find the state_changed event for our entity
    event = next(
        e for e in events if e.data["entity_id"] == entity_id
    )
    assert event.data["new_state"].attributes["event_type"] == "top_up_received"
    assert event.data["new_state"].attributes["amount"] == 50.0


async def test_meter_reading_event_triggers(
    hass: HomeAssistant, mock_pinergy_client: MagicMock
) -> None:
    """Test that a new meter reading triggers an event."""
    entry = await _setup_entry(hass)
    events = async_capture_events(hass, "state_changed")

    coordinator = entry.runtime_data
    entity_id = "event.pinergy_account_meter_reading"
    entity_instance = hass.data["entity_components"]["event"].get_entity(entity_id)
    
    # Initialize _last_seen_ts
    entity_instance._handle_coordinator_update()
    
    # Simulate a new meter reading
    coordinator.data.balance.last_reading_ts += 3600
    
    # Trigger the update logic directly
    entity_instance._handle_coordinator_update()
    await hass.async_block_till_done()

    # Find the state_changed event for our entity
    event = next(
        e for e in events if e.data["entity_id"] == entity_id
    )
    assert event.data["new_state"].attributes["event_type"] == "new_meter_reading"
