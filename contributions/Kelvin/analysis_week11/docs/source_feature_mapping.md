# Source-to-feature mapping

This document links the representative partner workbook to the features in
the Week 11 prototype. The workbook was inspected on its `in` worksheet, which
contains 3,588 event rows. Field names below are the canonical names used by
the application.

| Feature or concept | Source field(s) -> canonical field(s) | Status | Current interpretation |
| --- | --- | --- | --- |
| Fixture and teams | FXID -> fixture_id; teamName -> team_name; home/away names | Implemented | Select one fixture and one event-row team. |
| Event Replay | ps_timestamp, MatchTime, playerName, teamName, actionName, ActionTypeName, ActionResultName, qualifier3Name--qualifier10Name, and x/y start/end fields | Implemented | Orders rows by source period, then the canonical event timestamp, with stable source order for ties or missing timestamps. MatchTime remains display data. Each row receives an event-effect profile. Local motion is limited to semantic Kick, Pass, Carry, Restart and Goal Kick records with distinct, non-default source endpoints on that same row. |
| Match clock | MatchTime -> match_time_raw; period | Implemented | Decode documented mmss and group recorded rows into 10-minute bands. This is not elapsed ball-in-play time. |
| Try records | actionName = Try | Implemented, limited | Count source Try action rows; no score or points calculation. |
| General kick volume | actionName = Kick | Implemented | Use this exact subset. Goal Kick and Defensive Exits remain separate source actions. |
| Kick category | ActionTypeName -> action_type_name on Kick rows | Implemented | Display source labels as supplied. |
| Kicker | playerName -> player_name on Kick rows | Implemented | Group by the recorded player. |
| Kicks by player position | playerpositionName -> player_position_name on Kick rows | Implemented | Use the recorded position; blank values display as Not recorded. |
| Kick outcome | ActionResultName -> action_result_name on Kick rows | Implemented | Display source outcomes without inferring a success rule. |
| Kick start/end location | x_coord, y_coord, x_coord_end, y_coord_end -> x/y and x_end/y_end | Implemented | Plot recorded starts and ends; no trajectory or distance is reconstructed. |
| Kick receipt contest status | qualifier5Name -> qualifier_5_name: Kick Receipt Contested / Kick Receipt Not Contested | Implemented, limited | Map the two supplied values to Contested / Not Contested. This is not the official Reds Contestable Kick metric. |
| Attacking or phase kick | No validated whole-event definition | Not supported | PlayNum and SetNum are not given an inferred rugby meaning. |
| Initial linebreak records | actionName = Attacking Qualities and ActionTypeName = Initial Break | Implemented, limited | Retain source results such as Line Break and Kick Line Break; do not combine unrelated Possession rows. |
| Linebreak achieved | Selected-team Initial Break events | Implemented | Count Initial Break rows recorded for the selected team. |
| Linebreak conceded | Opponent Initial Break events in the selected fixture | Implemented, team level | Count opponent Initial Break rows without assigning a particular defender. |
| Break player, position and location | playerName, playerpositionName, x/y on Initial Break rows | Implemented | Group populated source values. End coordinates are not used because representative Initial Break endpoints are 0,0. |
| Offloads | actionName = Pass, ActionTypeName = Offload | Implemented, limited | Count Offload pass rows by recorded player; they are not automatically linked to a tackle. |
| Playmaker / breakdown choice | actionName = Playmaker Options, ActionResultName = Playmaker Option - Pass/Carry/Kick, ActionTypeName | Implemented | Count the decision and show recorded receiver context. |
| Breakdown zone | x_coord -> x | Partially implemented | Use configurable equal 25m relative-x bands; formal Reds A/B/C/D/E definitions have not been supplied. |
| Tackle volume and outcome | actionName = Tackle, playerName, ActionResultName | Implemented | Preserve every source outcome label in the tables. |
| Explicit missed tackle | actionName = Missed Tackle | Implemented | Keep separate from Tackle rows with result Missed. |
| First-tackler missed result | qualifier5Name = 1st Tackler and ActionResultName = Missed on Tackle rows | Implemented | Use the strict source filter; first tacklers are not inferred. |
| Tackle height | qualifier6Name -> qualifier_6_name | Implemented | Show populated source labels. |
| Dominant tackle | qualifier4Name = Dominant Tackle -> qualifier_4_name | Implemented, limited | Count the explicit qualifier by player and observed outcome. |
| Linked evaded tackles | Missed Tackle: player and associated-player fields, assoc_event_id, ActionTypeName | Implemented for this workbook | In this workbook, the 41 associated events resolve to opposing-team Carry events. The table ranks the linked ball carrier; unexpected or blank evasion labels are grouped as Other. |
| Possession, phases, ball-in-play, territory gained and kick distance | No confirmed cross-row calculation specification | Not supported | These measures are not displayed or inferred. |

## Coordinate and clock conventions

The supplied partner guidance defines coordinates relative to the team on each
event row: x=0 is that team's own tryline and x=100 is the opposition tryline.
The transformation leaves those values intact. The interface uses a 0-100 by
0-70 field with a small visual margin and reports out-of-range plotted values
instead of clamping them.

MatchTime is source mmss, not seconds. ps_timestamp remains separate because
the partner guidance notes a half-time jump. The interval page labels records
at or beyond minute 80 as 80+.

The current event-effect taxonomy audit is in
[event_effect_coverage.md](event_effect_coverage.md).

## Items to confirm for future data releases

- Check that associated-player links use the same meaning in later exports.
- Confirm the formal Reds definition of Contestable Kick before using that
  name for receipt-contest status.
- Confirm official Reds field-zone definitions before replacing the neutral
  25m relative-x bands.
- Agree definitions for possession, phase, ball-in-play, territory, scoring,
  and multi-fixture trend measures before adding them.
