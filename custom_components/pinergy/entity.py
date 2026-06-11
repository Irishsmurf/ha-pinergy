"""Base entity for the Pinergy integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import PinergyDataUpdateCoordinator


class PinergyEntity(CoordinatorEntity[PinergyDataUpdateCoordinator]):
    """Common base class tying all entities to the Pinergy account device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PinergyDataUpdateCoordinator,
        description: EntityDescription,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.entity_description = description
        login = coordinator.login_response
        self._attr_unique_id = f"{login.premises_number}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, login.premises_number)},
            name="Pinergy Account",
            manufacturer=MANUFACTURER,
            model=login.account_type or "Smart Meter",
        )
