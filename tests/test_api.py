"""Tests for MyDeltaSolar API normalization."""

from custom_components.mydeltasolar.api import _normalize_telemetry


def test_normalize_telemetry() -> None:
    """Normalize discovered MyDeltaSolar payload shape."""
    plant = {
        "plant_ID": [47858],
        "plant_name": ["HomeAuto"],
        "start_date": ["2023-03-18"],
        "location": ["Tainan City"],
        "country": ["Taiwan"],
        "timezone": ["8.00"],
        "tzID": ["Asia/Taipei"],
        "plt_status": [1],
        "event_num": [0],
        "P_SN": {"47858": ["O5P20B01745WM", "O5P20B01748WM", "O5P20B01754WM"]},
        "P_cid": {"47858": [26171, 26170, 26169]},
        "P_INV_NUM": {"47858": ["1", "1", "1"]},
        "P_last_ts": {
            "47858": [
                "2026-02-04 17:15:04",
                "2026-01-11 17:45:10",
                "2026-05-10 18:15:00",
            ]
        },
        "invid_arr": {"47858": [1, 2, 3]},
        "invtp_arr": {"47858": ["H5A_220", "H5A_220", "H5A_220"]},
    }
    energy = {"te": [1190], "le": [6697770], "de": [149]}
    month = {"energy": [None, 31580, 25380, 1190]}
    year = {"energy": [1317940, 438120, None, 193620]}

    data = _normalize_telemetry(plant, energy, month, year)

    assert data.plant_id == 47858
    assert data.plant_name == "HomeAuto"
    assert data.status_code == 1
    assert data.status == "monitoring"
    assert data.country == "Taiwan"
    assert data.location == "Tainan City"
    assert data.timezone_id == "Asia/Taipei"
    assert data.event_count == 0
    assert data.today_energy_kwh == 1.19
    assert data.lifetime_energy_kwh == 6697.77
    assert data.current_power_kw == 0.149
    assert data.month_to_date_energy_kwh == 58.15
    assert data.year_to_date_energy_kwh == 1949.68
    assert len(data.inverters) == 3
    assert data.inverters[2].serial == "O5P20B01754WM"
    assert data.inverters[2].model == "H5A_220"
    assert data.inverters[2].collector_id == 26169
    assert data.inverters[2].cloud_status in {"online", "stale"}
