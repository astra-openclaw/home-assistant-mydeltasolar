# MyDeltaSolar Site/API Map

Complete working map of the MyDeltaSolar website screens, JavaScript flows, endpoints, payload schemas, units, chart reconstruction logic, and Home Assistant entity candidates.

This folder is intentionally evidence-oriented. Rows should say whether a mapping is UI-observed, JS-inferred, request-observed, payload-confirmed, HA-implemented, or rejected/stale.

## Files

- `redaction-policy.md` - safe capture rules for credentialed portal probing.
- `ui-inventory.md` - screens, tabs, selectors, and visible options.
- `endpoint-inventory.md` - endpoint catalog, request params, and redacted schemas.
- `data-dictionary.md` - field-by-field mapping to units and HA entity candidates.
- `graph-reconstruction.md` - chart series, formulas, aggregation, and freshness notes.
- `ha-entity-plan.md` - proposed Home Assistant devices/entities and rollout phases.

## Confidence labels

| Label | Meaning |
| --- | --- |
| `ui-observed` | Seen in the website UI or screenshot, but endpoint/key not confirmed. |
| `js-inferred` | Found in JavaScript/control flow, but not confirmed by a live request. |
| `request-observed` | Endpoint/request observed or successfully called, but field semantics not fully confirmed. |
| `payload-confirmed` | Live authenticated payload confirmed key/unit/shape. |
| `ui-correlated` | Payload value was compared to visible UI value. |
| `ha-implemented` | Implemented in the integration with tests or runtime validation. |
| `rejected/stale` | Field looked useful but was proven unsuitable for the intended purpose. |

## Current priority

1. Map the whole site once: Energy, History, Setting, Plant/Inverter modes, selectors, and all item/chart options.
2. Identify raw inverter data needed to reconstruct plant-level graphs ourselves.
3. Compare our calculated graph/power against MyDeltaSolar's website graph.
4. Use the map to plan a richer Home Assistant integration.

Legacy starter map: see `docs/mydeltasolar-data-map.md`. Canonical full map is now under `docs/deltasolar-map/`.
