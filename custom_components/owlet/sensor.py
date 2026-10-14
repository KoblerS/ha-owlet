"""Sensor platform for the Owlet integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import OwletConfigEntry
from .const import SLEEP_STATES
from .entity import OwletBaseEntity


@dataclass(frozen=True, kw_only=True)
class OwletSensorEntityDescription(SensorEntityDescription):
    """Describes an Owlet sensor."""

    value_fn: Callable[[dict[str, Any]], Any]


def _sleep_state(data: dict[str, Any]) -> str | None:
    state = data.get("sleep_state")
    if state is None:
        return None
    return SLEEP_STATES.get(int(state), "unknown")


SENSORS: tuple[OwletSensorEntityDescription, ...] = (
    OwletSensorEntityDescription(
        key="heart_rate",
        translation_key="heart_rate",
        native_unit_of_measurement="bpm",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:heart-pulse",
        value_fn=lambda d: d.get("heart_rate"),
    ),
    OwletSensorEntityDescription(
        key="oxygen_saturation",
        translation_key="oxygen_saturation",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:percent",
        value_fn=lambda d: d.get("oxygen_saturation"),
    ),
    OwletSensorEntityDescription(
        key="oxygen_10_av",
        translation_key="oxygen_10_av",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        icon="mdi:percent-outline",
        value_fn=lambda d: d.get("oxygen_10_av"),
    ),
    OwletSensorEntityDescription(
        key="movement",
        translation_key="movement",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:run",
        value_fn=lambda d: d.get("movement"),
    ),
    OwletSensorEntityDescription(
        key="skin_temperature",
        translation_key="skin_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=lambda d: d.get("skin_temperature"),
    ),
    OwletSensorEntityDescription(
        key="battery_percentage",
        translation_key="battery_percentage",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("battery_percentage"),
    ),
    OwletSensorEntityDescription(
        key="battery_minutes",
        translation_key="battery_minutes",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:battery-clock",
        value_fn=lambda d: d.get("battery_minutes"),
    ),
    OwletSensorEntityDescription(
        key="signal_strength",
        translation_key="signal_strength",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda d: d.get("signal_strength"),
    ),
    OwletSensorEntityDescription(
        key="sleep_state",
        translation_key="sleep_state",
        device_class=SensorDeviceClass.ENUM,
        options=list(dict.fromkeys(SLEEP_STATES.values())),
        icon="mdi:sleep",
        value_fn=_sleep_state,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OwletConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Owlet sensors."""
    coordinator = entry.runtime_data
    entities: list[OwletSensor] = []
    for dsn in coordinator.devices:
        for description in SENSORS:
            entities.append(OwletSensor(coordinator, dsn, description))
    async_add_entities(entities)


class OwletSensor(OwletBaseEntity, SensorEntity):
    """Representation of an Owlet sensor."""

    entity_description: OwletSensorEntityDescription

    def __init__(
        self,
        coordinator,
        dsn: str,
        description: OwletSensorEntityDescription,
    ) -> None:
        """Initialise the sensor."""
        super().__init__(coordinator, dsn)
        self.entity_description = description
        self._attr_unique_id = f"{dsn}_{description.key}"

    @property
    def native_value(self) -> Any:
        """Return the current value."""
        return self.entity_description.value_fn(self.device_data)
