"""Stateful protection against partially rolled-over Delta cloud energy totals."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta, timezone, tzinfo
from math import isfinite
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

_LOGGER = logging.getLogger(__name__)

PLANT_MAX_KW = 25.0
INVERTER_MAX_KW = 10.0
LIFETIME_RESET_DELAY = timedelta(hours=6)


def plant_timezone(
    timezone_id: str | None, offset: str | None, fallback: str
) -> tzinfo:
    """Prefer the plant's IANA zone, then its UTC-hour offset, then HA's zone."""
    if timezone_id:
        try:
            return ZoneInfo(timezone_id)
        except ValueError, ZoneInfoNotFoundError:
            pass
    if offset is not None:
        try:
            return timezone(timedelta(hours=float(offset)))
        except TypeError, ValueError, OverflowError:
            pass
    return ZoneInfo(fallback)


def _energy(value: Any) -> float | None:
    """Ignore missing, non-finite and negative readings (including restored data)."""
    try:
        number = float(value)
    except TypeError, ValueError, OverflowError:
        return None
    return number if isfinite(number) and number >= 0 else None


def _datetime(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value)
    except TypeError, ValueError:
        return None
    return parsed.astimezone(UTC) if parsed.tzinfo is not None else None


@dataclass
class EnergyGuard:
    """Guard one counter; only fresh coordinator observations advance its state."""

    daily: bool
    max_kw: float
    value: float | None = None
    day: date | None = None
    lower_since: datetime | None = None
    last_lower_seen: datetime | None = None

    def interrupt(self) -> None:
        """Missing/failed polls cannot establish a continuous lower counter."""
        self.lower_since = None
        self.last_lower_seen = None

    def observe(
        self,
        raw: float | None,
        now: datetime,
        *,
        max_gap: timedelta,
        label: str,
    ) -> None:
        """Accept sane growth, daily resets, or a confirmed lifetime reset."""
        reading = _energy(raw)
        if self.daily:
            if self.day != now.date():
                self.day = now.date()
                self.value = 0.0
            midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
            hours = (
                now.astimezone(UTC) - midnight.astimezone(UTC)
            ).total_seconds() / 3600
            # Check every poll, not just the first rejected poll of a new day.
            if reading is not None and reading <= max(0.0, hours) * self.max_kw:
                self.value = max(self.value or 0.0, reading)
            return

        if reading is None:
            self.interrupt()
            return
        if self.value is None or reading >= self.value:
            self.value = reading
            self.interrupt()
            return

        utc_now = now.astimezone(UTC)
        if (
            self.lower_since is None
            or self.last_lower_seen is None
            or not timedelta(0) <= utc_now - self.last_lower_seen <= max_gap
        ):
            self.lower_since = utc_now
        self.last_lower_seen = utc_now
        if utc_now - self.lower_since >= LIFETIME_RESET_DELAY:
            _LOGGER.warning(
                "%s: accepting lifetime energy reset from %s to %s kWh after "
                "six hours of continuously lower readings",
                label,
                self.value,
                reading,
            )
            self.value = reading
            self.interrupt()

    def as_dict(self) -> dict[str, Any]:
        """Serialize guard metadata alongside RestoreSensor's native value."""
        return {
            "day": self.day.isoformat() if self.day else None,
            "lower_since": self.lower_since.isoformat() if self.lower_since else None,
            "last_lower_seen": self.last_lower_seen.isoformat()
            if self.last_lower_seen
            else None,
        }

    def restore(self, value: Any, metadata: dict[str, Any]) -> None:
        """Restore the accepted counter and its day/reset streak before polling."""
        self.value = _energy(value)
        if self.value is None:
            return
        try:
            self.day = date.fromisoformat(metadata.get("day"))
        except TypeError, ValueError:
            self.day = None
        self.lower_since = _datetime(metadata.get("lower_since"))
        self.last_lower_seen = _datetime(metadata.get("last_lower_seen"))
        if (
            self.lower_since is None
            or self.last_lower_seen is None
            or self.lower_since > self.last_lower_seen
        ):
            self.interrupt()
