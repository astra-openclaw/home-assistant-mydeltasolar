"""Tests for MyDeltaSolar API normalization."""

from custom_components.mydeltasolar.api import (
    _latest_plot_power_kw,
    _normalize_telemetry,
)


def _plant_payload() -> dict:
    return {
        "plant_ID": [12345],
        "plant_name": ["Example Plant"],
        "start_date": ["2023-03-18"],
        "location": ["Example City"],
        "country": ["Taiwan"],
        "timezone": ["8.00"],
        "tzID": ["Asia/Taipei"],
        "plt_status": [1],
        "event_num": [0],
        "P_SN": {"12345": ["INV-SERIAL-001", "INV-SERIAL-002", "INV-SERIAL-003"]},
        "P_cid": {"12345": [9001, 9002, 9003]},
        "P_INV_NUM": {"12345": ["1", "1", "1"]},
        "P_last_ts": {
            "12345": [
                "2026-02-04 17:15:04",
                "2026-01-11 17:45:10",
                "2026-05-10 18:15:00",
            ]
        },
        "invid_arr": {"12345": [1, 2, 3]},
        "invtp_arr": {"12345": ["H5A_220", "H5A_220", "H5A_220"]},
    }


def test_normalize_telemetry() -> None:
    """Normalize discovered MyDeltaSolar payload shape."""
    plant = _plant_payload()
    energy = {"te": [1190], "le": [6697770], "de": [149]}
    day = {"top": [0, None, 875, 1604]}
    month = {"energy": [None, 31580, 25380, 1190]}
    year = {"energy": [1317940, 438120, None, 193620]}

    data = _normalize_telemetry(plant, energy, day, month, year)

    assert data.plant_id == 12345
    assert data.plant_name == "Example Plant"
    assert data.status_code == 1
    assert data.status == "monitoring"
    assert data.country == "Taiwan"
    assert data.location == "Example City"
    assert data.timezone_id == "Asia/Taipei"
    assert data.event_count == 0
    assert data.today_energy_kwh == 1.19
    assert data.lifetime_energy_kwh == 6697.77
    assert data.current_power_kw == 1.604
    assert data.month_to_date_energy_kwh == 58.15
    assert data.year_to_date_energy_kwh == 1949.68
    assert len(data.inverters) == 3
    assert data.inverters[2].serial == "INV-SERIAL-003"
    assert data.inverters[2].model == "H5A_220"
    assert data.inverters[2].collector_id == 9003
    assert data.inverters[2].cloud_status in {"online", "stale"}


def test_current_power_ignores_stale_energy_de_field() -> None:
    """The energy payload's de field is stale at night; use day plot instead."""
    data = _normalize_telemetry(
        _plant_payload(),
        {"te": [1600], "le": [6800000], "de": [150]},
        {"top": [1200, 800, 0]},
    )

    assert data.current_power_kw == 0


def test_latest_plot_power_kw_accepts_watts_and_point_pairs() -> None:
    """Daily plot samples may be kW, W, or [timestamp, value] pairs."""
    assert _latest_plot_power_kw({"top": [0, 250, 1600]}) == 1.6
    assert _latest_plot_power_kw({"power": [0, 0.25, 1.6]}) == 1.6
    assert _latest_plot_power_kw({"data": [["08:00", 0.5], ["12:00", 1.75]]}) == 1.75
    assert _latest_plot_power_kw({"energy": [None, "bad", 0]}) == 0
