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
from .coordinator import PinergyData
from .entity import PinergyEntity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class PinergyBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a Pinergy binary sensor entity."""

    is_on_fn: Callable[[PinergyData], bool]
    available_fn: Callable[[PinergyData], bool] | None = None


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
    PinergyBinarySensorEntityDescription(
        key="pending_top_up",
        translation_key="pending_top_up",
        is_on_fn=lambda data: data.balance.pending_top_up,
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
        PinergyBinarySensor(coordinator, description) for description in BINARY_SENSORS
    )


class PinergyBinarySensor(PinergyEntity, BinarySensorEntity):
    """A binary sensor exposing one Pinergy account status flag."""

    entity_description: PinergyBinarySensorEntityDescription

    @property
    def available(self) -> bool:
        """Return True if the coordinator and this sensor's data are available."""
        if not super().available:
            return False
        available_fn = self.entity_description.available_fn
        return available_fn is None or available_fn(self.coordinator.data)

    @property
    def is_on(self) -> bool:
        """Return True if the binary sensor is on."""
        return self.entity_description.is_on_fn(self.coordinator.data)
