# UI Inventory

Status: initial scaffold. Complete during full site walk.

## ENERGY

### Known controls

| Area | Control | Values | Status | Notes |
| --- | --- | --- | --- | --- |
| Energy dashboard | Option | `PLANT`, `INVERTER` | ui-observed | Switches plant aggregate vs inverter-focused views. |
| Plant graph | Date/unit selector | day/month/year likely | js-inferred | `home-date-selector` in JS. |
| Inverter view | ID selector | `ALL`, per-inverter IDs | ui-observed | Need complete enumeration from page. |
| Inverter view | Items selector | `More Info.`, `DC V/I` observed | ui-observed | Need all dropdown values. |
| Inverter chart | Date selector | date string | ui-observed | Need endpoint and params. |

### Observed item views

| Mode | ID | Item | Description | Status |
| --- | --- | --- | --- | --- |
| INVERTER | specific inverter, e.g. `3` | `More Info.` | Latest/status panel with Info, Input, Output, FW Version. | ui-observed |
| INVERTER | `ALL` | `DC V/I` | Daily chart of DC voltage/current per channel. | ui-observed |

## HISTORY

TODO: enumerate tabs, selectors, charts, tables, endpoint calls.

## SETTING

TODO: enumerate pages/options. Likely lower priority for HA telemetry, but included for complete site map.

## Static JS control inventory additions

### Energy mode controls

| Control/function | Values or behavior | Confidence |
| --- | --- | --- |
| `show_sel(0/1/2)` | Switches Plant / DC collector / Inverter panels | js-inferred |
| `input[name=date-selector]` | `day`, `month`, `year`, `20years` for plant history/chart | js-inferred |
| `input[name=dc-date-selector]` | `day`, `month`, `year`, `20years` for DC collector charts | js-inferred |
| `input[name=inv-date-selector]` | `day`, `month`, `year`, `20years` for inverter charts | js-inferred |
| `#h_dc_items` | recognizes `power`, `more` | js-inferred |
| `#h_inv_items` | recognizes `power`, `top`, `energy`, `more`, `bt`, `DCVI`, `DCI`, `DCV`, `ACVI`, `ACI`, `ACV`, `disconnect`, `ev` | js-inferred |
| `#energy_inv_block_select`, `#energy_inv_dc_select`, `#energy_inv_inv_select` | block/DC/inverter selector chain; supports `all` | js-inferred |
| `#energy_dc_block_select`, `#energy_dc_dc_select` | block/DC selector chain; supports `all` | js-inferred |

### History controls

| Control/function | Values or behavior | Confidence |
| --- | --- | --- |
| `tab1_show_sel(0/1/2)` | History Plant / DC / Inverter tabs | js-inferred |
| `#rt_inv_items` | recognizes `disconnect`, `startup`, `event`, `fw_upgrade` | js-inferred |
| `#rt_collector_items` | recognizes `startup`, `disconnect` | js-inferred |
| `#hist_inv_date_start`, `#hist_inv_date_end` | date range for inverter event/disconnect/startup/firmware history | js-inferred |
| `#hist_dc_date_start`, `#hist_dc_date_end` | date range for collector disconnect history | js-inferred |

### Setting/component controls

| Function | Target | Confidence |
| --- | --- | --- |
| `AJAXSetting(page)` | `/component/{page}` with plant/settings params | js-inferred |
| `AJAXTabsPage(page)` | `/component/{page}` with plant ID | js-inferred |
| `refreshBlockData()` | reloads edit pages like `edit_block`, `edit_dc`, `edit_dc_inv`, `edit_inv` | js-inferred |

## Authenticated page DOM inventory

The portal appears to serve the same large authenticated shell for `m_gtop`, `m_history`, `m_setting`, `m_energy`, and `share_list`; tab/component state is controlled by JS and dynamic components.

### Energy option radio

| UI option | Value/function | Meaning | Confidence |
| --- | --- | --- | --- |
| Plant | `sel_radio=plant`, `show_sel(0)` | plant aggregate panel | request-observed |
| Block/DC | `sel_radio=block`, `show_sel(1)` | collector/DC block panel | request-observed |
| Inverter | `sel_radio=inv`, `show_sel(2)` | inverter panel | request-observed |

### Energy inverter item dropdown `#h_inv_items`

| Value | UI label | Endpoint family | Confidence |
| --- | --- | --- | --- |
| `more` | More Info. | `AjaxInverterUpdate.php item=more` | request-observed |
| `power` | Power Flow | `AjaxInverterUpdate.php item=power` | payload-confirmed |
| `DCVI` | DC V/I | `AjaxInverterUpdate.php item=DCVI` | payload-confirmed |
| `ACVI` | AC V/I | `AjaxInverterUpdate.php item=ACVI` | payload-confirmed |
| `DCV` | DC Voltage | `AjaxInverterUpdate.php item=DCV` | payload-confirmed |
| `DCI` | DC Current | `AjaxInverterUpdate.php item=DCI` | payload-confirmed |
| `ACV` | AC Voltage | `AjaxInverterUpdate.php item=ACV` | payload-confirmed |
| `ACI` | AC Current | `AjaxInverterUpdate.php item=ACI` | payload-confirmed |
| `bt` | Battery | `AjaxInverterUpdate.php item=bt` | request-observed, null data for this setup |
| `ev` | Battery(EV) | `AjaxInverterUpdate.php item=ev` | request-observed, empty data for this setup |

### Energy DC/collector item dropdown `#h_dc_items`

| Value | UI label | Endpoint family | Confidence |
| --- | --- | --- | --- |
| `more` | More Info. | likely `AjaxUpdateDC.php item=more` | ui-observed/js-inferred |
| `power` | Power Flow | likely `AjaxUpdateDC.php item=power` | ui-observed/js-inferred |

### Date/unit radio groups

| Radio group | Values | Applies to | Confidence |
| --- | --- | --- | --- |
| `home-date-selector` | `day`, `month`, `year`, `20years` | main plant overview graph `process_gtop_plot.php` | request-observed |
| `date-selector` | `day`, `month`, `year`, `20years` | plant history/energy panel | request-observed |
| `dc-date-selector` | `day`, `month`, `year`, `20years` | DC/collector charts | request-observed |
| `inv-date-selector` | `day`, `month`, `year`, `20years` | inverter charts | request-observed |

### History item dropdowns

| Dropdown | Value | UI label | Endpoint family | Confidence |
| --- | --- | --- | --- | --- |
| `#rt_inv_items` | `event` | Event | `AjaxInverterUpdate.php` history params | request-observed/js-inferred |
| `#rt_inv_items` | `disconnect` | Disconnect | `AjaxInverterUpdate.php` history params | request-observed/js-inferred |
| `#rt_inv_items` | `startup` | Startup | `AjaxInverterUpdate.php` history params | request-observed/js-inferred |
| `#rt_collector_items` | `disconnect` | Disconnect | `AjaxDCstartup.php` or `AjaxUpdateDC.php` history params | request-observed/js-inferred |
| `#rt_collector_items` | `startup` | Startup | `AjaxDCstartup.php` | request-observed/js-inferred |
