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
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import InverterInfo, InverterTelemetry, PlantTelemetry
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


@dataclass(frozen=True, kw_only=True)
class MyDeltaSolarInverterSensorEntityDescription(SensorEntityDescription):
    """Describes a MyDeltaSolar inverter sensor."""

    value_fn: Callable[[InverterTelemetry], Any]


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
        key="calculated_current_power",
        translation_key="calculated_current_power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        value_fn=lambda data: data.calculated_current_power_kw,
    ),
    MyDeltaSolarSensorEntityDescription(
        key="current_power_delta",
        translation_key="current_power_delta",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        value_fn=lambda data: data.current_power_delta_kw,
    ),
    MyDeltaSolarSensorEntityDescription(
        key="current_power_delta_percent",
        translation_key="current_power_delta_percent",
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data.current_power_delta_percent,
    ),
    MyDeltaSolarSensorEntityDescription(
        key="live_inverters",
        translation_key="live_inverters",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.live_inverter_count,
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
        key="month_to_date_energy",
        translation_key="month_to_date_energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=3,
        value_fn=lambda data: data.month_to_date_energy_kwh,
    ),
    MyDeltaSolarSensorEntityDescription(
        key="year_to_date_energy",
        translation_key="year_to_date_energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=3,
        value_fn=lambda data: data.year_to_date_energy_kwh,
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
        value_fn=lambda data: data.status,
    ),
    MyDeltaSolarSensorEntityDescription(
        key="event_count",
        translation_key="event_count",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.event_count,
    ),
)


INVERTER_TELEMETRY_SENSORS: tuple[MyDeltaSolarInverterSensorEntityDescription, ...] = (
    MyDeltaSolarInverterSensorEntityDescription(
        key="inverter_status",
        translation_key="inverter_status",
        value_fn=lambda data: data.status,
    ),
    MyDeltaSolarInverterSensorEntityDescription(
        key="inverter_today_energy",
        translation_key="inverter_today_energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=3,
        value_fn=lambda data: data.today_energy_kwh,
    ),
    MyDeltaSolarInverterSensorEntityDescription(
        key="inverter_lifetime_energy",
        translation_key="inverter_lifetime_energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=3,
        value_fn=lambda data: data.lifetime_energy_kwh,
    ),
    MyDeltaSolarInverterSensorEntityDescription(
        key="inverter_output_power",
        translation_key="inverter_output_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda data: data.total_ac_power_w,
    ),
    MyDeltaSolarInverterSensorEntityDescription(
        key="inverter_output_voltage",
        translation_key="inverter_output_voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: _first_tuple(data.ac_voltage_v),
    ),
    MyDeltaSolarInverterSensorEntityDescription(
        key="inverter_output_current",
        translation_key="inverter_output_current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda data: _first_tuple(data.ac_current_a),
    ),
    MyDeltaSolarInverterSensorEntityDescription(
        key="inverter_dc_power",
        translation_key="inverter_dc_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda data: data.total_dc_power_w,
    ),
    MyDeltaSolarInverterSensorEntityDescription(
        key="inverter_dc_voltage",
        translation_key="inverter_dc_voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: _first_tuple(data.dc_voltage_v),
    ),
    MyDeltaSolarInverterSensorEntityDescription(
        key="inverter_dc_current",
        translation_key="inverter_dc_current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda data: _first_tuple(data.dc_current_a),
    ),
    MyDeltaSolarInverterSensorEntityDescription(
        key="inverter_telemetry_last_sample",
        translation_key="inverter_telemetry_last_sample",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: data.last_sample,
    ),
    MyDeltaSolarInverterSensorEntityDescription(
        key="inverter_telemetry_portal_update",
        translation_key="inverter_telemetry_portal_update",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: data.portal_update,
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
    entities.extend(
        MyDeltaSolarInverterLastSeenSensor(coordinator, inverter)
        for inverter in data.inverters
    )
    for inverter in data.inverters:
        entities.extend(
            MyDeltaSolarInverterTelemetrySensor(coordinator, inverter, description)
            for description in INVERTER_TELEMETRY_SENSORS
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
            "status_code": self.coordinator.data.status_code,
            "country": self.coordinator.data.country,
            "location": self.coordinator.data.location,
            "timezone": self.coordinator.data.timezone,
            "timezone_id": self.coordinator.data.timezone_id,
            "start_date": self.coordinator.data.start_date,
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
        self._attr_unique_id = (
            f"{coordinator.data.plant_id}_inverter_{inverter.index}_last_update"
        )
        self._attr_device_info = _inverter_device_info(coordinator.data, inverter)

    @property
    def native_value(self) -> datetime | None:
        """Return the last update timestamp."""
        inverter = _find_inverter(self.coordinator.data, self._inverter.index)
        return inverter.last_update_datetime if inverter else None

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
        self._attr_unique_id = (
            f"{coordinator.data.plant_id}_inverter_{inverter.index}_cloud_status"
        )
        self._attr_device_info = _inverter_device_info(coordinator.data, inverter)

    @property
    def native_value(self) -> str:
        """Return online if last cloud update is today, otherwise stale."""
        inverter = _find_inverter(self.coordinator.data, self._inverter.index)
        return inverter.cloud_status if inverter else "unknown"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return inverter attributes."""
        return _inverter_attributes(self._inverter)


class MyDeltaSolarInverterLastSeenSensor(
    CoordinatorEntity[MyDeltaSolarDataUpdateCoordinator], SensorEntity
):
    """Representation of an inverter last-seen age sensor."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "min"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_translation_key = "inverter_last_seen_minutes"

    def __init__(
        self,
        coordinator: MyDeltaSolarDataUpdateCoordinator,
        inverter: InverterInfo,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._inverter = inverter
        self._attr_unique_id = (
            f"{coordinator.data.plant_id}_inverter_{inverter.index}_last_seen_minutes"
        )
        self._attr_device_info = _inverter_device_info(coordinator.data, inverter)

    @property
    def native_value(self) -> int | None:
        """Return minutes since last cloud update."""
        inverter = _find_inverter(self.coordinator.data, self._inverter.index)
        return inverter.last_seen_minutes if inverter else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return inverter attributes."""
        return _inverter_attributes(self._inverter)


class MyDeltaSolarInverterTelemetrySensor(
    CoordinatorEntity[MyDeltaSolarDataUpdateCoordinator], SensorEntity
):
    """Representation of an inverter telemetry sensor."""

    entity_description: MyDeltaSolarInverterSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MyDeltaSolarDataUpdateCoordinator,
        inverter: InverterInfo,
        description: MyDeltaSolarInverterSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._inverter = inverter
        self.entity_description = description
        self._attr_unique_id = (
            f"{coordinator.data.plant_id}_inverter_{inverter.index}_{description.key}"
        )
        self._attr_device_info = _inverter_device_info(coordinator.data, inverter)

    @property
    def native_value(self) -> Any:
        """Return the inverter telemetry value."""
        inverter = _find_inverter(self.coordinator.data, self._inverter.index)
        if inverter is None or inverter.telemetry is None:
            return None
        return self.entity_description.value_fn(inverter.telemetry)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return inverter attributes."""
        inverter = _find_inverter(self.coordinator.data, self._inverter.index)
        attrs = _inverter_attributes(inverter or self._inverter)
        telemetry = inverter.telemetry if inverter else None
        if telemetry is not None:
            attrs.update(
                {
                    "status_code": telemetry.status_code,
                    "dc_voltage_channels": telemetry.dc_voltage_v,
                    "dc_current_channels": telemetry.dc_current_a,
                    "dc_power_channels": telemetry.dc_power_w,
                    "ac_voltage_channels": telemetry.ac_voltage_v,
                    "ac_current_channels": telemetry.ac_current_a,
                    "ac_power_channels": telemetry.ac_power_w,
                }
            )
        return attrs


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
        "inverter_id": inverter.inverter_id,
    }


def _first_tuple(values: tuple[float, ...]) -> float | None:
    return values[0] if values else None
