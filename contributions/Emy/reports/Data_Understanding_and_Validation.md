# Data Understanding and Validation

**Project:** P631 Accelerating Opposition Analysis in Professional Rugby
**Team:** T243
**Author:** Ngoc Ha Nguyen (n12248746)
**Week:** 11

## 1. Purpose

The Team's prototype now works with the Partner's event data. Before we rely on its outputs, we need to know three things. First, which fields in the dataset matter for opposition analysis. Second, whether the data is complete and internally consistent. Third, whether the metrics we calculate mean the same thing as the metrics the Partner already uses in their opposition preview.

This document records that review. The checks in Sections 4 and 5 are repeatable through `validate_reds_dataset.py`, and the full output is in `validation_results.md`.

## 2. What the dataset contains

| Item | Value |
|---|---|
| File | `949231_REDSvWARA_BI.xlsx` (one sheet) |
| Size | 3,588 event rows, 88 columns |
| Fixtures | 1 (FXID 949231) |
| Match | Queensland Reds (home) 26, NSW Waratahs 17 |
| Half-time score | 7 all |
| Competition | Super Rugby Pacific 2026, Round 5, Suncorp Stadium, 14 March 2026 |
| Events by team | Waratahs 2,063, Reds 1,525 |
| Grain | One row per recorded event, such as a tackle, pass, carry, kick or ruck arrival |

**Key limitation.** The Partner's existing opposition preview (Fijian Drua) is built from 12 matches and compares the opponent against competition averages and rankings. With one fixture, the prototype can reproduce the structure of those analyses but not the season-level numbers. Multi-match support is therefore a prerequisite for reproducing the full preview, not an optional extra.

## 3. Important fields (data dictionary)

Only the fields needed for the current analysis modules are listed. 37 of the 88 columns have the same value on every row, mostly match metadata such as venue, referee and scores, and 6 of these are completely empty.

| Field | Meaning | Used for | Notes from validation |
|---|---|---|---|
| `FXID` | Fixture identifier | Separating matches | Only one value in this file |
| `teamName`, `team_id` | Team that performed the event | Every module | For tackles this is the tackling team |
| `playerName`, `PLID` | Player who performed the event | Player tables | Empty for team-level events such as Possession, Sequences and Period (6.4%) |
| `playerShirtNumber`, `playerpositionName` | Shirt number and position for that match | Position analysis | Includes bench numbers 16 to 23, so position name is safer than shirt number |
| `period` | Half (1 or 2) | Game Intervals | Valid |
| `MatchTime` | Match clock | Game Intervals | Stored as MMSS, for example 4135 means 41 minutes 35 seconds. It must be converted before calculating intervals |
| `ps_timestamp`, `ps_endstamp` | Elapsed time in seconds | Event ordering, Event Replay | 91 rows go backwards, so sort before sequencing |
| `x_coord`, `y_coord` | Event location | Pitch maps, field zones | Team-relative. Each team attacks towards x = 100. Values above 100 or below 0 are in-goal. Width runs 0 to 68 |
| `x_coord_end`, `y_coord_end` | End location | Kick and carry paths | 75.6% of rows are (0,0), which appears to mean "not recorded" rather than a real location. To be confirmed with the Partner |
| `actionName` | Event category | Every module | 290 rows (8.1%) have codes 28 and 29 with no name |
| `ActionTypeName` | Event sub-type | Kick type, breakdown role, tackle type | For example Box, Bomb, Territorial. First Receiver, Second Receiver |
| `ActionResultName` | Event outcome | Kick outcome, tackle outcome | Empty for event types that have no outcome (31.1%) |
| `qualifier3Name` to `qualifier7Name` | Extra detail that depends on the action | Contested kicks, tackle order, tackle height | For tackles, qualifier5 is tackler order (1st Tackler) and qualifier6 is tackle height. For kicks, qualifier5 is contested or not contested |
| `assoc_playerName`, `assoc_playerTeamName` | Linked player, such as the ball carrier in a tackle | Evaded tackles, matchups | Filled for tackles, passes, carries, rucks and missed tackles |
| `PlayNum`, `SetNum`, `sequence_id` | Phase number and possession set | Linebreaks by phase | PlayNum appears to be the phase. The meaning of PlayNum 0 needs confirming |
| `hometeamCurrentScore`, `awayteamCurrentScore` | Running score | Game Intervals, score state | Never decreases and ends at 26 to 17 |

### How each preview section maps to the data

| Preview section | Fields used | Fit |
|---|---|---|
| Kick selection and outcomes | Kick events, `ActionTypeName`, `ActionResultName`, `qualifier5Name` | Same kick categories as the preview. Cross Pitch does not occur in this match |
| Breakdown choices | Playmaker Options, role in `ActionTypeName`, Pass, Carry or Kick in `ActionResultName`, `x_coord` for zone | Fields exist, but the counting rule and zone boundaries need confirming (Section 5) |
| Tackle outcomes and height | Tackle events, `ActionResultName`, `qualifier5Name` (first tackler), `qualifier6Name` (height) | Same 10 outcome categories and 3 height categories as the preview |
| Evaded tackles | Missed Tackle events, `ActionTypeName` (Bumped Off, Stepped, Outpaced, Positional), `assoc_playerName` (evader) | Same 4 categories as the preview |
| Linebreaks | Attacking Qualities with type Initial Break, result Line Break or Kick Line Break, `PlayNum` for phase | 11 linebreaks in this match (Reds 6, Waratahs 5) |
| Offloads | Carry events with result Off Load | 15 offloads |
| Game Intervals | `MatchTime` after MMSS conversion, `period`, scores, `x_coord` for zone | Works once the time is converted |

## 4. Data quality results

Full results are in `validation_results.md`. 29 checks were run. 17 passed and 12 were flagged for review. None of the flagged items stop the analysis, but each one affects how a metric must be calculated.

**Checks that passed**

| Check | Result |
|---|---|
| Points reproduced from Try and Goal Kick events | Reds 4 tries and 3 conversions = 26. Waratahs 3 tries and 1 conversion = 17. Matches the final score |
| Half-time score from events | One converted try each in the first half = 7 all. Matches |
| Running score | Never decreases and ends at 26 to 17 |
| Missed tackles | 41 Tackle events with result Missed equal 41 Missed Tackle events |
| Tackle pairs | Every tackle links a tackler and a ball carrier from opposite teams |
| Match clock | Seconds part never exceeds 59, and the match ends at 80 minutes |
| Duplicate events | None |
| Try locations | All 7 tries are at x = 101 or 102 for both teams in both halves, which confirms team-relative coordinates |

**Items flagged for review**

| Issue | Why it matters | How the prototype should handle it |
|---|---|---|
| `MatchTime` is MMSS, not seconds or minutes | Subtracting raw values gives wrong interval lengths | Convert to seconds before grouping into 10-minute intervals |
| 75.6% of end coordinates are (0,0) | This appears to represent missing endpoint data, but a real event at the corner cannot be told apart from a missing value | Treat (0,0) as missing until the Partner confirms, and only draw paths where an end point exists |
| 290 events with action codes 28 and 29 but no name | These events are invisible in any analysis that filters by name | Ask the Partner what the codes mean |
| Coordinates on non-spatial events (Sub In, Sub Out, Period) | They would appear as false points on a pitch map | Exclude non-spatial events from pitch views |
| 91 rows where time goes backwards | Phase and sequence logic depends on order | Sort by `ps_timestamp` and `ID` before building sequences |
| Bench shirt numbers 16 to 23 | The preview groups by positions 1 to 15 | Use `playerpositionName`, or ask how the Partner maps replacements |
| 6 fully empty columns | No impact, but adds noise | Drop at load time |

## 5. Do the metrics make sense for rugby analysis?

### 5.1 Definitions that change the numbers

1. **Breakdown decisions.** In this match, 125 of 399 Playmaker Options are passes by the halfback at the breakdown. In the Partner's preview, "Pass from breakdown" is between 0.7% and 6.1% of decisions in every zone. A simple row count would therefore produce very different percentages from the Partner's report. The Partner most likely counts one decision per breakdown, so the routine halfback pass is replaced by the first receiver's decision. This rule must be confirmed before the Breakdown Choices module is treated as validated.
2. **Field zones A, B, M, C and D.** The zones are not stored in the data. The prototype currently uses four temporary 25-metre bands, while the preview uses five zones plus a separate within-5m view. The preview's own numbers support that D is the defending team's own 22 and A is the opposition 22, because kicking is the most common choice in zone D and is almost never chosen in zone A. The exact boundaries still need confirming.
3. **Dominant tackle.** The data has a Dominant Tackle qualifier (25 in this match), but the preview ranks "dominant tackles" by sack rate. These are not the same measure.
4. **Phase.** `PlayNum` behaves like the phase number. PlayNum 0 has no obvious rugby meaning and should be confirmed.

### 5.2 Reconciliation of the Partner's opposition preview

I also recalculated the numbers inside the Partner's Fijian Drua preview to check that the existing reports are internally consistent. This tells us which metrics are reliable targets for the prototype to reproduce.

| Preview section | Result | Notes |
|---|---|---|
| Kicking | Mostly consistent | 307 kicks reconcile across kick type, kicker, phase and per-game averages over 12 games. Three issues found. The "All teams" average row sums to 28.2 but is shown as 26.4. Box kicks to touch are 11 in the chart, but the 13.0% in the outcome table implies 10. Box kick outcome rows add to between 96% and 98.5%. Separately, kicks by position total 293, which is 14 fewer than 307, and are not explained on any slide |
| Linebreaks (attack and defence) | Consistent | Totals of 69, 72, 84 and 88 reconcile across outcome, phase, position and player views. Rankings are consistent across sections |
| Breakdown choices | Consistent | All 12 count and percentage columns across 6 zones reconcile |
| Tackling | Consistent | Team totals of 25,646 and 1,967, the 254 missed tackles, and every player row reconcile across all tables |
| Evaded tackles and offloads | Consistent | Both tables share the same denominator for each player (times tackled) |

The preview also showed presentation issues that the prototype can address. Colours for positions and phases change between side-by-side charts, tables are sorted differently in each zone, sample sizes are not shown next to percentages, and some labels mix "they" and "we".

## 6. Questions for the Partner

1. What do action codes 28 and 29 represent?
2. What are the exact x boundaries of field zones A, B, M, C and D?
3. How is a breakdown decision counted? Is the halfback's pass to the first receiver counted as a decision?
4. What does PlayNum 0 mean, and does PlayNum 1 correspond to "1st phase" in the preview?
5. Is "dominant tackle" defined by the Dominant Tackle qualifier or by sack outcome?
6. How should replacements (shirts 16 to 23) be grouped in position analysis?
7. Is a minimum sample size used when ranking players by percentage?
8. Do end coordinates of (0,0) mean that the end point was not recorded?
9. Can more fixtures be provided so that multi-match and competition-average analysis can be tested?
