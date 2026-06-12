"""The Pinergy integration."""

from __future__ import annotations

from pypinergy import PinergyClient

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant

from .coordinator import PinergyDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR]

type PinergyConfigEntry = ConfigEntry[PinergyDataUpdateCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: PinergyConfigEntry) -> bool:
    """Set up Pinergy from a config entry."""
    client = PinergyClient(entry.data[CONF_EMAIL], entry.data[CONF_PASSWORD])

    coordinator = PinergyDataUpdateCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: PinergyConfigEntry) -> bool:
    """Unload a Pinergy config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await hass.async_add_executor_job(entry.runtime_data.client.close)
    return unload_ok
