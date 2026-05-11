# Endpoint Inventory

Status: initial scaffold. All schemas must be redacted.

## Confirmed endpoints

| Endpoint | Method | Params | Purpose | Status |
| --- | --- | --- | --- | --- |
| `/web/process_login.php` | POST | credentials | Login | request-observed; do not document payload details beyond success/error shape |
| `/web/process_init_plant.php` | GET | none observed | Plant metadata, inverter metadata, status arrays | payload-confirmed |
| `/web/process_init_energy.php` | POST | `is_all_plants` | Plant overview energy totals and stale `de` field | payload-confirmed |
| `/web/process_gtop_plot.php` | POST | `unit`, `is_all_plants` | Plant production graph for day/month/year | payload-confirmed for `unit=day`; request-observed for month/year |

## Endpoint details

### `/web/process_gtop_plot.php` - plant daily graph

Request:

```text
POST /web/process_gtop_plot.php
unit=day
is_all_plants=1
```

Redacted schema:

| Key | Type | Unit/meaning | Status |
| --- | --- | --- | --- |
| `unit` | string | `day` | payload-confirmed |
| `plant_date` | string | graph date | payload-confirmed |
| `ts` | list[int] | Unix timestamps in milliseconds | payload-confirmed |
| `top` | list[number] | plant production samples in W | payload-confirmed |
| `pid_arr` | list[id] | redacted plant IDs | payload-confirmed |
| `tzID` | list[string] | timezone IDs | payload-confirmed |

### `/web/process_init_energy.php`

Request:

```text
POST /web/process_init_energy.php
is_all_plants=1
```

Redacted schema:

| Key | Type | Unit/meaning | Status |
| --- | --- | --- | --- |
| `te` | list[number] | today energy, Wh | payload-confirmed |
| `le` | list[number] | lifetime energy, Wh | payload-confirmed |
| `de` | list[number] | stale/unreliable live-power-looking value | rejected/stale |

## Candidate/unknown endpoints

TODO: fill from static JS inventory for inverter detail, inverter history charts, history page, and settings.

## Static JS-discovered endpoints

| Endpoint | Method | Params observed in JS | Purpose | Confidence |
| --- | --- | --- | --- | --- |
| `/web/AjaxPlantUpdatePlant.php` | POST | `item`, `unit`, `sn`, `inv_num`, `year`, `month`, `day`, `is_inv`, `plant_id`, `timezone`, `start_date`, `plt_type`, `mtnm`, `plt_tz`, `is_dst_plt`; export variants may add battery IDs | Plant/history chart data and CSV/XLSX export source | js-inferred |
| `/web/AjaxInverterUpdate.php` | POST | Energy view: `year`, `month`, `day`, `unit`, `item`, `sn`, `inv`, `plant_id`, `is_inv`, `start_date`, `plt_type`, `devices`, `is_dst_plt`, `country`; history view adds date ranges and event flags | Inverter charts, inverter `More Info`, battery/EV charts, inverter event/disconnect/startup/firmware history | js-inferred |
| `/web/AjaxUpdateDC.php` | POST | `year`, `month`, `day`, `sn`, `inv`, `unit`, `item`, `plt_type`, `mtnm`, `start_date`, `plant_id`, `is_inv`, `timezone`, `is_dst_plt`; optional `is_p2=1` | Collector/DC block charts and `More Info` | js-inferred |
| `/web/AjaxDCstartup.php` | POST | `sn`, `inv`, `item`, `tz`, `start_date`; disconnect mode includes date range params | Collector startup/disconnect history | js-inferred |
| `/web/weather_new.php` | POST | `lat`, `lon`, `tz`, `country` | Header weather widget | js-inferred |
| `/web/process_plant_events.php` | POST | `sn_array`, `is_inv`, `plant_id`, `action=get`; remove uses `action=remove`, `plant_id` | Current event modal and notification removal | js-inferred |
| `/web/process_system_info.php` | POST | `user_id`, `action`, `type` | System news / firmware upgrade modal state | js-inferred |
| `/component/{page}` | GET/POST | `lang`; settings variants use `pid`, `is_inv`, `edit_result` | Dynamic HTML components/settings tabs | js-inferred |
| `/web/upload_image.php` | POST multipart | `pid`, `old_img`, file | Plant image upload | js-inferred; out-of-scope write endpoint |
| `/web/process_share_email.php` | POST | `plant_ID`, `email`, `permission` | Share plant | js-inferred; out-of-scope write endpoint |
| `/web/process_share_list.php` | POST | `action=removeShareUser`, `pid`, `uid` | Remove shared user | js-inferred; out-of-scope write endpoint |

### `/web/AjaxInverterUpdate.php` - candidate inverter More Info endpoint

Static JS indicates `item=more` feeds inverter detail rendering functions. Expected fields include:

| Key family | Keys | Likely meaning | Confidence |
| --- | --- | --- | --- |
| Identity/status | `sn`, `invtp`, `ivs`, `last_ts`, `update_ts` | serial/model/status and timestamps | js-inferred |
| Energy | `te`, `male` | today energy and lifetime/main/life energy | js-inferred |
| DC input | `iv`, `ic`, `ip`, `str`, `nistr` | input voltage/current/power and string metadata | js-inferred |
| AC output | `ov`, `oc`, `op` | output voltage/current/power | js-inferred |
| Standalone | `stv`, `stc`, `stp` | standalone voltage/current/power | js-inferred |
| Battery/EV/DD | `bt*`, `ev*`, `dd*` | storage/EV related telemetry | js-inferred |
| Meter | `mt_status`, `mt_switch_ts`, `mtp` | meter state/power | js-inferred |
| Firmware | `fwv`, `fwd`, `mcu` | communication/DSP/MCU/WiFi firmware strings | js-inferred |
| Extension | `dbsn`, `db18_ov`, `db18_oc`, `db18_op` | extension/DB18 output fields | js-inferred |

Status value mapping from JS includes strings such as `Check DC`, `Countdown`, `ON Grid`, `NO DC`, `Alarm`, `Stand Alone`, `Off`, `Online`, `Disconnected`, and `Communication Unstable`.

## Authenticated targeted observations - inverter endpoints

### `/web/AjaxInverterUpdate.php` with `item=more`

Request shape confirmed for Energy/Inverter/More Info:

```text
POST /web/AjaxInverterUpdate.php
year=<YYYY>
month=<M>
day=<D>
unit=day
item=more
sn=<redacted inverter serial>
inv=<portal inverter id>
plant_id=<redacted plant id>
is_inv=1
start_date=<plant start date>
plt_type=<plant type>
devices=
is_dst_plt=0
country=<country>
```

Redacted response shape:

```text
result[<serial>][<inverter id>] = inverter detail record
```

Confirmed record keys seen for producing inverter include:

| Key | Raw shape | Likely UI correlation | Raw/display unit notes | Confidence |
| --- | --- | --- | --- | --- |
| `te` | number | Today Energy | Wh raw, kWh display | payload-confirmed |
| `male` | number | Life Energy | Wh raw, kWh/MWh display | payload-confirmed |
| `ivs` | integer status code | Status, e.g. ON Grid | code mapped by JS | payload-confirmed |
| `last_ts` | Unix seconds | last sample timestamp | timestamp | payload-confirmed |
| `update_ts` | Unix seconds | cloud/update timestamp | timestamp | payload-confirmed |
| `iv` | list[number] | Input Voltage | tenths of V in latest payload; convert `/10` | payload-confirmed for active inverter |
| `ic` | list[number] | Input Current | hundredths of A in latest payload; convert `/100` | payload-confirmed for active inverter |
| `ip` | list[number] | Input Power | W | payload-confirmed for active inverter |
| `ov` | list[number] | Output Voltage | tenths of V; convert `/10` | payload-confirmed for active inverter |
| `oc` | list[number] | Output Current | hundredths of A; convert `/100` | payload-confirmed for active inverter |
| `op` | list[number] | Output Power | W | payload-confirmed; best live calculated-plant source candidate |
| `str`, `nistr` | lists | string/input metadata | needs UI correlation | payload-confirmed |

Notes:

- Inverters without current production may omit `iv/ic/ip/ov/oc/op` and only return identity/status/energy/timestamps.
- `op` latest value matched the same order of magnitude as plant graph `top`, making it the likely source for calculated live plant power.
- More Info endpoint should be tested across all inverters during production, after sunset, and with missing/offline inverters before becoming primary plant current-power source.

### `/web/AjaxInverterUpdate.php` chart items

Same request base as above, varying `item`:

| Item | Result shape | Semantics | Confidence |
| --- | --- | --- | --- |
| `power` | `result.inv[<serial>][<inv id>] = list[{x: unix_ms, y: W}]` | Inverter AC/output power time series | payload-confirmed |
| `DCVI` | nested series keys like `iv1`, `ic1` | DC voltage/current time series | payload-confirmed |
| `DCI` | `ic1` | DC current time series | payload-confirmed |
| `DCV` | `iv1` | DC voltage time series | payload-confirmed |
| `ACVI` | `ov1`, `oc1` | AC voltage/current time series | payload-confirmed |
| `ACI` | `oc1` | AC current time series | payload-confirmed |
| `ACV` | `ov1` | AC voltage time series | payload-confirmed |
| `bt` | `btsoc`, `btv`, `btch`, `btdisch` arrays, null for this setup | battery chart data | request-observed |
| `ev` | empty `inv` array for this setup | EV chart data | request-observed |
| `top`, `energy`, `disconnect` | returned `Incorrect Format` with Energy-view params | not valid in this context/params | request-observed |

### `inv=all` behavior note

Initial authenticated variants using `inv=all` with empty or joined serial params returned an empty `inv` list for `item=power`. Current safest mapping is one request per inverter serial/id from `process_init_plant.php` metadata. This may be a UI parameter nuance; keep as an open question.

### `sn=all` / device-list behavior for inverter charts

Further probing found the UI's all-device path expects `sn=all` and `inv=<JSON device list>`, where each device object includes serial/inverter identifiers. With a JSON device list, `item=power` returned the same active inverter series that individual probing returned. Because inactive/stale inverters had no series at the time, this still needs a sunny/all-inverters-active verification before relying on one all-device call for complete plant reconstruction.
