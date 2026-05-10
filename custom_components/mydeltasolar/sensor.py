"""Sensors for MyDeltaSolar."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import InverterInfo, PlantTelemetry
from .const import (
    ATTR_COLLECTOR_ID,
    ATTR_INVERTER_MODEL,
    ATTR_INVERTER_SERIAL,
    ATTR_PLANT_ID,
    ATTR_PLANT_NAME,
    DOMAIN,
)
from .coordinator import MyDeltaSolarDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class MyDeltaSolarSensorEntityDescription(SensorEntityDescription):
    """Describes a MyDeltaSolar plant sensor."""

    value_fn: Callable[[PlantTelemetry], Any]


PLANT_SENSORS: tuple[MyDeltaSolarSensorEntityDescription, ...] = (
    MyDeltaSolarSensorEntityDescription(
        key="current_power",
        translation_key="current_power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        value_fn=lambda data: data.current_power_kw,
    ),
    MyDeltaSolarSensorEntityDescription(
        key="today_energy",
        translation_key="today_energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=3,
        value_fn=lambda data: data.today_energy_kwh,
    ),
    MyDeltaSolarSensorEntityDescription(
        key="lifetime_energy",
        translation_key="lifetime_energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=3,
        value_fn=lambda data: data.lifetime_energy_kwh,
    ),
    MyDeltaSolarSensorEntityDescription(
        key="active_inverters",
        translation_key="active_inverters",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.active_inverter_count,
    ),
    MyDeltaSolarSensorEntityDescription(
        key="plant_status",
        translation_key="plant_status",
        value_fn=lambda data: data.status_code,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MyDeltaSolar sensors."""
    coordinator: MyDeltaSolarDataUpdateCoordinator = entry.runtime_data
    data = coordinator.data

    entities: list[SensorEntity] = [
        MyDeltaSolarPlantSensor(coordinator, description)
        for description in PLANT_SENSORS
    ]
    entities.extend(
        MyDeltaSolarInverterLastUpdateSensor(coordinator, inverter)
        for inverter in data.inverters
    )
    entities.extend(
        MyDeltaSolarInverterStatusSensor(coordinator, inverter)
        for inverter in data.inverters
    )
    async_add_entities(entities)


class MyDeltaSolarPlantSensor(
    CoordinatorEntity[MyDeltaSolarDataUpdateCoordinator], SensorEntity
):
    """Representation of a MyDeltaSolar plant sensor."""

    entity_description: MyDeltaSolarSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MyDeltaSolarDataUpdateCoordinator,
        description: MyDeltaSolarSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.data.plant_id}_{description.key}"
        self._attr_device_info = _plant_device_info(coordinator.data)

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return plant attributes."""
        return {
            ATTR_PLANT_ID: self.coordinator.data.plant_id,
            ATTR_PLANT_NAME: self.coordinator.data.plant_name,
        }


class MyDeltaSolarInverterLastUpdateSensor(
    CoordinatorEntity[MyDeltaSolarDataUpdateCoordinator], SensorEntity
):
    """Representation of an inverter last update timestamp sensor."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_translation_key = "inverter_last_update"

    def __init__(
        self,
        coordinator: MyDeltaSolarDataUpdateCoordinator,
        inverter: InverterInfo,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._inverter = inverter
        self._attr_unique_id = f"{coordinator.data.plant_id}_inverter_{inverter.index}_last_update"
        self._attr_device_info = _inverter_device_info(coordinator.data, inverter)

    @property
    def native_value(self) -> datetime | None:
        """Return the last update timestamp."""
        inverter = _find_inverter(self.coordinator.data, self._inverter.index)
        if inverter is None or inverter.last_update is None:
            return None
        try:
            return datetime.fromisoformat(inverter.last_update)
        except ValueError:
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return inverter attributes."""
        return _inverter_attributes(self._inverter)


class MyDeltaSolarInverterStatusSensor(
    CoordinatorEntity[MyDeltaSolarDataUpdateCoordinator], SensorEntity
):
    """Representation of an inverter cloud status sensor."""

    _attr_has_entity_name = True
    _attr_translation_key = "inverter_cloud_status"

    def __init__(
        self,
        coordinator: MyDeltaSolarDataUpdateCoordinator,
        inverter: InverterInfo,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._inverter = inverter
        self._attr_unique_id = f"{coordinator.data.plant_id}_inverter_{inverter.index}_cloud_status"
        self._attr_device_info = _inverter_device_info(coordinator.data, inverter)

    @property
    def native_value(self) -> str:
        """Return online if last cloud update is today, otherwise stale."""
        inverter = _find_inverter(self.coordinator.data, self._inverter.index)
        if inverter is None or inverter.last_update is None:
            return "unknown"
        try:
            return "online" if datetime.fromisoformat(inverter.last_update).date() == datetime.now().date() else "stale"
        except ValueError:
            return "unknown"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return inverter attributes."""
        return _inverter_attributes(self._inverter)


def _plant_device_info(data: PlantTelemetry) -> dict[str, Any]:
    return {
        "identifiers": {(DOMAIN, str(data.plant_id))},
        "name": data.plant_name,
        "manufacturer": "Delta Electronics",
        "model": "MyDeltaSolar Plant",
    }


def _inverter_device_info(data: PlantTelemetry, inverter: InverterInfo) -> dict[str, Any]:
    return {
        "identifiers": {(DOMAIN, f"{data.plant_id}_{inverter.serial}")},
        "name": f"{data.plant_name} Inverter {inverter.index}",
        "manufacturer": "Delta Electronics",
        "model": inverter.model,
        "via_device": (DOMAIN, str(data.plant_id)),
    }


def _find_inverter(data: PlantTelemetry, index: int) -> InverterInfo | None:
    return next((inverter for inverter in data.inverters if inverter.index == index), None)


def _inverter_attributes(inverter: InverterInfo) -> dict[str, Any]:
    return {
        ATTR_INVERTER_SERIAL: inverter.serial,
        ATTR_INVERTER_MODEL: inverter.model,
        ATTR_COLLECTOR_ID: inverter.collector_id,
    }
