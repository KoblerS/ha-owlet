"""Base entity for the Owlet integration."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import OwletCoordinator


class OwletBaseEntity(CoordinatorEntity[OwletCoordinator]):
    """Common base for all Owlet entities tied to a single sock (dsn)."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: OwletCoordinator, dsn: str) -> None:
        """Initialise the entity for the given device serial number."""
        super().__init__(coordinator)
        self._dsn = dsn
        info = coordinator.devices.get(dsn, {})
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, dsn)},
            manufacturer=MANUFACTURER,
            name=info.get("product_name", "Owlet Dream Sock"),
            model=info.get("oem_model") or info.get("model"),
            sw_version=info.get("sw_version"),
            serial_number=dsn,
        )

    @property
    def device_data(self) -> dict[str, Any]:
        """Return the normalised properties for this sock."""
        return self.coordinator.data.get(self._dsn, {})

    @property
    def available(self) -> bool:
        """Return True if the coordinator succeeded and this sock has data."""
        return super().available and self._dsn in self.coordinator.data
