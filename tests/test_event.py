"""Tests for the Pinergy event platform."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_capture_events,
    mock_restore_cache,
)

from custom_components.pinergy.const import DOMAIN
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, State

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


async def test_event_setup(hass: HomeAssistant, mock_pinergy_client: MagicMock) -> None:
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

    # Find the state_changed event where the top-up actually fired. Exposing
    # last_seen_ts via extra_state_attributes means the baseline update also
    # emits a state_changed (event_type=None), so filter for the real event.
    event = next(
        e
        for e in events
        if e.data["entity_id"] == entity_id
        and e.data["new_state"].attributes.get("event_type") == "top_up_received"
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

    # Filter for the state_changed where the meter reading actually fired; the
    # baseline update also emits a state_changed (event_type=None).
    event = next(
        e
        for e in events
        if e.data["entity_id"] == entity_id
        and e.data["new_state"].attributes.get("event_type") == "new_meter_reading"
    )
    assert event.data["new_state"].attributes["event_type"] == "new_meter_reading"


async def test_topup_during_downtime_fires_on_first_refresh(
    hass: HomeAssistant, mock_pinergy_client: MagicMock
) -> None:
    """Test that a top-up which occurred during HA downtime fires on first refresh.

    This validates the async_added_to_hass restore logic: if the recorder has
    a previous last_seen_ts that predates the API's current last_top_up_ts, the
    first _handle_coordinator_update should fire a top_up_received event.
    """
    balance = build_balance_response()
    pre_downtime_ts = balance.last_top_up_ts - 3600

    # Inject a "previous run" state whose last_seen_ts is before the top-up.
    mock_restore_cache(
        hass,
        [
            State(
                "event.pinergy_account_top_up",
                STATE_UNKNOWN,
                {"last_seen_ts": pre_downtime_ts},
            )
        ],
    )

    entry = _make_entry()
    entry.add_to_hass(hass)
    events = async_capture_events(hass, "state_changed")

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    topup_events = [
        e
        for e in events
        if e.data["entity_id"] == "event.pinergy_account_top_up"
        and (s := e.data.get("new_state")) is not None
        and s.attributes.get("event_type") == "top_up_received"
    ]
    assert len(topup_events) == 1


async def test_no_spurious_event_on_clean_startup(
    hass: HomeAssistant, mock_pinergy_client: MagicMock
) -> None:
    """Test that no event fires on the first refresh when there is no prior state.

    On a brand-new install (or after the recorder DB is cleared), _last_seen_ts
    starts as None and the first update must set the baseline without firing.
    """
    entry = _make_entry()
    entry.add_to_hass(hass)
    events = async_capture_events(hass, "state_changed")

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    topup_events = [
        e
        for e in events
        if e.data["entity_id"] == "event.pinergy_account_top_up"
        and (s := e.data.get("new_state")) is not None
        and s.attributes.get("event_type") == "top_up_received"
    ]
    assert len(topup_events) == 0
