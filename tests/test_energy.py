"""Regression coverage for midnight rollover and persistent energy guards."""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from custom_components.mydeltasolar.energy import (
    INVERTER_MAX_KW,
    LIFETIME_RESET_DELAY,
    PLANT_MAX_KW,
    EnergyGuard,
    plant_timezone,
)

TAIPEI = ZoneInfo("Asia/Taipei")
GAP = timedelta(minutes=10)


def _at(hour: int, minute: int = 0, day: int = 4) -> datetime:
    return datetime(2026, 10, day, hour, minute, tzinfo=TAIPEI)


def _observe(guard: EnergyGuard, value, now) -> float | None:
    guard.observe(value, now, max_gap=GAP, label="test_counter")
    return guard.value


@pytest.mark.parametrize("max_kw", [PLANT_MAX_KW, INVERTER_MAX_KW])
def test_today_bound_and_monotonic_growth(max_kw) -> None:
    """A rejected first sample cannot let a second bogus sample through."""
    guard = EnergyGuard(daily=True, max_kw=max_kw)
    assert _observe(guard, 26.25, _at(0, 3)) == 0
    assert _observe(guard, 26.25, _at(0, 4)) == 0
    assert _observe(guard, 0, _at(0, 8)) == 0
    assert _observe(guard, 3, _at(8)) == 3
    assert _observe(guard, 2, _at(8, 5)) == 3
    assert _observe(guard, 4, _at(8, 10)) == 4
    assert _observe(guard, 5, _at(9)) == 5
    assert _observe(guard, 26.25, _at(0, 3, day=5)) == 0
    assert _observe(guard, 0.5, _at(0, 4, day=5)) == 0.5


def test_today_exact_bound_and_dst_elapsed_hours() -> None:
    """Use real elapsed time from local midnight on daylight-saving days."""
    zone = ZoneInfo("America/New_York")
    guard = EnergyGuard(daily=True, max_kw=INVERTER_MAX_KW)
    assert _observe(guard, 0.001, _at(0)) == 0
    assert _observe(guard, 5, _at(0, 30)) == 5
    spring = datetime(2026, 3, 8, 3, tzinfo=zone)
    assert _observe(guard, 21, spring) == 0  # Only two physical hours elapsed.
    assert _observe(guard, 20, spring) == 20
    fall = datetime(2026, 11, 1, 2, tzinfo=zone)
    assert _observe(guard, 30, fall) == 30  # Three physical hours elapsed.


def test_lifetime_reset_after_six_continuous_hours(caplog) -> None:
    """Accept a replacement counter only once six hours of lower polls pass."""
    guard = EnergyGuard(daily=False, max_kw=PLANT_MAX_KW)
    start = _at(0)
    assert _observe(guard, 100, start - timedelta(minutes=5)) == 100
    for minutes in range(0, 360, 5):
        # The replacement counter may grow while remaining below the old total.
        assert (
            _observe(guard, 10 + minutes / 60, start + timedelta(minutes=minutes))
            == 100
        )
    assert "accepting lifetime energy reset" not in caplog.text
    assert _observe(guard, 16, start + LIFETIME_RESET_DELAY) == 16
    assert caplog.text.count("accepting lifetime energy reset") == 1
    assert (
        _observe(guard, 17, start + LIFETIME_RESET_DELAY + timedelta(minutes=5)) == 17
    )


@pytest.mark.parametrize(
    "interruption", ["recovered", "missing", "failed", "gap", "clock"]
)
def test_lifetime_lower_streak_must_be_continuous(interruption, caplog) -> None:
    """Recoveries, missing/failed polls, outages and clock reversals restart it."""
    guard = EnergyGuard(daily=False, max_kw=PLANT_MAX_KW)
    start = _at(0)
    _observe(guard, 100, start)
    for minutes in range(5, 360, 5):
        _observe(guard, 10, start + timedelta(minutes=minutes))
    now = start + timedelta(hours=6)
    if interruption == "recovered":
        _observe(guard, 100, now)
    elif interruption == "missing":
        _observe(guard, None, now)
    elif interruption == "failed":
        guard.interrupt()
    elif interruption == "gap":
        now += timedelta(hours=6)
    else:
        now = start
    assert _observe(guard, 10, now + timedelta(minutes=5)) == 100
    assert "accepting lifetime energy reset" not in caplog.text


@pytest.mark.parametrize("daily", [False, True])
@pytest.mark.parametrize("invalid", [None, float("nan"), float("inf"), -1, "bad"])
def test_invalid_energy_does_not_poison_guard(daily, invalid) -> None:
    guard = EnergyGuard(daily=daily, max_kw=PLANT_MAX_KW)
    assert _observe(guard, 10, _at(12)) == 10
    assert _observe(guard, invalid, _at(12, 5)) == 10
    assert _observe(guard, 11, _at(12, 10)) == 11


@pytest.mark.parametrize(
    ("zone", "offset", "fallback", "expected_hours"),
    [
        ("Asia/Taipei", "0", "UTC", 8),
        (None, "8.00", "UTC", 8),
        ("bad/zone", "5.5", "UTC", 5.5),
        ("bad/zone", "bad", "Asia/Taipei", 8),
        (None, None, "Asia/Taipei", 8),
        (None, "nan", "Asia/Taipei", 8),
        (None, "25", "Asia/Taipei", 8),
    ],
)
def test_plant_timezone_fallbacks(zone, offset, fallback, expected_hours) -> None:
    tz = plant_timezone(zone, offset, fallback)
    assert _at(12).astimezone(tz).utcoffset().total_seconds() == expected_hours * 3600


def test_restore_lower_streak_and_outage(caplog) -> None:
    guard = EnergyGuard(daily=False, max_kw=PLANT_MAX_KW)
    guard.restore(
        100,
        {"lower_since": _at(0).isoformat(), "last_lower_seen": _at(5, 55).isoformat()},
    )
    assert _observe(guard, 10, _at(6)) == 10
    assert "accepting lifetime energy reset" in caplog.text
    guard.restore(
        100,
        {"lower_since": _at(0).isoformat(), "last_lower_seen": _at(5, 55).isoformat()},
    )
    assert _observe(guard, 10, _at(12)) == 100
    assert guard.lower_since == _at(12).astimezone(UTC)


def test_restore_corrupt_metadata_is_safe() -> None:
    guard = EnergyGuard(daily=False, max_kw=PLANT_MAX_KW)
    guard.restore(100, {"day": "bad", "lower_since": "bad", "last_lower_seen": "bad"})
    assert _observe(guard, 10, _at(6)) == 100
    guard.restore(float("nan"), {})
    assert guard.value is None
