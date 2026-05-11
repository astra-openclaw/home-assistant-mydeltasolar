# Home Assistant Entity Plan

Status: draft.

## Device model

- One plant device for aggregate plant telemetry.
- One device per inverter using stable portal inverter ID and/or serial for unique ID.
- UI labels like inverter `1`, `2`, `3` should be friendly names, not the only unique identifier.

## Plant entities

| Entity concept | Source | Default | Notes |
| --- | --- | --- | --- |
| Current power | daily graph `top[-1]` initially; calculated inverter sum later if validated | enabled | Current fix uses graph source. |
| DeltaSolar graph power | daily graph `top[-1]` | diagnostic/future | Keep for comparison if calculated source becomes primary. |
| Calculated inverter-sum power | sum inverter output power | enabled | Implemented from `AjaxInverterUpdate.php item=more` AC output `op`. |
| Graph vs calculated delta | calculated - graph | enabled diagnostic | Useful for debugging freshness/accuracy. |
| Today energy | `te` | enabled | Existing. |
| Lifetime energy | `le` | enabled | Existing. |

## Inverter entities

Enabled by default from `AjaxInverterUpdate.php item=more`:

- portal inverter status
- output power
- output voltage
- output current
- DC input power
- DC input voltage
- DC input current
- today energy
- lifetime energy
- latest telemetry sample timestamp
- portal update timestamp

Still future/diagnostic candidates:

- separate PV input channel entities if multiple channels are observed consistently
- firmware versions
- historical chart entities/statistics from `item=power`, `DCVI`, `ACVI`, etc.

## Rollout phases

1. Plant current-power fix from daily graph.
2. Full website/API map.
3. Per-inverter latest sensors from More Info endpoint. ✅
4. Calculated plant power and graph comparison diagnostics. ✅
5. Historical graph reconstruction if endpoint data supports it cleanly.
