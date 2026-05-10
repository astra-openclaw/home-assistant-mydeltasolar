"""The MyDeltaSolar integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES
from .coordinator import MyDeltaSolarDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]

type MyDeltaSolarConfigEntry = ConfigEntry[MyDeltaSolarDataUpdateCoordinator]


async def async_setup_entry(
    hass: HomeAssistant, entry: MyDeltaSolarConfigEntry
) -> bool:
    """Set up MyDeltaSolar from a config entry."""
    _remove_legacy_entities(hass, entry)

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


def _remove_legacy_entities(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove entities that were created by older integration versions."""
    registry = er.async_get(hass)
    for entity_entry in er.async_entries_for_config_entry(registry, entry.entry_id):
        if entity_entry.unique_id.endswith("_daily_yield"):
            registry.async_remove(entity_entry.entity_id)

    # Older Home Assistant reload paths can leave an unavailable state behind even
    # after registry cleanup. Remove the known legacy state as a harmless fallback.
    hass.states.async_remove("sensor.homeauto_daily_yield")
