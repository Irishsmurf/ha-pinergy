"""Binary sensor platform for the Pinergy integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import PinergyConfigEntry
from .coordinator import PinergyData, PinergyDataUpdateCoordinator
from .entity import PinergyEntity


@dataclass(frozen=True, kw_only=True)
class PinergyBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a Pinergy binary sensor entity."""

    is_on_fn: Callable[[PinergyData], bool]


BINARY_SENSORS: tuple[PinergyBinarySensorEntityDescription, ...] = (
    PinergyBinarySensorEntityDescription(
        # On = power flowing; the supply being disconnected reads as "off",
        # matching the POWER device class semantics (on = power detected).
        key="power",
        translation_key="power",
        device_class=BinarySensorDeviceClass.POWER,
        is_on_fn=lambda data: not data.balance.power_off,
    ),
    PinergyBinarySensorEntityDescription(
        key="emergency_credit",
        translation_key="emergency_credit",
        device_class=BinarySensorDeviceClass.SAFETY,
        is_on_fn=lambda data: data.balance.emergency_credit,
    ),
    PinergyBinarySensorEntityDescription(
        key="credit_low",
        translation_key="credit_low",
        device_class=BinarySensorDeviceClass.PROBLEM,
        is_on_fn=lambda data: data.balance.credit_low,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PinergyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pinergy binary sensors from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        PinergyBinarySensor(coordinator, description)
        for description in BINARY_SENSORS
    )


class PinergyBinarySensor(PinergyEntity, BinarySensorEntity):
    """A binary sensor exposing one Pinergy account status flag."""

    entity_description: PinergyBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: PinergyDataUpdateCoordinator,
        description: PinergyBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, description)

    @property
    def is_on(self) -> bool:
        """Return True if the binary sensor is on."""
        return self.entity_description.is_on_fn(self.coordinator.data)
