"""Exercise the real HA platform and registries across setup and reload."""

from unittest.mock import patch

import pytest
from custom_components.mydeltasolar.api import _normalize_telemetry
from custom_components.mydeltasolar.const import DOMAIN
from custom_components.mydeltasolar.sensor import (
    INVERTER_TELEMETRY_SENSORS,
    PLANT_SENSORS,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry


def _data():
    return _normalize_telemetry(
        {
            "plant_ID": [12345],
            "plant_name": ["HomeAuto"],
            "P_SN": {"12345": ["INV-001", "INV-002"]},
            "invid_arr": {"12345": [1, 2]},
            "invtp_arr": {"12345": ["H5A_220", "H5A_220"]},
        },
        {"te": [1190], "le": [6697770]},
        {"top": [1604]},
    )


@pytest.mark.parametrize("existing", [False, True], ids=["fresh", "v030-upgrade"])
async def test_registry_identity_and_parent_links(
    hass: HomeAssistant, existing: bool, caplog
) -> None:
    """Reuse old identities and link every inverter before and after reload."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="HomeAuto",
        data={"username": "test@example.invalid", "password": "test-only"},
    )
    entry.add_to_hass(hass)
    devices = dr.async_get(hass)
    entities = er.async_get(hass)
    data = _data()
    expected_unique_ids = {f"12345_{description.key}" for description in PLANT_SENSORS}
    for inverter in data.inverters:
        expected_unique_ids.update(
            f"12345_inverter_{inverter.index}_{key}"
            for key in (
                "last_update",
                "cloud_status",
                "last_seen_minutes",
                *(description.key for description in INVERTER_TELEMETRY_SENSORS),
            )
        )

    # Identical identifiers in another config entry must never steal the link.
    other_entry = MockConfigEntry(domain=DOMAIN, data={})
    other_entry.add_to_hass(hass)
    other_plant = devices.async_get_or_create(
        config_entry_id=other_entry.entry_id, identifiers={(DOMAIN, "12345")}
    )

    seeded_device_ids = set()
    seeded_entity_ids = {}
    if existing:
        plant = devices.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, "12345")},
            name="HomeAuto",
            manufacturer="Delta Electronics",
            model="MyDeltaSolar Plant",
        )
        devices.async_update_device(plant.id, name_by_user="My customized plant")
        seeded_device_ids.add(plant.id)
        inverter_devices = {}
        for inverter in data.inverters:
            device = devices.async_get_or_create(
                config_entry_id=entry.entry_id,
                identifiers={(DOMAIN, f"12345_{inverter.serial}")},
                name=f"HomeAuto Inverter {inverter.index}",
                manufacturer="Delta Electronics",
                model=inverter.model,
                via_device_id=plant.id,
            )
            inverter_devices[inverter.index] = device
            seeded_device_ids.add(device.id)
        # These are the identifiers and topology persisted by v0.3.0. Registry
        # snapshots store via_device_id even when old DeviceInfo used via_device.
        for unique_id in expected_unique_ids:
            device = plant
            if "_inverter_" in unique_id:
                device = inverter_devices[int(unique_id.split("_")[2])]
            registered = entities.async_get_or_create(
                "sensor",
                DOMAIN,
                unique_id,
                suggested_object_id=f"homeauto_{unique_id.removeprefix('12345_')}",
                config_entry=entry,
                device_id=device.id,
            )
            if unique_id == "12345_current_power_delta":
                entities.async_update_entity(
                    registered.entity_id, disabled_by=er.RegistryEntryDisabler.USER
                )
            if unique_id == "12345_lifetime_energy":
                entities.async_update_entity(
                    registered.entity_id, name="My energy total"
                )
            seeded_entity_ids[unique_id] = registered.entity_id
        assert (
            seeded_entity_ids["12345_lifetime_energy"]
            == "sensor.homeauto_lifetime_energy"
        )

    original_get_or_create = devices.async_get_or_create

    def checked_registration(**kwargs):
        assert "via_device" not in kwargs
        if "via_device_id" in kwargs:
            assert devices.async_get(kwargs["via_device_id"]) is not None
        return original_get_or_create(**kwargs)

    with (
        patch(
            "custom_components.mydeltasolar.coordinator.MyDeltaSolarClient.async_get_plant_telemetry",
            return_value=data,
        ),
        patch.object(devices, "async_get_or_create", side_effect=checked_registration),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        first_devices = dr.async_entries_for_config_entry(devices, entry.entry_id)
        first_entities = er.async_entries_for_config_entry(entities, entry.entry_id)
        assert len(first_devices) == 3
        assert {entity.unique_id for entity in first_entities} == expected_unique_ids
        first_device_ids = {device.id for device in first_devices}
        first_entity_ids = {
            entity.unique_id: entity.entity_id for entity in first_entities
        }
        if existing:
            assert first_device_ids == seeded_device_ids
            assert first_entity_ids == seeded_entity_ids
        lifetime = hass.states.get(first_entity_ids["12345_lifetime_energy"])
        assert lifetime is not None
        assert lifetime.state == "6697.77"
        assert lifetime.attributes["device_class"] == "energy"
        assert lifetime.attributes["state_class"] == "total_increasing"
        assert lifetime.attributes["unit_of_measurement"] == "kWh"

        for _ in range(2):
            assert await hass.config_entries.async_reload(entry.entry_id)
            await hass.async_block_till_done()
            current_devices = dr.async_entries_for_config_entry(devices, entry.entry_id)
            assert {device.id for device in current_devices} == first_device_ids
            current_entities = er.async_entries_for_config_entry(
                entities, entry.entry_id
            )
            assert {
                entity.unique_id: entity.entity_id for entity in current_entities
            } == first_entity_ids
            plant = next(
                device
                for device in current_devices
                if (DOMAIN, "12345") in device.identifiers
            )
            assert plant.id != other_plant.id
            assert plant.via_device_id is None
            if existing:
                assert plant.name_by_user == "My customized plant"
                assert (
                    entities.async_get("sensor.homeauto_lifetime_energy").name
                    == "My energy total"
                )
                disabled = entities.async_get(
                    seeded_entity_ids["12345_current_power_delta"]
                )
                assert disabled.disabled_by is er.RegistryEntryDisabler.USER
                assert hass.states.get(disabled.entity_id) is None
            for inverter in data.inverters:
                device = next(
                    device
                    for device in current_devices
                    if (DOMAIN, f"12345_{inverter.serial}") in device.identifiers
                )
                assert device.via_device_id == plant.id
                assert device.name == f"HomeAuto Inverter {inverter.index}"
                assert device.model == inverter.model
                assert device.manufacturer == "Delta Electronics"
                assert all(
                    entity.device_id == device.id
                    for entity in current_entities
                    if entity.unique_id.startswith(f"12345_inverter_{inverter.index}_")
                )
        assert "via_device" not in caplog.text
