"""Button platform for the Pinergy integration."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import PinergyConfigEntry
from .entity import PinergyEntity

PARALLEL_UPDATES = 0

REFRESH_BUTTON = ButtonEntityDescription(
    key="refresh",
    translation_key="refresh",
    entity_category=EntityCategory.DIAGNOSTIC,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PinergyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Pinergy refresh button from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities([PinergyRefreshButton(coordinator, REFRESH_BUTTON)])


class PinergyRefreshButton(PinergyEntity, ButtonEntity):
    """A button that triggers an immediate Pinergy data refresh."""

    async def async_press(self) -> None:
        """Handle the button press by requesting a coordinator refresh."""
        await self.coordinator.async_request_refresh()
