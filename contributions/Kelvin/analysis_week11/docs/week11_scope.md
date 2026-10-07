# Week 11 scope and data boundaries

## Project direction

The Week 9 prototype used public/Sportradar event data to explore a general
rugby workflow. Week 11 applies the same idea to the Queensland Reds partner
schema and keeps the work within the fields supplied in the representative
workbook.

~~~text
Authorised partner event file
  -> validate expected columns
  -> retain the documented clock and coordinates
  -> select recorded event subsets
  -> display local analysis views
~~~

prototype_match_analysis/ is the earlier prototype and is outside this
folder's scope.

## Included analysis

- **Event Replay:** a sequence of recorded events for the selected fixture,
  team, and action filter. It applies an event-specific cue to each source
  row, such as travel, contact, evasion, breakdown, set-piece or scoring. A
  local start/end route is limited to semantic movement events with a credible
  pair on that same source row.
- **Kicking:** Kick rows, their types, outcomes, players, listed positions,
  receipt-contest status, and recorded start/end locations.
- **Linebreaks:** Attacking Qualities / Initial Break rows, source results,
  players, positions, locations, and team-level achieved/conceded comparison.
- **Breakdown Choices:** Playmaker Options pass/carry/kick labels and receiver
  context. The relative-x bands are exploratory rather than official Reds
  zones.
- **Tackling:** Tackle outcomes and player table, explicit Missed Tackle
  records, first-tackler and height fields, dominant-tackle qualifiers, and
  linked associated ball-carrier evasion records where available.
- **Game Intervals:** valid MatchTime event-row counts and Try action rows in
  10-minute bands, with 80+ for records after minute 80.
- **Key Insights:** short statements drawn from these same event subsets.

The field-level detail is in [source_feature_mapping.md](source_feature_mapping.md).
The comparison with the reference preview is in
[pdf_coverage_matrix.md](pdf_coverage_matrix.md).
The current Event Replay taxonomy audit is in
[event_effect_coverage.md](event_effect_coverage.md).

## Data boundaries

- One fixture is not a competition average or a long-term opposition trend.
- MatchTime is supplied as mmss; it is not ball-in-play time.
- Coordinates are team-relative: x=0 is the event team's own tryline and
  x=100 is the opposition tryline. Values are shown as supplied rather than
  flipped or clamped.
- Event Replay is based on coded events. It does not create locations between
  rows or claim continuous player tracking. A common `(0,0)` end-coordinate
  placeholder is retained as source data but is not treated as evidence of
  movement.
- An explicit Missed Tackle action remains separate from a Tackle row with the
  result Missed.
- Conceded linebreaks are reported at team level and do not assign individual
  defender responsibility.
- Kick receipt-contest status is kept separate from an official Reds
  "Contestable Kick" metric, which has not been defined in the supplied data.
- The current prototype does not calculate score, possession, phase,
  territory, kick distance, or multi-fixture trends.
- Raw partner files stay local and are ignored by Git.

## Future work

Additional authorised fixtures would support multi-match views. Before adding
new measures, the project needs agreed definitions for Reds zones,
associated-player links across exports, contestable kicks, scoring and phase
measures, and the final report format.
