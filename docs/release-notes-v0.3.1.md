# MyDeltaSolar v0.3.1 — device registry compatibility

## Change

Register or reuse the existing plant device during sensor-platform setup, then
pass its Home Assistant registry ID to every inverter entity as
`DeviceInfo.via_device_id`. No deprecated `via_device` fallback is emitted.

Plant/inverter identifiers, all sensor unique IDs, names, units, device classes
and state classes remain unchanged. Existing registry entity IDs, user names and
disabled choices are reused. This includes `sensor.homeauto_lifetime_energy`: its
energy/kWh/total-increasing metadata stays suitable for existing Energy dashboard
configuration. No config-entry migration or deletion/recreation is needed.

## Compatibility and supported API boundaries

- Minimum Home Assistant Core: **2026.8.0**. The new `DeviceInfo.via_device_id`
  support landed with the device-registry changes in 2026.8. Earlier versions are
  not supported by this release; HACS advertises the new minimum.
- Runtime development/testing uses Python **3.14.2 or newer** to match the
  supported Core test environment. No Home Assistant internals are patched.
- The integration boundary is the documented public sensor-platform setup API,
  `device_registry.async_get(hass).async_get_or_create(config_entry_id=...,
  **plant_device_info)` and the returned `DeviceEntry.id`, supplied to inverter
  `DeviceInfo.via_device_id`. Existing identifiers scope registry reuse to the
  owning config entry. No private state/database edits or lookup shim is used.
- `via_device` is deprecated for custom integrations and scheduled for removal
  in Core **2027.8**. This release removes that usage now. This does not claim
  full validation against a future Home Assistant release.

Official sources:

- [Device registry: automatic registration through an entity](https://developers.home-assistant.io/docs/device_registry_index/#automatic-registration-through-an-entity)
  documents passing the returned registry device ID into an entity constructor.
- [Devices restricted to one config entry (2026-07-21)](https://developers.home-assistant.io/blog/2026/07/21/device-registry-single-config-entry/)
  identifies Core 2026.8 and the `via_device_id` replacement.
- [Device registry follow-ups (2026-08-24)](https://developers.home-assistant.io/blog/2026/08/24/device-registry-follow-up-changes/)
  confirms the returned `.id` approach and the Core 2027.8 removal deadline.

## Validation

The tests run the real Home Assistant sensor platform, entity registry and device
registry with mocked cloud telemetry. They cover a fresh install and a seeded
v0.3.0 registry, all 40 sensor identities across two inverters, three devices, two
reloads, parent topology, user-customized names, a disabled diagnostic, identical
plant identifiers belonging to another config entry, and lifetime energy
metadata. Registration fails the test if deprecated `via_device` is supplied or
if a parent registry ID does not already exist.

- Python 3.14.7, Home Assistant **2026.8.0** (declared minimum), test plugin
  0.13.354: **7 tests passed**; `ruff check .` passed.
- Python 3.14.7, Home Assistant **2026.9.3** (matching the reported live Core version),
  test plugin 0.13.366: **7 tests passed**; `ruff check .` passed.
- Python 3.14.7, Home Assistant 2026.9.4, test plugin 0.13.367: **7 tests passed**;
  `ruff check .` passed.

## Installation boundary

This is a source/release preparation change only. No live Home Assistant install,
configuration edit, restart, credential access, publishing, pushing or tagging
was performed. Live installation remains subject to Robert’s confirmation and a
verified Home Assistant backup. Install over the existing integration; do not
remove/re-add its config entry or recreate entities.
