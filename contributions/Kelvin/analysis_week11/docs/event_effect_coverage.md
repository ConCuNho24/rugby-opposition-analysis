# Event Replay effect coverage

## Representative-data audit

This audit is based on the representative Partner workbook for fixture 949231:
Queensland Reds v NSW Waratahs, Super Rugby Pacific 2026 round 5. It contains
3,588 event rows: 2,063 NSW Waratahs rows and 1,525 Queensland Reds rows.

The audit reviewed `actionName`, `ActionTypeName`, `ActionResultName`, and
qualifier names 3--10. Qualifiers 8--10 are present as columns but are empty
in this workbook. The application retains them so later files can use them.

Every row receives a visual profile. The two rows with no action name, no
usable type, and no usable action meaning receive the neutral labelled marker;
this is the only fallback in the representative file. The other 288 blank
`actionName` rows have source IDs/types identifying a scrum set-piece context.

## Action coverage

| actionName | Records | Source-aware treatment | Effect family or families | Coverage |
| --- | ---: | --- | --- | --- |
| Not recorded | 290 | Scrum IDs/types identify 288 set-piece outcomes; 2 rows have no usable semantic fields | Set-piece context; neutral fallback | Covered with fallback |
| Collection | 595 | General, loose-ball, restart and contested receipt labels | Receipt | Covered |
| Ruck OOA | 470 | Secured, cleaned-out, entry, jackal and counter-ruck context | Breakdown | Covered |
| Playmaker Options | 399 | Pass, carry and kick decision result; receiver context | Decision | Covered |
| Tackle | 353 | Complete, passive, dominant, turnover and missed result variants | Contact; evasion for missed | Covered |
| Pass | 349 | Length, direction, receiver and offload context | Ball travel | Covered |
| Carry | 230 | One-out, pick-and-go, support, outcome and contact context | Player advance; scoring where explicitly recorded | Covered |
| Ruck | 185 | Won, lost, penalty and ruck-speed context | Breakdown | Covered |
| Attacking Qualities | 123 | Initial break, defender beaten, break assist and support-break types | Breakthrough; attacking-quality cue | Covered |
| Possession | 84 | Initial-break, turnover, kick-out, restart and scoring results | Breakthrough, possession phase, possession change, exit or scoring | Covered |
| Sequences | 78 | Lineout, scrum, penalty-touch, restart and outcome context | Phase context; explicit scoring, turnover, exit or stoppage | Covered |
| Kick | 68 | Box, touch, territorial, bomb, low and chip types; receipt/touch results | Ball travel; scoring where explicitly recorded | Covered |
| Defensive Action | 51 | Tackle arrival, aerial-kick contest and ball-steal maul types | Contact, contested receipt or breakdown | Covered |
| Missed Tackle | 41 | Bumped-off, stepped, positional and outpaced types; linked player when supplied | Evasion | Covered |
| Turnover | 32 | Error, ruck/maul, kick and carried-in-touch types | Possession change; out-of-play | Covered |
| Lineout Throw | 31 | Throw position, formation, catch/drive and player-count context | Set-piece | Covered |
| Lineout Take | 29 | Win/steal position and clean/tap result | Set-piece | Covered |
| Defensive Exits | 26 | Kicked-out or carried-out type | Exit travel or player-advance cue | Covered |
| Penalty Conceded | 19 | Infringement, sanction and scrum/ruck context | Stoppage | Covered |
| Scrum | 18 | Pass, pick-up, reset, penalty and rotation context | Set-piece | Covered |
| Sub Out | 18 | Tactical/replacement reason | Administration | Covered |
| Sub In | 18 | Tactical/replacement reason | Administration | Covered |
| Attacking 22 Entry | 16 | Explicit try, turnover or penalty outcome | Scoring, possession change or stoppage | Covered |
| Ref Review | 13 | Advantage or video-referee result | Administration | Covered |
| Restart | 11 | 50m, goal-line or 22m restart; length/direction/receipt context | Ball travel | Covered |
| Period | 10 | Period marker | Administration | Covered |
| Maul | 9 | Won, lost, penalty and rolling-maul context | Breakdown | Covered |
| Counter Attack | 8 | Transition outcome context | Player-advance cue | Covered |
| Try | 7 | Passing move, ruck, maul, kick or individual-effort result | Scoring | Covered |
| Goal Kick | 7 | Made/missed conversion result and post qualifier | Scoring with goal-kick travel cue | Covered |

## Route and motion boundary

The renderer permits a short local route, and optional event-local animation,
only for `Kick`, `Pass`, `Carry`, `Restart`, and `Goal Kick` when that single
row has a distinct endpoint other than the feed's common `(0,0)` placeholder.
In the representative file, the credible source pairs are 67 Kick, 347 Pass,
222 Carry, 10 Restart and 2 Goal Kick rows.

All other families use a stationary source-anchored cue. For example, contact
uses impact rings, missed tackles use an open evasion cue, breakdowns use a
compact cluster, and set pieces use a stationary marker. The renderer never
links one source event to the next.

## Maintaining the audit

`event_effect_coverage(events)` creates the detailed runtime table used by the
Event Replay coverage expander. When a new authorised Partner export is added,
review that table and update this document if its taxonomy changes.
