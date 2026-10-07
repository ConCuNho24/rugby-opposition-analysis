# Preview PDF coverage matrix

preview_Drua_Round_16.pdf is used as a communication and layout reference, not
as a data dictionary. This matrix compares its broad concepts with what the
representative Week 11 partner file can support.

| PDF-style section or output | Week 11 status | What the app provides | Current boundary |
| --- | --- | --- | --- |
| Cover / opponent fixture context | Partially implemented | Fixture, teams and selected team in Overview | No branded PDF cover or historical opponent profile. |
| Executive observations | Implemented, limited | Key Insights drawn from recorded events | No forecasts or competition benchmarks. |
| Match period view | Partially implemented | 10-minute recorded event activity and source Try rows | Not ball-in-play, possession, score, or momentum. |
| Event Replay | Implemented | A selected team's recorded event sequence, locations, and source-supported event-specific cues for travel, contact, breakdown, set pieces and other coded actions | Event-level timeline only; any local route belongs to one source event and is not continuous player tracking. |
| Kicking selection | Implemented | Source kick types, count and percentage | Limited to actionName = Kick. |
| Kicks by position | Implemented | Recorded playerpositionName counts and percentages | No inferred backs/forwards grouping. |
| Kicking locations | Implemented | Rugby-pitch start/end maps with type filter | Not a reconstructed trajectory or kick-distance analysis. |
| Kick outcomes and kickers | Implemented | Source outcome and player tables | No inferred success KPI. |
| Kick receipt contest status | Partially implemented | qualifier5Name Contested / Not Contested status | Not assumed to equal the official Contestable Kick metric. |
| Linebreak achieved / conceded | Implemented, team level | Selected-team Initial Breaks and opponent Initial Breaks in the fixture | No individual defender responsibility. |
| Linebreak player / position / location | Implemented, limited | Initial Break results, players, positions and start locations | No phase, trajectory, or end-location interpretation. |
| Offload indication | Implemented, limited | Pass / Offload rows by player | Not automatically linked to a tackle or linebreak. |
| Breakdown choices | Implemented | Playmaker pass/carry/kick, receiver context and selectable x-bands | Bands are not confirmed Reds A/B/C/D/E zones. |
| Player-level tackle outcomes | Implemented | Player-by-source-outcome table with totals and sorting | Source labels are preserved; no quality score is added. |
| Missed tackles | Implemented | Explicit Missed Tackle table; missed result in Tackle rows remains separate | The event types are not merged. |
| First-tackler misses | Implemented | 1st Tackler plus source result Missed table | First-tackler status is not inferred. |
| Dominant tackles | Implemented, limited | Explicit Dominant Tackle qualifier by player and outcome | No derived dominance definition. |
| Most evaded tackles | Implemented for this workbook | Associated ball-carrier table with Bumped Off / Stepped / Outpaced / Positional / Other columns | Depends on the associated-player link used in this workbook. |
| Set piece, exits, attack/defence profile, territory, possession and ruck speed | Not supported | Not shown | The current source mapping does not define these measures. |
| Multi-match opposition averages / trends | Requires more data | Not shown | One representative fixture cannot support trends or benchmarks. |

## Scope of the prototype

The prototype focuses on Overview, Key Insights, Game Intervals, Event Replay,
Kicking, Linebreaks, Breakdown Choices, and Tackling. This keeps the screens
within the fields available in the current event file while leaving room for
additional views once definitions and data are supplied.
