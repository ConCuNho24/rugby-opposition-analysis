# Canonical event schema

## Purpose

`CanonicalEvent` in
`src/rugby_analysis/core/schema.py` is the contract between all source adapters
and all downstream processing, analysis, insight and reporting code. An adapter
is the only layer allowed to know a source provider's raw fields.

The model is intentionally permissive: an optional field is null when the
source does not provide it. Null is an honest result, not a defect to be filled
with a guess.

## Fields

| Field | Type | Meaning and source-independence rule |
| --- | --- | --- |
| `source` | string | Stable adapter/source name. Required. |
| `match_id` | string | Stable identifier within the canonical store. Required. It may be a deterministic adapter-generated ID when the source lacks one. |
| `event_id` | string | Unique event identifier within a match/source. Required. |
| `sequence_index` | integer | Zero-based order emitted for a match. Required; used for deterministic ordering and adjacency analysis. |
| `period` | integer or null | Provider-supplied period only. Never inferred from a minute without documented source semantics. |
| `timestamp_seconds` | number or null | Event time in seconds if a real source time exists or can be exactly converted. |
| `team_id` / `team_name` | string or null | Event-owning team ID/name as supplied by the source. Do not substitute fixture membership for event attribution. |
| `opponent_id` / `opponent_name` | string or null | Opposing side, if safely available from the fixture/source. |
| `player_id` / `player_name` | string or null | Player responsible for or associated with the event, only where supplied. |
| `event_type` | string | Normalised broad action/record type. Required. |
| `event_subtype` | string or null | Normalised finer-grained action type, when the source distinguishes one. |
| `start_x`, `start_y`, `end_x`, `end_y` | number or null | Source coordinates only. Coordinate system and orientation belong in metadata/documentation. |
| `outcome` | string or null | A normalised result such as `scored`, `missed` or `recorded`, only where genuinely supplied/derivable. |
| `metadata` | JSON-compatible mapping | Source-specific information retained without coupling downstream modules to raw column names. |

The persisted CSV uses the same ordered columns. `metadata` is serialised as a
JSON string so it remains inspectable and can be restored by
`CanonicalEvent.from_record`.

## Selected-source mapping

The Rugby-Data adapter maps the actual public JSON as follows.

| Rugby-Data field/structure | Canonical representation | Notes |
| --- | --- | --- |
| Fixture `date` + home/away team names | `match_id` | A deterministic `rugbydata_<date>_<home>_vs_<away>` ID; the source record has no inspected stable match ID. |
| `home.team` / `away.team` | `team_name` / `opponent_name` | Each scoring, card and substitution record is attributed to the correct fixture side. |
| `scores[].type` | `event_type` | Slug-normalised (for example, `Missed conversion` becomes `missed_conversion`). Original label remains in metadata. |
| `scores[].minute` | `timestamp_seconds` | Exact multiplication by 60. `period` remains null because no verified source period is supplied. |
| `scores[].player` | `player_name` | Left null if absent in the source. |
| `scores[].value` | `metadata.score_value`, and where appropriate `outcome` | Value is preserved, not recomputed from rugby scoring rules. Missed labels become `outcome = missed`; positive values become `scored`. |
| Line-up `on` / `off` entries | `substitution_on` / `substitution_off` | A minute-zero `on` entry represents a starter, not an invented substitution event. |
| Line-up `yellows` / `reds` entries | `yellow_card` / `red_card` | `outcome = recorded`. |
| Fixture fields such as round, venue and attendance | `metadata` | Retained for traceability and report context. |

## What this schema does not assert

The selected real source does **not** provide complete on-ball events or
coordinate data. As a result, the following fields remain null and must not be
used to claim support for spatial/tactical analysis:

```text
period
team_id, opponent_id, player_id
start_x, start_y, end_x, end_y
```

Likewise, the schema's ability to represent a tackle, carry, line break,
possession or kick does not mean the selected source contains such an event.
Future adapters may populate those fields after their source is profiled and
validated.

## Validation rules

The dataclass rejects empty `source`, `match_id`, `event_id` or `event_type`,
a negative `sequence_index`, and a negative timestamp. Adapter validation then
returns non-fatal quality warnings such as no emitted events, no timestamps or
source records with a missing player name.

The canonical schema isolates change: when partner data arrive, the partner
adapter maps its real headers and semantics into this model. Analysis modules
continue to access `event_type`, `team_name`, `timestamp_seconds`, `outcome` and
metadata through the common contract rather than a provider-specific column.

