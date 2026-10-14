"""Binary sensor platform for the Owlet integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import OwletConfigEntry
from .entity import OwletBaseEntity


@dataclass(frozen=True, kw_only=True)
class OwletBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes an Owlet binary sensor."""

    value_fn: Callable[[dict[str, Any]], bool | None]


def _as_bool(value: Any) -> bool | None:
    if value is None:
        return None
    return bool(value)


BINARY_SENSORS: tuple[OwletBinarySensorEntityDescription, ...] = (
    OwletBinarySensorEntityDescription(
        key="base_station_on",
        translation_key="base_station_on",
        device_class=BinarySensorDeviceClass.POWER,
        value_fn=lambda d: _as_bool(d.get("base_station_on")),
    ),
    OwletBinarySensorEntityDescription(
        key="sock_connection",
        translation_key="sock_connection",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_fn=lambda d: _as_bool(d.get("sock_connection")),
    ),
    OwletBinarySensorEntityDescription(
        key="sock_off",
        translation_key="sock_off",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda d: _as_bool(d.get("sock_off")),
    ),
    OwletBinarySensorEntityDescription(
        key="charging",
        translation_key="charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: _as_bool(d.get("charging")),
    ),
    OwletBinarySensorEntityDescription(
        key="high_heart_rate_alert",
        translation_key="high_heart_rate_alert",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda d: _as_bool(d.get("high_heart_rate_alert")),
    ),
    OwletBinarySensorEntityDescription(
        key="low_heart_rate_alert",
        translation_key="low_heart_rate_alert",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda d: _as_bool(d.get("low_heart_rate_alert")),
    ),
    OwletBinarySensorEntityDescription(
        key="low_oxygen_alert",
        translation_key="low_oxygen_alert",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda d: _as_bool(d.get("low_oxygen_alert")),
    ),
    OwletBinarySensorEntityDescription(
        key="high_oxygen_alert",
        translation_key="high_oxygen_alert",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_registry_enabled_default=False,
        value_fn=lambda d: _as_bool(d.get("high_oxygen_alert")),
    ),
    OwletBinarySensorEntityDescription(
        key="low_battery_alert",
        translation_key="low_battery_alert",
        device_class=BinarySensorDeviceClass.BATTERY,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: _as_bool(d.get("low_battery_alert")),
    ),
    OwletBinarySensorEntityDescription(
        key="lost_power_alert",
        translation_key="lost_power_alert",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: _as_bool(d.get("lost_power_alert")),
    ),
    OwletBinarySensorEntityDescription(
        key="firmware_update_available",
        translation_key="firmware_update_available",
        device_class=BinarySensorDeviceClass.UPDATE,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda d: _as_bool(d.get("firmware_update_available")),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OwletConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Owlet binary sensors."""
    coordinator = entry.runtime_data
    entities: list[OwletBinarySensor] = []
    for dsn in coordinator.devices:
        for description in BINARY_SENSORS:
            entities.append(OwletBinarySensor(coordinator, dsn, description))
    async_add_entities(entities)


class OwletBinarySensor(OwletBaseEntity, BinarySensorEntity):
    """Representation of an Owlet binary sensor."""

    entity_description: OwletBinarySensorEntityDescription

    def __init__(
        self,
        coordinator,
        dsn: str,
        description: OwletBinarySensorEntityDescription,
    ) -> None:
        """Initialise the binary sensor."""
        super().__init__(coordinator, dsn)
        self.entity_description = description
        self._attr_unique_id = f"{dsn}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        """Return the current state."""
        return self.entity_description.value_fn(self.device_data)
