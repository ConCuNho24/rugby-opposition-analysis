# Future Queensland Reds partner-data integration

## Boundary of the current PoC

The partner has not supplied event CSVs, schema documentation, existing scripts,
Tableau workbooks, Opta/Rugby Australia access, qualifier definitions or video
rights. The current project therefore does **not** implement a speculative Opta
parser.

`PartnerAdapterPlaceholder` is intentionally non-functional. It documents the
extension point and raises a clear error until real partner data can be profiled.
This prevents a dangerous claim that a public-source mapping is equivalent to
the partner's data.

## Integration objective

When partner data arrive, the main new implementation task should be a
header-aware `PartnerAdapter` that produces `CanonicalEvent` objects. The
following components are designed to be reused unchanged or with only
data-supported configuration:

```text
REUSE
  canonical schema
  incremental pipeline and manifest
  canonical storage convention
  generic analysis interfaces
  candidate-insight structure
  report engine and Streamlit architecture

ADD / VALIDATE
  partner source profiler
  PartnerAdapter
  source-specific mappings and validation
  partner-supported analyses and report sections
```

## Step 1 -- preserve and profile the received data

1. Store originals in a restricted, partner-approved location. Do not commit
   them to Git or mix them with public data.
2. Identify whether each file represents a match, a period, a competition export
   or another unit.
3. Record headers, encodings, delimiters, row counts and schema drift across
   files.
4. Locate real match IDs, fixture date, home/away teams, player/team IDs,
   event/action IDs, timestamps/periods and coordinates.
5. Profile null rates and verify whether event time is match clock, video clock,
   elapsed clock, or another convention.
6. Inventory `Action`, `ActionType`, `Qualifier` and related fields by event
   type. A qualifier may have different meaning for a tackle and a carry, so do
   not assign one universal interpretation.
7. Confirm field-coordinate origin, orientation, units and whether direction
   changes by half.
8. Identify controlled vocabularies, duplicate/event-correction conventions and
   the provider's licensing/privacy rules.

Create an auditable profile output analogous to
`outputs/data_profile.json`, but keep it in an approved private location.

## Step 2 -- agree mappings with analysts

Map real partner fields only after the profile is reviewed with data owners and
analysts. A mapping table should state the source field, canonical target,
transformation, null rule and validation test.

| Likely partner concept | Canonical target | Mapping rule to agree, not assume |
| --- | --- | --- |
| Match/game identifier | `match_id` | Use the provider's stable ID; do not derive it if a safe source ID exists. |
| Event/action identifier | `event_id` | Preserve provider identity and correction/version semantics. |
| Action | `event_type` | Map with a maintained vocabulary table. |
| Action type / subtype | `event_subtype` | Preserve meaning by event family; retain unmapped raw values in metadata. |
| Team and player fields | `team_id`, `team_name`, `player_id`, `player_name` | Resolve official IDs/names and identity changes. |
| Clock + period | `timestamp_seconds`, `period` | Convert only after the timing convention is confirmed. |
| Coordinates | `start_x`, `start_y`, `end_x`, `end_y` | Standardise only after orientation and units are documented. |
| Qualifiers/outcomes | `outcome` and/or `metadata` | Model typed, event-specific semantics; do not flatten ambiguous values into false universals. |
| Fixture/team context | `metadata` | Keep venue, competition, score, phase, possession or provider fields traceable. |

The mapping itself should be versioned and reviewed. Unmapped values should be
counted and surfaced as warnings, not silently coerced.

## Step 3 -- implement a real PartnerAdapter

A future implementation should:

1. inherit `EventDataAdapter`;
2. discover the partner's actual file/match unit;
3. parse by header name rather than fragile numeric column position;
4. emit one validated `CanonicalEvent` per real event;
5. preserve source identifiers and source-specific qualifiers in metadata;
6. write deterministic validation warnings for invalid time, unknown vocabulary,
   duplicated IDs, unsupported coordinate convention or missing attribution; and
7. never fill an unavailable player, outcome or coordinate with a placeholder
   that looks real.

The partner adapter should be independently testable against a small,
approval-cleared fixture extract.

## Step 4 -- validate against existing analyst work

Before operational use, select several known matches and reconcile:

- match/event counts after filters;
- named-team and player totals;
- time/period alignment;
- coordinates and attack direction;
- event-type vocabulary;
- selected team metrics versus an approved existing notebook/Tableau result;
- known cards, tries, kicks, tackles and other reference events; and
- report/chart consistency with analyst interpretation.

Record mismatches, their cause and resolution. A matching row count alone is not
sufficient validation.

## Step 5 -- extend analyses only where the partner data supports them

The public source supports scoring, line-up and discipline timeline analyses.
A rich partner event feed may support additional modules such as kicking,
carries, tackle outcomes, line breaks, set pieces, possession sequences and
spatial distribution. Add each only after its field definitions, sample size and
analyst relevance are understood.

A canonical field being available does not automatically validate a rugby metric;
the event definition, orientation and denominator must still be agreed with the
analyst team.

## Data governance and safety checklist

- Confirm the partner's permitted users, retention period and storage location.
- Keep private data, credentials and reports out of public Git repositories.
- Remove/anonymise extracts only under partner approval.
- Do not ingest game footage or third-party media without rights confirmation.
- Treat automatically surfaced results as analyst prompts, not coaching advice.
- Document the data version and adapter mapping version used for every report.

