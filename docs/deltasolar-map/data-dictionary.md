# Data Dictionary

Status: initial scaffold.

## Plant fields

| Website field/chart | Endpoint | Key | Raw unit | HA unit | Semantics | Confidence | HA status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Today Energy | `/web/process_init_energy.php` | `te[0]` | Wh | kWh | cumulative today energy | payload-confirmed | ha-implemented |
| Life/Total Energy | `/web/process_init_energy.php` | `le[0]` | Wh | kWh | cumulative lifetime energy | payload-confirmed | ha-implemented |
| Current production graph | `/web/process_gtop_plot.php` | latest `top` | W | kW | latest sampled plant production | payload-confirmed | ha-implemented in current-power fix |
| Current-power-looking `de` | `/web/process_init_energy.php` | `de[0]` | W? | kW? | stale/unreliable for live power | rejected/stale | do not use |

## Inverter More Info fields

| Website section | Website field | Raw source | Raw unit | HA unit | Semantics | Confidence | HA candidate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Info | ID | unknown | — | — | inverter UI ID | ui-observed | device label/attribute |
| Info | Serial Number | likely plant/inverter metadata endpoint | — | — | physical inverter serial | ui-observed | device identifier, redacted in docs |
| Info | Model | likely plant/inverter metadata endpoint | — | — | inverter model | ui-observed | device model |
| Info | Status | unknown | — | — | inverter operating state, e.g. ON Grid | ui-observed | diagnostic/status sensor |
| Info | Today Energy | unknown | kWh displayed | kWh | per-inverter daily generation | ui-observed | energy sensor |
| Info | Life Energy | unknown | MWh displayed | kWh | per-inverter lifetime generation | ui-observed | energy sensor |
| Input | Voltage 1/2 | unknown | V displayed | V | PV/DC channel voltage | ui-observed | voltage sensors |
| Input | Current 1/2 | unknown | A displayed | A | PV/DC channel current | ui-observed | current sensors |
| Input | Power 1/2 | unknown | W displayed | W | PV/DC channel power | ui-observed | power sensors |
| Output | Voltage | unknown | V displayed | V | AC output voltage | ui-observed | voltage sensor |
| Output | Current | unknown | A displayed | A | AC output current | ui-observed | current sensor |
| Output | Power | unknown | W displayed | W | AC output power | ui-observed | primary source candidate for calculated plant power |
| FW Version | Comm/DSP/WiFi | unknown | version strings | — | firmware versions | ui-observed | diagnostic attributes/entities |

## Inverter DC V/I chart fields

| Legend | Raw source | Raw unit | Display axis | Semantics | Confidence | HA candidate |
| --- | --- | --- | --- | --- | --- | --- |
| `<id> dc voltage 1` | unknown | V | left | PV/DC channel 1 voltage time series | ui-observed | historical/source for voltage sensor |
| `<id> dc current 1` | unknown | A | right | PV/DC channel 1 current time series | ui-observed | historical/source for current sensor |
| `<id> dc voltage 2` | unknown | V | left | PV/DC channel 2 voltage time series | ui-observed | historical/source for voltage sensor |
| `<id> dc current 2` | unknown | A | right | PV/DC channel 2 current time series | ui-observed | historical/source for current sensor |

## Authenticated inverter latest fields from `AjaxInverterUpdate.php item=more`

| Website field | Endpoint/key | Raw unit | HA unit | Conversion | Semantics | Confidence | HA candidate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Inverter Today Energy | `te` | Wh | kWh | `/1000` | per-inverter daily energy | payload-confirmed | `inverter_<id>_today_energy` |
| Inverter Life Energy | `male` | Wh | kWh | `/1000` | per-inverter lifetime energy | payload-confirmed | `inverter_<id>_lifetime_energy` |
| Inverter Status | `ivs` | code | text | JS status map | inverter operating status | payload-confirmed | `inverter_<id>_status` |
| Last sample time | `last_ts` | Unix seconds | datetime | timestamp parse | inverter last telemetry timestamp | payload-confirmed | diagnostic attribute/entity |
| Cloud update time | `update_ts` | Unix seconds | datetime | timestamp parse | portal update timestamp | payload-confirmed | diagnostic attribute/entity |
| DC input voltage | `iv[]` | tenths of V | V | `/10` | PV/DC input voltage, channel(s) present | payload-confirmed | `inverter_<id>_pv<n>_voltage` |
| DC input current | `ic[]` | hundredths of A | A | `/100` | PV/DC input current, channel(s) present | payload-confirmed | `inverter_<id>_pv<n>_current` |
| DC input power | `ip[]` | W | W | identity | PV/DC input power, channel(s) present | payload-confirmed | `inverter_<id>_pv<n>_power` |
| AC output voltage | `ov[]` | tenths of V | V | `/10` | AC output voltage | payload-confirmed | `inverter_<id>_output_voltage` |
| AC output current | `oc[]` | hundredths of A | A | `/100` | AC output current | payload-confirmed | `inverter_<id>_output_current` |
| AC output power | `op[]` | W | W/kW | identity or `/1000` for plant kW | AC output power; best calculated plant source candidate | payload-confirmed | `inverter_<id>_output_power` |

## Authenticated inverter chart fields from `AjaxInverterUpdate.php`

| Item | Payload series | Raw unit | Semantics | Confidence | Graph reconstruction use |
| --- | --- | --- | --- | --- | --- |
| `power` | list `{x, y}` under `result.inv[serial][id]` | W | inverter output power over time | payload-confirmed | sum per-inverter `y` by timestamp to reconstruct plant production |
| `DCVI`/`DCV` | `iv1` series `{x, y}` | V | DC input voltage | payload-confirmed | derive/validate PV input behavior |
| `DCVI`/`DCI` | `ic1` series `{x, y}` | A | DC input current | payload-confirmed | derive/validate PV input behavior |
| `ACVI`/`ACV` | `ov1` series `{x, y}` | V | AC output voltage | payload-confirmed | diagnostic graph |
| `ACVI`/`ACI` | `oc1` series `{x, y}` | A | AC output current | payload-confirmed | diagnostic graph |
