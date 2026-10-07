# Event Replay manual coverage checklist

Use this checklist after loading an authorised Partner file and selecting a
fixture/team in Streamlit.

| Representative category | Check |
| --- | --- |
| Kick, Pass, Carry, Restart, Goal Kick | Label and recorded start/end route are sensible; animation, if enabled, stays within the selected event. |
| Tackle and Defensive Action | Contact marker/rings reflect complete, passive, dominant or turnover context without a route. |
| Missed Tackle | Evasion cue reflects the recorded type; any associated player is shown as text only. |
| Ruck, Ruck OOA and Maul | Breakdown cluster is stationary and does not create player positions. |
| Playmaker Options | Pass/carry/kick decision is labelled without presenting it as a completed movement. |
| Attacking Qualities and Possession Initial Break | Breakthrough cue is visible at the recorded event location. |
| Turnover and carried-in-touch variants | Possession-change or exit cue matches the recorded outcome. |
| Scrum and lineout actions | Set-piece marker is distinct from movement and contact cues. |
| Try and Goal Kick | Scoring emphasis matches the explicit source action/result. |
| Penalty, review, substitutions and period rows | Stoppage or administration treatment does not create a made-up field action. |
| Blank/unsupported semantics | Neutral labelled marker remains visible when a location exists; details panel remains readable. |
| Previous/Next, slider and recent trail | Navigation stays responsive and the trail contains only earlier source rows. |

## Current representative check

The representative workbook was run through Event Replay using Kick, Pass,
Carry, Tackle, Missed Tackle, Ruck OOA, Playmaker Options, Initial Break,
Turnover, Scrum, Lineout Throw, Try, Goal Kick, Penalty Conceded, Collection,
Sub In, Defensive Exits and Restart filters. Each selection rendered one pitch
and a readable current-event effect label without an application exception.
The local-movement control appeared for the selected eligible movement events
and remained absent for the stationary decision, contact, breakdown and
administration examples.
