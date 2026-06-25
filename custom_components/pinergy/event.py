"""Event platform for the Pinergy integration."""

from __future__ import annotations

import contextlib
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

    async def async_added_to_hass(self) -> None:
        """Restore the last-seen timestamp from the recorder on startup.

        Without this, any event that occurred while HA was offline would be
        silently dropped because _last_seen_ts would initialise to None and
        the first _handle_coordinator_update would set it without firing.

        EventEntity already inherits RestoreEntity, so async_get_last_state is
        available here without adding it to the base classes.
        """
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            with contextlib.suppress(KeyError, TypeError, ValueError):
                stored = last_state.attributes.get("last_seen_ts")
                if stored is not None:
                    self._last_seen_ts = float(stored)

        # The coordinator's first refresh runs before the entity is added, so
        # its update is never delivered here. Evaluate the already-available
        # data now so a top-up missed during downtime fires immediately on
        # startup rather than waiting for the next poll.
        if self.coordinator.data is not None:
            self._handle_coordinator_update()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose last_seen_ts so HA persists it and we can restore it."""
        return {"last_seen_ts": self._last_seen_ts}

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
