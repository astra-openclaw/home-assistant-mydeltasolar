"""Exercise energy filtering and restore through the real HA sensor platform."""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from custom_components.mydeltasolar.api import _normalize_telemetry
from custom_components.mydeltasolar.const import DOMAIN
from homeassistant.components.sensor import RestoreSensor
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    mock_restore_cache,
)

BASE_TIME = datetime(2026, 10, 3, 15, 55, tzinfo=UTC)  # Taipei 23:55


def _data(lifetime=16363.25, today=79.71, inverter_totals=None):
    if inverter_totals is None:
        inverter_totals = [(5000, 27.05), (6000, 26.41), (5363.25, 26.25)]
    return _normalize_telemetry(
        {
            "plant_ID": [12345],
            "plant_name": ["HomeAuto"],
            "tzID": ["Asia/Taipei"],
            "timezone": ["8.00"],
            "P_SN": {"12345": ["INV-001", "INV-002", "INV-003"]},
            "invid_arr": {"12345": [1, 2, 3]},
            "invtp_arr": {"12345": ["H5A_220"] * 3},
        },
        {"te": [today * 1000], "le": [lifetime * 1000]},
        {"top": [0]},
        inverter_payloads={
            f"INV-{index:03}": {
                "result": {
                    f"INV-{index:03}": {
                        str(index): {"male": le * 1000, "te": te * 1000}
                    }
                }
            }
            for index, (le, te) in enumerate(inverter_totals, 1)
        },
    )


@pytest.fixture
async def solar(hass: HomeAssistant, freezer):
    freezer.move_to(BASE_TIME)
    # Deliberately not the plant's zone: the API zone must win.
    await hass.config.async_update(time_zone="America/Los_Angeles")
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="HomeAuto",
        data={"username": "test@example.invalid", "password": "test-only"},
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.mydeltasolar.coordinator.MyDeltaSolarClient.async_get_plant_telemetry",
        return_value=_data(),
    ) as api:
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        yield entry, api


def _state(hass, key, index=None):
    unique_id = (
        f"12345_{key}" if index is None else f"12345_inverter_{index}_inverter_{key}"
    )
    entity_id = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, unique_id)
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.attributes["state_class"] == "total_increasing"
    assert state.attributes["device_class"] == "energy"
    assert state.attributes["unit_of_measurement"] == "kWh"
    return float(state.state)


async def test_replay_midnight_plant_and_all_inverters(hass, freezer, solar) -> None:
    """Replay the exact plant dip and asynchronous rollover for three inverters."""
    entry, _api = solar
    assert _state(hass, "lifetime_energy") == 16363.25
    assert _state(hass, "today_energy") == 79.71
    freezer.move_to("2026-10-03T16:03:00+00:00")
    entry.runtime_data.async_set_updated_data(
        _data(16309.79, 26.25, [(4972.95, 0), (5973.59, 0), (5363.25, 26.25)])
    )
    await hass.async_block_till_done()
    assert _state(hass, "lifetime_energy") == 16363.25
    assert _state(hass, "today_energy") == 0
    for index, lifetime in enumerate((5000, 6000, 5363.25), 1):
        assert _state(hass, "lifetime_energy", index) == lifetime
        assert _state(hass, "today_energy", index) == 0
    freezer.move_to("2026-10-03T16:08:00+00:00")
    entry.runtime_data.async_set_updated_data(
        _data(16363.25, 0, [(5000, 0), (6000, 0), (5363.25, 0)])
    )
    await hass.async_block_till_done()
    assert _state(hass, "lifetime_energy") == 16363.25
    assert _state(hass, "today_energy") == 0
    # Real daytime growth and same-day lower totals on every energy sensor.
    for hour, lifetime, today in [
        (8, 16366.25, 3),
        (9, 16365.25, 2),
        (10, 16369.25, 6),
    ]:
        freezer.move_to(f"2026-10-04T{hour - 8:02}:00:00+00:00")
        entry.runtime_data.async_set_updated_data(
            _data(lifetime, today, [(5000 + today, today)] * 3)
        )
        await hass.async_block_till_done()
        assert _state(hass, "lifetime_energy") == (16366.25 if hour == 9 else lifetime)
        assert _state(hass, "today_energy") == (3 if hour == 9 else today)
        for index in range(1, 4):
            assert _state(hass, "today_energy", index) == (3 if hour == 9 else today)


async def test_guard_state_survives_reload_before_first_reading(
    hass, freezer, solar
) -> None:
    """RestoreSensor holds the first post-restart dip, including same-day today."""
    entry, api = solar
    api.return_value = _data(16309.79, 70, [(4972.95, 26), (5973.59, 25), (5360, 24)])
    freezer.move_to(BASE_TIME + timedelta(minutes=1))
    with patch.object(
        RestoreSensor,
        "async_get_last_sensor_data",
        autospec=True,
        side_effect=RestoreSensor.async_get_last_sensor_data,
    ) as restore:
        assert await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
        assert restore.await_count == 8
    assert _state(hass, "lifetime_energy") == 16363.25
    assert _state(hass, "today_energy") == 79.71
    for index, (le, te) in enumerate(
        [(5000, 27.05), (6000, 26.41), (5363.25, 26.25)], 1
    ):
        assert _state(hass, "lifetime_energy", index) == le
        assert _state(hass, "today_energy", index) == te
    # Restart into the new local day still rejects the cloud's previous-day te.
    freezer.move_to("2026-10-03T16:03:00+00:00")
    api.return_value = _data(
        16309.79, 26.25, [(4972.95, 27.05), (5973.59, 26.41), (5360, 26.25)]
    )
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert _state(hass, "lifetime_energy") == 16363.25
    assert _state(hass, "today_energy") == 0
    for index in range(1, 4):
        assert _state(hass, "today_energy", index) == 0


async def test_restore_pending_reset_then_confirm(hass, freezer, solar, caplog) -> None:
    """Persist the lower streak as well as the accepted native kWh counter."""
    entry, api = solar
    reset = _data(100, 0, [(10, 0)] * 3)
    for minutes in range(5, 361, 5):
        freezer.move_to(BASE_TIME + timedelta(minutes=minutes))
        entry.runtime_data.async_set_updated_data(reset)
    await hass.async_block_till_done()
    assert _state(hass, "lifetime_energy") == 16363.25
    for index in range(1, 4):
        assert _state(hass, "lifetime_energy", index) > 10
    api.return_value = reset
    freezer.move_to(BASE_TIME + timedelta(minutes=365))
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert _state(hass, "lifetime_energy") == 100
    for index in range(1, 4):
        assert _state(hass, "lifetime_energy", index) == 10
    assert caplog.text.count("accepting lifetime energy reset") == 4


async def test_upgrade_restores_legacy_plain_state(hass, freezer) -> None:
    """Old releases have no native sensor extra data; use the public last state."""
    freezer.move_to(BASE_TIME)
    mock_restore_cache(
        hass,
        [
            State(
                "sensor.homeauto_lifetime_energy",
                "17000",
                {"unit_of_measurement": "kWh"},
                last_updated=BASE_TIME,
            ),
            State(
                "sensor.homeauto_today_energy",
                "85",
                {"unit_of_measurement": "kWh"},
                last_updated=BASE_TIME,
            ),
        ],
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"username": "test@example.invalid", "password": "test-only"},
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.mydeltasolar.coordinator.MyDeltaSolarClient.async_get_plant_telemetry",
        return_value=_data(),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    assert _state(hass, "lifetime_energy") == 17000
    assert _state(hass, "today_energy") == 85
