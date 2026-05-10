# MyDeltaSolar for Home Assistant

Custom Home Assistant integration for Delta Electronics MyDeltaSolar cloud monitoring.

## Status

Early development. Initial scope is aggregate plant telemetry from the MyDeltaSolar cloud.

## Entities

The first version creates these sensors:

- Current power (`kW`)
- Today energy (`kWh`)
- Lifetime energy (`kWh`)
- Month-to-date energy (`kWh`)
- Year-to-date energy (`kWh`)
- Human-readable plant status plus status code attribute
- Event count
- Active inverter count
- Per-inverter last update
- Per-inverter last-seen age in minutes
- Per-inverter cloud status (`online`, `stale`, or `unknown`)

Cloud status is inferred from the inverter's last update date. If only one inverter is reporting to MyDeltaSolar, aggregate production reflects only what the cloud currently sees.

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
