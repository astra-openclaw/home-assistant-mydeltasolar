"""Client for the MyDeltaSolar cloud portal."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from aiohttp import ClientError, ClientSession

from .const import BASE_URL

PLANT_STATUS = {
    0: "not_activated",
    1: "monitoring",
    2: "fault",
    3: "error",
    4: "warning",
    5: "disconnect",
}


class MyDeltaSolarError(Exception):
    """Base MyDeltaSolar API error."""


class MyDeltaSolarAuthError(MyDeltaSolarError):
    """Raised when authentication fails."""


class MyDeltaSolarFormatError(MyDeltaSolarError):
    """Raised when MyDeltaSolar returns an unexpected payload."""


@dataclass(slots=True, frozen=True)
class InverterInfo:
    """Cloud metadata for a Delta inverter/data collector."""

    index: int
    serial: str
    model: str | None
    collector_id: int | None
    inverter_id: int | None
    last_update: str | None
    timezone_id: str | None = None

    @property
    def last_update_datetime(self) -> datetime | None:
        """Return last update as a datetime, if parseable."""
        if self.last_update is None:
            return None
        try:
            parsed = datetime.fromisoformat(self.last_update)
        except ValueError:
            return None
        if parsed.tzinfo is not None:
            return parsed
        timezone_id = self.timezone_id or "UTC"
        try:
            return parsed.replace(tzinfo=ZoneInfo(timezone_id))
        except Exception:
            return parsed.replace(tzinfo=ZoneInfo("UTC"))

    @property
    def last_seen_minutes(self) -> int | None:
        """Return minutes since last cloud update."""
        last_update = self.last_update_datetime
        if last_update is None:
            return None
        delta = datetime.now(tz=last_update.tzinfo) - last_update
        return max(0, int(delta.total_seconds() // 60))

    @property
    def cloud_status(self) -> str:
        """Return online if last cloud update is today, otherwise stale."""
        last_update = self.last_update_datetime
        if last_update is None:
            return "unknown"
        return "online" if last_update.date() == datetime.now(tz=last_update.tzinfo).date() else "stale"


@dataclass(slots=True, frozen=True)
class PlantTelemetry:
    """Normalized MyDeltaSolar plant telemetry."""

    plant_id: int
    plant_name: str
    status_code: int | None
    status: str | None
    country: str | None
    location: str | None
    timezone: str | None
    timezone_id: str | None
    start_date: str | None
    event_count: int | None
    today_energy_kwh: float | None
    lifetime_energy_kwh: float | None
    current_power_kw: float | None
    month_to_date_energy_kwh: float | None
    year_to_date_energy_kwh: float | None
    inverters: tuple[InverterInfo, ...]
    raw_plant: dict[str, Any]
    raw_energy: dict[str, Any]
    raw_day: dict[str, Any] | None
    raw_month: dict[str, Any] | None
    raw_year: dict[str, Any] | None

    @property
    def active_inverter_count(self) -> int:
        """Return count of inverters with a last update date matching today."""
        return sum(1 for inverter in self.inverters if inverter.cloud_status == "online")


class MyDeltaSolarClient:
    """Minimal async client for MyDeltaSolar's web endpoints."""

    def __init__(
        self,
        session: ClientSession,
        username: str,
        password: str,
        base_url: str = BASE_URL,
    ) -> None:
        """Initialize the client."""
        self._session = session
        self._username = username
        self._password = password
        self._base_url = base_url.rstrip("/") + "/"
        self._logged_in = False

    async def async_login(self) -> None:
        """Log in to MyDeltaSolar."""
        await self._request("GET", "login", expected_json=False)
        payload = await self._request(
            "POST",
            "web/process_login.php",
            data={"email": self._username, "password": self._password},
            headers={
                "Origin": self._base_url.rstrip("/"),
                "Referer": self._base_url + "login",
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        if not isinstance(payload, dict):
            raise MyDeltaSolarAuthError("Login returned an unexpected response")
        if payload.get("errmsg"):
            raise MyDeltaSolarAuthError(str(payload["errmsg"]))
        self._logged_in = True

    async def async_get_plant_telemetry(self) -> PlantTelemetry:
        """Fetch and normalize plant telemetry."""
        if not self._logged_in:
            await self.async_login()

        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Referer": self._base_url + "m_gtop",
        }
        plant = await self._request("GET", "web/process_init_plant.php", headers=headers)
        energy = await self._request(
            "POST",
            "web/process_init_energy.php",
            data={"is_all_plants": "1"},
            headers=headers,
        )
        day = await self._request(
            "POST",
            "web/process_gtop_plot.php",
            data={"unit": "day", "is_all_plants": "1"},
            headers=headers,
        )
        month = await self._request(
            "POST",
            "web/process_gtop_plot.php",
            data={"unit": "month", "is_all_plants": "1"},
            headers=headers,
        )
        year = await self._request(
            "POST",
            "web/process_gtop_plot.php",
            data={"unit": "year", "is_all_plants": "1"},
            headers=headers,
        )

        if not isinstance(plant, dict) or not isinstance(energy, dict):
            raise MyDeltaSolarFormatError("Telemetry response was not JSON object")
        return _normalize_telemetry(
            plant,
            energy,
            day if isinstance(day, dict) else None,
            month if isinstance(month, dict) else None,
            year if isinstance(year, dict) else None,
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        expected_json: bool = True,
    ) -> Any:
        url = self._base_url + path.lstrip("/")
        try:
            async with self._session.request(
                method,
                url,
                data=data,
                headers={
                    "User-Agent": "Mozilla/5.0 HomeAssistant-MyDeltaSolar/0.1",
                    **(headers or {}),
                },
                timeout=30,
            ) as response:
                text = await response.text()
                if response.status >= 400:
                    raise MyDeltaSolarError(
                        f"MyDeltaSolar returned HTTP {response.status} for {path}: {text[:120]}"
                    )
                if not expected_json:
                    return text
                try:
                    return await response.json(content_type=None)
                except Exception as err:
                    raise MyDeltaSolarFormatError(
                        f"MyDeltaSolar returned non-JSON payload for {path}"
                    ) from err
        except ClientError as err:
            raise MyDeltaSolarError("Unable to reach MyDeltaSolar") from err


def _first(values: list[Any] | None, default: Any = None) -> Any:
    if not values:
        return default
    return values[0]


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _wh_to_kwh(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return round(float(value) / 1000, 3)
    except (TypeError, ValueError):
        return None


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _sum_wh_to_kwh(values: list[Any] | None) -> float | None:
    if values is None:
        return None
    total = 0.0
    found = False
    for value in values:
        if value is None:
            continue
        try:
            total += float(value)
        except (TypeError, ValueError):
            continue
        found = True
    return round(total / 1000, 3) if found else None


def _latest_plot_power_kw(day: dict[str, Any] | None) -> float | None:
    """Return the most recent power sample from the daily production plot."""
    if not day:
        return None

    values = day.get("top")
    if values is None:
        values = day.get("power") or day.get("kw") or day.get("kW")
    if values is None:
        values = day.get("data") or day.get("energy")
    if not isinstance(values, list):
        return None

    for value in reversed(values):
        if isinstance(value, (list, tuple)) and value:
            value = value[-1]
        parsed = _float_or_none(value)
        if parsed is not None:
            return round(parsed / 1000, 3) if parsed > 50 else round(parsed, 3)
    return None


def _normalize_telemetry(
    plant: dict[str, Any],
    energy: dict[str, Any],
    day: dict[str, Any] | None = None,
    month: dict[str, Any] | None = None,
    year: dict[str, Any] | None = None,
) -> PlantTelemetry:
    plant_ids = plant.get("plant_ID") or []
    plant_id = int(_first(plant_ids, 0))
    if plant_id == 0:
        raise MyDeltaSolarFormatError("No plant found in MyDeltaSolar account")

    plant_name = str(_first(plant.get("plant_name"), plant_id))
    status_code = _int_or_none(_first(plant.get("plt_status")))

    serials = (plant.get("P_SN") or {}).get(str(plant_id), [])
    models = (plant.get("invtp_arr") or {}).get(str(plant_id), [])
    collector_ids = (plant.get("P_cid") or {}).get(str(plant_id), [])
    inverter_ids = (plant.get("invid_arr") or {}).get(str(plant_id), [])
    last_updates = (plant.get("P_last_ts") or {}).get(str(plant_id), [])

    inverters: list[InverterInfo] = []
    for idx, serial in enumerate(serials):
        inverters.append(
            InverterInfo(
                index=idx + 1,
                serial=str(serial),
                model=str(models[idx]) if idx < len(models) else None,
                collector_id=_int_or_none(collector_ids[idx])
                if idx < len(collector_ids)
                else None,
                inverter_id=_int_or_none(inverter_ids[idx])
                if idx < len(inverter_ids)
                else None,
                last_update=str(last_updates[idx]) if idx < len(last_updates) else None,
                timezone_id=_first(plant.get("tzID")),
            )
        )

    return PlantTelemetry(
        plant_id=plant_id,
        plant_name=plant_name,
        status_code=status_code,
        status=PLANT_STATUS.get(status_code, "unknown")
        if status_code is not None
        else None,
        country=_first(plant.get("country")),
        location=_first(plant.get("location")),
        timezone=_first(plant.get("timezone")),
        timezone_id=_first(plant.get("tzID")),
        start_date=_first(plant.get("start_date")),
        event_count=_int_or_none(_first(plant.get("event_num"))),
        today_energy_kwh=_wh_to_kwh(_first(energy.get("te"))),
        lifetime_energy_kwh=_wh_to_kwh(_first(energy.get("le"))),
        current_power_kw=_latest_plot_power_kw(day),
        month_to_date_energy_kwh=_sum_wh_to_kwh(month.get("energy") if month else None),
        year_to_date_energy_kwh=_sum_wh_to_kwh(year.get("energy") if year else None),
        inverters=tuple(inverters),
        raw_plant=plant,
        raw_energy=energy,
        raw_day=day,
        raw_month=month,
        raw_year=year,
    )
