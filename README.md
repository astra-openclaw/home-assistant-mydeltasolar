# MyDeltaSolar for Home Assistant

Custom Home Assistant integration for Delta Electronics MyDeltaSolar cloud monitoring.

## Status

Early development. Current scope is aggregate plant telemetry plus latest per-inverter telemetry from the MyDeltaSolar cloud.

## Entities

The integration creates plant sensors for:

- Current power from the MyDeltaSolar daily graph (`kW`)
- Calculated current power from summed inverter AC output (`kW`)
- Current power delta and delta percent between calculated and graph values
- Today energy (`kWh`)
- Lifetime energy (`kWh`)
- Month-to-date energy (`kWh`)
- Year-to-date energy (`kWh`)
- Human-readable plant status plus status code attribute
- Event count
- Active inverter count
- Live inverter count with current AC output telemetry

It also creates per-inverter sensors for:

- Cloud status (`online`, `stale`, or `unknown`)
- Portal inverter status, such as `on_grid`, `no_dc`, or `disconnected`
- Last update and last-seen age
- Latest telemetry sample and portal update timestamps
- Today energy and lifetime energy
- AC output power, voltage, and current
- DC input power, voltage, and current

Cloud status is inferred from the inverter's last update date. The primary current-power sensor still uses the MyDeltaSolar graph source; the calculated current-power sensor is exposed separately so both sources can be compared before switching primary behavior.

## Installation

### HACS custom repository

1. Add this repository as a HACS custom repository of type `Integration`.
2. Install **MyDeltaSolar**.
3. Restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration → MyDeltaSolar**.
5. Enter your MyDeltaSolar email and password.

### Manual

Copy `custom_components/mydeltasolar` into your Home Assistant `custom_components` directory, restart Home Assistant, then add the integration from the UI.

## Security

Credentials are entered through the Home Assistant config flow and stored by Home Assistant. Do not commit `.env`, cookies, logs, packet captures, or real credentials.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
ruff check .
pytest
```

## Known limitations

- Uses the MyDeltaSolar web portal endpoints, not an officially documented public API. Delta may change these endpoints.
- Initial release focuses on aggregate plant telemetry. Per-inverter production details require additional endpoint reverse engineering.
