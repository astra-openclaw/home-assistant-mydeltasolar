"""Client for the MyDeltaSolar cloud portal."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from aiohttp import ClientError, ClientSession

from .const import BASE_URL


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


@dataclass(slots=True, frozen=True)
class PlantTelemetry:
    """Normalized MyDeltaSolar plant telemetry."""

    plant_id: int
    plant_name: str
    status_code: int | None
    today_energy_kwh: float | None
    lifetime_energy_kwh: float | None
    current_power_kw: float | None
    daily_yield: float | None
    inverters: tuple[InverterInfo, ...]
    raw_plant: dict[str, Any]
    raw_energy: dict[str, Any]

    @property
    def active_inverter_count(self) -> int:
        """Return count of inverters with a last update date matching today."""
        today = datetime.now().date()
        count = 0
        for inverter in self.inverters:
            if not inverter.last_update:
                continue
            try:
                if datetime.fromisoformat(inverter.last_update).date() == today:
                    count += 1
            except ValueError:
                continue
        return count


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

        headers = {"X-Requested-With": "XMLHttpRequest", "Referer": self._base_url + "m_gtop"}
        plant = await self._request("GET", "web/process_init_plant.php", headers=headers)
        energy = await self._request(
            "POST",
            "web/process_init_energy.php",
            data={"is_all_plants": "1"},
            headers=headers,
        )

        if not isinstance(plant, dict) or not isinstance(energy, dict):
            raise MyDeltaSolarFormatError("Telemetry response was not JSON object")
        return _normalize_telemetry(plant, energy)

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
                        f"MyDeltaSolar returned HTTP {response.status} for {path}"
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


def _wh_to_kwh(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return round(float(value) / 1000, 3)
    except (TypeError, ValueError):
        return None


def _w_to_kw(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return round(float(value) / 1000, 3)
    except (TypeError, ValueError):
        return None


def _normalize_telemetry(plant: dict[str, Any], energy: dict[str, Any]) -> PlantTelemetry:
    plant_ids = plant.get("plant_ID") or []
    plant_id = int(_first(plant_ids, 0))
    if plant_id == 0:
        raise MyDeltaSolarFormatError("No plant found in MyDeltaSolar account")

    plant_name = str(_first(plant.get("plant_name"), plant_id))
    status_code = _first(plant.get("plt_status"))
    if status_code is not None:
        status_code = int(status_code)

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
                collector_id=int(collector_ids[idx]) if idx < len(collector_ids) else None,
                inverter_id=int(inverter_ids[idx]) if idx < len(inverter_ids) else None,
                last_update=str(last_updates[idx]) if idx < len(last_updates) else None,
            )
        )

    return PlantTelemetry(
        plant_id=plant_id,
        plant_name=plant_name,
        status_code=status_code,
        today_energy_kwh=_wh_to_kwh(_first(energy.get("te"))),
        lifetime_energy_kwh=_wh_to_kwh(_first(energy.get("le"))),
        current_power_kw=_w_to_kw(_first(energy.get("de"))),
        daily_yield=float(_first(energy.get("de"), 0)) if energy.get("de") else None,
        inverters=tuple(inverters),
        raw_plant=plant,
        raw_energy=energy,
    )
