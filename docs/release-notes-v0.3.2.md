# MyDeltaSolar v0.3.2 — midnight energy rollover protection

## Changes

Delta cloud totals can temporarily combine inverters from different local days.
Plant and inverter lifetime energy now retain the last accepted kWh value when
cloud totals fall. A lower counter is accepted only after at least **six hours**
of continuously lower successful observations, with a warning identifying the
counter. Lower readings need not be identical: replacement meters can grow.
Recovery to the previous total, missing/non-finite/negative readings, failed
polls, backwards clock movement, or a gap exceeding twice the configured poll
interval restart confirmation. An unobserved outage is not evidence of a reset.

Today energy uses `tzID` first, then the portal's numeric UTC-hour `timezone`
offset, then Home Assistant's configured zone. It holds same-day decreases and
starts a new local day at zero. Cloud values exceeding elapsed hours since local
midnight × **25 kW for the plant / 10 kW for an inverter** are held back. The bound
is checked on subsequent polls too, so a rejected first rollover sample cannot
let another leftover through. DST days use physically elapsed hours.

Accepted counters, the daily date, and pending lifetime-reset timestamps survive
reloads/restarts with `RestoreSensor`. Restoration occurs before checking the
first cloud sample. Previous versions' restored plain kWh state can provide an
upgrade baseline, without changing any entity identity.

## Identity and compatibility

All unique IDs, device identifiers, energy units and state classes are unchanged.
Install over the existing integration: do not remove/re-add the config entry or
recreate entities. This release includes v0.3.1's `via_device_id` registry fix and
retains its **Home Assistant Core 2026.8.0+ / Python 3.14.2+** requirement. HACS has
no version field; its existing Core minimum remains unchanged.

The integration uses supported sensor-platform APIs, not HA internals: energy
entities subclass `RestoreSensor`, call `async_get_last_sensor_data`, and extend
`SensorExtraStoredData.as_dict()` to store guard metadata. The public
`async_get_last_extra_data` retrieves that metadata and `async_get_last_state`
provides the upgrade fallback. No custom state files or registry/database edits
are needed.

Official source:
[Sensor: restoring sensor states](https://developers.home-assistant.io/docs/core/entity/sensor/#restoring-sensor-states)
— the prescribed native-value restore path is `RestoreSensor` and
`async_get_last_sensor_data`.

## Timestamp finding

Live HA states supplied by the owner from the same inverter record/poll on
2026-10-04 at approximately **10:40 Asia/Taipei (02:40 UTC)** settle the field
semantics despite both fields being numeric epochs:

- `update_ts` / portal update: **2026-10-04T02:35:49+00:00**, correctly
  representing **10:35:49+08:00**.
- `last_ts` / telemetry sample: previously **2026-10-04T10:35:00+00:00**,
  eight hours in the future; the inverter's separate last-update entity was
  correctly **02:35:00+00:00**.
- Inverters 2 and 3 had the same pattern at **10:30:00+00:00**, consistent with
  the prior night's 22:50 local sample labeled UTC.

`update_ts` remains a true Unix instant with the existing plant-zone conversion.
`last_ts` encodes plant-local wall time as if UTC: decode its epoch in UTC, then
attach the valid plant zone without shifting the clock (`replace(tzinfo=zone)`).
The live pair now yields telemetry sample **2026-10-04T10:35:00+08:00** and portal
update **2026-10-04T10:35:49+08:00**. Both seconds and milliseconds are supported.
With a missing or invalid plant zone, retain the previous UTC interpretation
rather than guessing. Entity unique IDs and device identifiers are unchanged.
Regression tests cover the live pair and missing/invalid-zone fallback.

## Validation

- Full suite: **48 tests passed** on Python **3.14.7**, Home Assistant
  **2026.9.3**, pytest-homeassistant-custom-component **0.13.366**, and
  pytest **9.0.3**; `ruff check .` passed with ruff **0.16.9**.
- Tests cover the exact midnight plant sequence and three inverters, same-day
  monotonicity, physical bounds (including DST), six-hour resets and interrupted
  confirmation, restored counters/pending resets, legacy-state upgrade, Unix
  timestamp conversion, the live wall-time/instant pair and no-zone fallback,
  and fresh/upgrade registry identity across reloads.
- The owner-authorized environment `/tmp/mds-venv-2026.9.3` was populated entirely
  offline from the existing uv cache, without network or proxy changes. The
  repository's old `.venv` (Python 3.12 / Home Assistant 2025.1.4) remains untouched;
  it cannot validate v0.3.1's `via_device_id` registry API. This release was tested
  against the reported live Core version, not separately against the minimum.

## Deployment boundary and remaining risks

Source/release preparation only: no Home Assistant access, live installation,
restart, cloud request, push or tag. Historical corrupted statistics are not
rewritten. A genuine meter replacement remains held for six observed hours.
Physical limits are intentionally generous but sites larger than these limits
would need appropriate constants before deployment. Without a valid plant zone,
telemetry sample timestamps retain the previous UTC fallback. Live installation
requires the owner's existing backup/approval process.
