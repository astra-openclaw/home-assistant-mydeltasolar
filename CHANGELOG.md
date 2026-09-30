# Changelog

## v0.3.1

- Replace deprecated inverter `DeviceInfo.via_device` with `via_device_id`, registering or reusing the plant before its inverter entities.
- Preserve existing device identifiers, sensor unique IDs, entity IDs and energy metadata across setup/reload.
- Require Home Assistant 2026.8.0 or newer; older versions lack the new entity device-info API.
- Add real Home Assistant platform/registry regression tests for fresh installs and v0.3.0 upgrades.

## v0.3.0

- Fix current power to use the MyDeltaSolar daily production graph instead of stale `de` energy payload data.
- Add per-inverter telemetry sensors from the inverter More Info endpoint.
- Add calculated plant current power from summed inverter AC output power.
- Add graph-vs-calculated current power diagnostics and live inverter count.
- Document the mapped MyDeltaSolar site/API data sources.

## v0.2.1

- Remove legacy `daily_yield` entity from the Home Assistant entity registry during setup.
- Keeps the previous v0.2.0 sensors and attributes.

## v0.2.0

- Add human-readable plant status.
- Add event count sensor.
- Add month-to-date and year-to-date energy sensors.
- Add per-inverter last-seen age in minutes.
- Add richer plant and inverter attributes.

## v0.1.1

- Remove incorrect daily yield sensor.

## v0.1.0

- Initial MyDeltaSolar cloud polling integration.
- Add current power, today energy, lifetime energy, plant status, active inverter count, and inverter cloud status sensors.
