"""The MyDeltaSolar integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant

from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES
from .coordinator import MyDeltaSolarDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]

type MyDeltaSolarConfigEntry = ConfigEntry[MyDeltaSolarDataUpdateCoordinator]


async def async_setup_entry(
    hass: HomeAssistant, entry: MyDeltaSolarConfigEntry
) -> bool:
    """Set up MyDeltaSolar from a config entry."""
    coordinator = MyDeltaSolarDataUpdateCoordinator(
        hass=hass,
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        scan_interval_minutes=entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES
        ),
    )
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: MyDeltaSolarConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
