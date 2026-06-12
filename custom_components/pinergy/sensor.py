"""Sensor platform for the Pinergy integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import CURRENCY_EURO, UnitOfEnergy, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import PinergyConfigEntry
from .coordinator import PinergyData
from .entity import PinergyEntity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class PinergySensorEntityDescription(SensorEntityDescription):
    """Describes a Pinergy sensor entity."""

    value_fn: Callable[[PinergyData], StateType]
    available_fn: Callable[[PinergyData], bool] | None = None


def _today_available(data: PinergyData) -> bool:
    """Return True when today's meter data has been reported."""
    return bool(data.usage.day) and data.usage.day[0].available


SENSORS: tuple[PinergySensorEntityDescription, ...] = (
    PinergySensorEntityDescription(
        key="current_balance",
        translation_key="current_balance",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=CURRENCY_EURO,
        suggested_display_precision=2,
        value_fn=lambda data: data.balance.credit_balance,
    ),
    PinergySensorEntityDescription(
        key="days_remaining",
        translation_key="days_remaining",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.DAYS,
        value_fn=lambda data: data.balance.top_up_in_days,
    ),
    PinergySensorEntityDescription(
        key="last_top_up_amount",
        translation_key="last_top_up_amount",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=CURRENCY_EURO,
        suggested_display_precision=2,
        value_fn=lambda data: data.balance.last_top_up_amount,
    ),
    PinergySensorEntityDescription(
        key="today_usage",
        translation_key="today_usage",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        value_fn=lambda data: data.usage.day[0].kwh,
        available_fn=_today_available,
    ),
    PinergySensorEntityDescription(
        key="today_cost",
        translation_key="today_cost",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=CURRENCY_EURO,
        suggested_display_precision=2,
        value_fn=lambda data: data.usage.day[0].amount,
        available_fn=_today_available,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PinergyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pinergy sensors from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        PinergySensor(coordinator, description) for description in SENSORS
    )


class PinergySensor(PinergyEntity, SensorEntity):
    """A sensor exposing one Pinergy account metric."""

    entity_description: PinergySensorEntityDescription

    @property
    def available(self) -> bool:
        """Return True if the coordinator and this sensor's data are available."""
        if not super().available:
            return False
        available_fn = self.entity_description.available_fn
        return available_fn is None or available_fn(self.coordinator.data)

    @property
    def native_value(self) -> StateType:
        """Return the current value of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data)
