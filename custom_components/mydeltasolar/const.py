"""Constants for the MyDeltaSolar integration."""

from __future__ import annotations

DOMAIN = "mydeltasolar"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL_MINUTES = 5
MIN_SCAN_INTERVAL_MINUTES = 1

BASE_URL = "https://mydeltasolar.deltaww.com/"

ATTR_PLANT_ID = "plant_id"
ATTR_PLANT_NAME = "plant_name"
ATTR_INVERTER_SERIAL = "serial"
ATTR_INVERTER_MODEL = "model"
ATTR_COLLECTOR_ID = "collector_id"
