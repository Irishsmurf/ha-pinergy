"""Event platform for the Pinergy integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.event import (
    EventEntity,
    EventEntityDescription,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import PinergyConfigEntry
from .coordinator import PinergyData
from .entity import PinergyEntity


@dataclass(frozen=True, kw_only=True)
class PinergyEventEntityDescription(EventEntityDescription):
    """Describes a Pinergy event entity."""

    value_fn: Callable[[PinergyData], int | float | None]
    attributes_fn: Callable[[PinergyData], dict[str, Any]] | None = None


EVENTS: tuple[PinergyEventEntityDescription, ...] = (
    PinergyEventEntityDescription(
        key="top_up",
        translation_key="top_up",
        event_types=["top_up_received"],
        value_fn=lambda data: data.balance.last_top_up_ts,
        attributes_fn=lambda data: {"amount": data.balance.last_top_up_amount},
    ),
    PinergyEventEntityDescription(
        key="meter_reading",
        translation_key="meter_reading",
        event_types=["new_meter_reading"],
        value_fn=lambda data: data.balance.last_reading_ts,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PinergyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pinergy events from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        PinergyEventEntity(coordinator, description) for description in EVENTS
    )


class PinergyEventEntity(PinergyEntity, EventEntity):
    """An event entity for Pinergy account occurrences."""

    entity_description: PinergyEventEntityDescription
    _last_seen_ts: int | float | None = None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        current_ts = self.entity_description.value_fn(self.coordinator.data)

        if (
            current_ts is not None
            and self._last_seen_ts is not None
            and current_ts > self._last_seen_ts
        ):
            event_type = self.entity_description.event_types[0]
            attributes = (
                self.entity_description.attributes_fn(self.coordinator.data)
                if self.entity_description.attributes_fn
                else None
            )
            self._trigger_event(event_type, attributes)

        self._last_seen_ts = current_ts
        super()._handle_coordinator_update()
