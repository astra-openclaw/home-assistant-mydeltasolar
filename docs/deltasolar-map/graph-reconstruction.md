# Graph Reconstruction Notes

Status: initial scaffold.

## Plant production graph

Known website graph source:

```text
POST /web/process_gtop_plot.php
unit=day
is_all_plants=1
```

- `ts`: timestamps in Unix milliseconds.
- `top`: plant production samples in watts.
- Latest plant graph power in kW: `top[-1] / 1000`.

Future comparison:

```text
calculated_plant_power_w = sum(inverter_output_power_w for online/available inverters)
graph_delta_w = calculated_plant_power_w - latest_graph_top_w
```

Need to determine:

- sample cadence and delay of `top`
- whether `top` is sum of AC output powers, DC input powers, or another aggregate
- whether per-inverter chart/data can reconstruct the same series

## Inverter DC V/I chart

Observed chart series:

- `<id> dc voltage 1` in V
- `<id> dc current 1` in A
- `<id> dc voltage 2` in V
- `<id> dc current 2` in A

Potential derived series:

```text
pv1_power_w = dc_voltage_1_v * dc_current_1_a
pv2_power_w = dc_voltage_2_v * dc_current_2_a
total_dc_input_power_w = pv1_power_w + pv2_power_w
```

Need endpoint confirmation before using these formulas in HA.

## Inverter AC output

Observed More Info field:

```text
output_power_w
```

Likely best candidate for calculated live plant power:

```text
plant_live_power_w = sum(inverter_output_power_w)
```

Need to verify freshness and endpoint source.

## Static JS chart renderer inventory

### `plotEnergyChart(data, chart_id, unit)`

| Unit | Value type | Chart style | X-axis |
| --- | --- | --- | --- |
| `day` | power | custom line | minute/time-of-day |
| `month` | energy | bar | day |
| `year` | energy | bar | month |
| `20years` | energy | bar | year |

Recognized series keys include:

- `top` - production/power
- `energy` - energy
- `con` - consumption
- `sell` - feed-in
- `buy` - purchased
- `btch`, `btdisch` - battery charge/discharge
- `extp1`, `extp2`, `extp3`, `loadp1`, `loadp2`, `loadp3` - extended/load phases

Inverter daily power may use nested shape similar to `data.inv[sn][id]` for per-inverter datasets.

### `plotVIChart(data, chart_id)`

Expected nested shape from JS: `data.inv[sn][id][key]`.

Key conventions inferred from renderer:

| Key pattern | Meaning | Axis/unit |
| --- | --- | --- |
| second character `v` | voltage | V |
| second character `c` | current | A |
| first character `i` | DC input label | V/A |
| otherwise | AC output label | V/A |

Mapped item values:

- `DCVI` - DC voltage/current
- `DCI` - DC current
- `DCV` - DC voltage
- `ACVI` - AC voltage/current
- `ACI` - AC current
- `ACV` - AC voltage

### Battery/EV chart renderers

Static JS recognizes battery/EV style series including charge, discharge, SOC, and voltage keys (`btch`, `btdisch`, `btsoc`, `btv`, `evch`, `evdisch`, `evsoc`, `evv`, and related `dd*` keys). These are likely irrelevant for Robert's current non-storage solar setup unless endpoints return data.

## Confirmed inverter graph source

`POST /web/AjaxInverterUpdate.php` with `item=power` returns inverter output power time series:

```text
result.inv[<serial>][<inverter id>] = [
  {x: <unix_ms>, y: <watts>}, ...
]
```

This is the key raw source for reconstructing plant production ourselves:

```text
for each timestamp:
  calculated_plant_power_w[timestamp] = sum(inverter_power_w[timestamp] for all inverter series)
```

Need to verify `ALL` selector behavior. If `inv=all` returns all inverter series in one call, use it. Otherwise query each inverter serial/id and align timestamps.

## Confirmed inverter voltage/current graph sources

`POST /web/AjaxInverterUpdate.php` supports these item values:

| Item | Series keys | Unit | Notes |
| --- | --- | --- | --- |
| `DCVI` | `iv1`, `ic1` observed | V/A | combined DC voltage/current chart |
| `DCV` | `iv1` observed | V | DC voltage only |
| `DCI` | `ic1` observed | A | DC current only |
| `ACVI` | `ov1`, `oc1` observed | V/A | combined AC voltage/current chart |
| `ACV` | `ov1` observed | V | AC voltage only |
| `ACI` | `oc1` observed | A | AC current only |

For the current observed active inverter, chart latest points correlated with More Info latest values after unit scaling:

- More Info `iv` raw tenths of V corresponds to chart `iv1` V.
- More Info `ic` raw hundredths of A corresponds to chart `ic1` A.
- More Info `ov` raw tenths of V corresponds to chart `ov1` V.
- More Info `oc` raw hundredths of A corresponds to chart `oc1` A.
- More Info `op` W corresponds to chart `power` W.

This makes the More Info endpoint suitable for latest sensors and the chart endpoint suitable for graph reconstruction/comparison.

## Initial plant graph vs inverter sum comparison

Authenticated check on 2026-05-11 found:

- `inv=all` variants returned empty inverter series for this account/UI path, so current reconstruction should query each inverter serial/id individually unless later JS/UI probing finds the correct ALL payload.
- Only the currently producing inverter returned a non-empty `item=power` series during the check; older/offline/stale inverters returned empty series.
- Summing all available per-inverter `item=power` series matched the plant daily graph `top` series exactly for the overlapping latest samples.
- Latest timestamp matched between calculated inverter series and plant graph.

Implication: the website plant daily graph appears to be an aggregate of the per-inverter `AjaxInverterUpdate.php item=power` series. This strongly supports reconstructing plant graphs from inverter data.

Implementation note:

```text
for each inverter in process_init_plant metadata:
  call AjaxInverterUpdate.php item=power for date/unit
  collect result.inv[serial][inverter_id]
  align by x timestamp
  sum y watts per timestamp
compare against process_gtop_plot.php top[] for diagnostics
```

### All-device request nuance

The JS builds all-inverter chart requests as:

```text
sn=all
inv=<JSON.stringify(g_block[block_i].device)>
devices=<JSON.stringify(g_devices)>
```

A manually constructed JSON device list returned the active inverter series for `item=power`. Keep both implementation options open:

1. **Simple/reliable:** request each inverter serial/id individually and sum returned series.
2. **Optimized:** reproduce the portal's all-device JSON shape and request all series at once after confirming it returns multiple active inverter series.
