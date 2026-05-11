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
| Calculated inverter-sum power | sum inverter output power | future | Needs inverter endpoint mapping. |
| Graph vs calculated delta | calculated - graph | future diagnostic | Useful for debugging freshness/accuracy. |
| Today energy | `te` | enabled | Existing. |
| Lifetime energy | `le` | enabled | Existing. |

## Inverter entities

Candidate enabled-by-default if reliable:

- output power
- output voltage
- output current
- today energy
- status

Candidate diagnostic/disabled-by-default:

- PV input voltage/current/power per channel
- lifetime energy per inverter
- firmware versions
- last update/freshness fields

## Rollout phases

1. Plant current-power fix from daily graph.
2. Full website/API map.
3. Per-inverter latest sensors from More Info endpoint.
4. Calculated plant power and graph comparison diagnostics.
5. Historical graph reconstruction if endpoint data supports it cleanly.
