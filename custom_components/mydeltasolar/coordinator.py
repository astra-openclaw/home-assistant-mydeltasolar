"""Data update coordinator for MyDeltaSolar."""

from __future__ import annotations

import logging
from datetime import timedelta

from aiohttp import ClientSession
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MyDeltaSolarClient, MyDeltaSolarError, PlantTelemetry
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class MyDeltaSolarDataUpdateCoordinator(DataUpdateCoordinator[PlantTelemetry]):
    """Coordinate MyDeltaSolar polling."""

    def __init__(
        self,
        *,
        hass: HomeAssistant,
        username: str,
        password: str,
        scan_interval_minutes: int,
        session: ClientSession | None = None,
    ) -> None:
        """Initialize the coordinator."""
        self.client = MyDeltaSolarClient(
            session or async_get_clientsession(hass), username, password
        )
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=scan_interval_minutes),
        )

    async def _async_update_data(self) -> PlantTelemetry:
        """Fetch fresh MyDeltaSolar data."""
        try:
            return await self.client.async_get_plant_telemetry()
        except MyDeltaSolarError as err:
            raise UpdateFailed(str(err)) from err
