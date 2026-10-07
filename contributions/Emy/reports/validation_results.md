# Data Validation Results

Source file: `949231_REDSvWARA_BI.xlsx`. Rows: 3588. Columns: 88.

| Area | Check | Expected | Actual | Status |
|---|---|---|---|---|
| Structure | Event rows | > 0 | 3588 | Pass |
| Structure | Fixtures in file | 1 or more | 1 | Pass |
| Structure | Teams per fixture | 2 | 2 | Pass |
| Structure | Duplicate event IDs | 0 | 0 | Pass |
| Structure | Fully empty columns | none | qualifier8Name, qualifier9Name, qualifier10Name, cityName, homecoachName, awaycoachName | Review |
| Structure | Constant columns (match metadata repeated per row) | expected for one fixture | 37 | Review |
| Completeness | Missing playerName | low or explained | 6.4% | Review |
| Completeness | Missing actionName | low or explained | 8.1% | Review |
| Completeness | Missing ActionTypeName | low or explained | 10.2% | Review |
| Completeness | Missing ActionResultName | low or explained | 31.1% | Review |
| Completeness | Events without a player are team-level events | Possession, Sequences, Period and similar | {'Possession': 84, 'Sequences': 78, 'Defensive Exits': 26, 'Attacking 22 Entry': 16, 'Ref Review': 13, 'Period': 10, nan: 2} | Review |
| Completeness | Action codes without a name | none | {28: 144, 29: 144, 17: 2} | Review |
| Completeness | End coordinates stored as 0,0 | appears to mean not recorded, to confirm with Partner | 75.6% of rows | Review |
| Validity | MatchTime stored as MMSS (seconds part 0 to 59) | all <= 59 | 59 | Pass |
| Validity | Match length after MMSS conversion (minutes) | about 80 plus stoppage | 80.0 | Pass |
| Validity | Periods | 1 and 2 | [1, 2] | Pass |
| Validity | x_coord outside 0 to 100 | in-goal events only (tries and similar) | {'Try': 7, 'Tackle': 2, 'Period': 2, 'Sub Out': 2, 'Sub In': 2, 'Defensive Exits': 1, 'Restart': 1, 'Sequences': 1, 'Ref Review': 1} | Review |
| Validity | y_coord range | 0 to 70 | 0 to 68 | Pass |
| Validity | Rows where timestamp goes backwards | 0, or sort before analysis | 91 | Review |
| Consistency | Points reproduced from Try and Goal Kick events equal final score | Queensland Reds 26, NSW Waratahs 17 | Queensland Reds 26, NSW Waratahs 17 | Pass |
| Consistency | First-half points reproduced from events equal half-time score | Queensland Reds 7, NSW Waratahs 7 | Queensland Reds 7, NSW Waratahs 7 | Pass |
| Consistency | Running score never decreases | 0 | 0 | Pass |
| Consistency | Final running score equals recorded FT score | (26, 17) | (26, 17) | Pass |
| Consistency | Tackle result 'Missed' equals Missed Tackle events | 41 | 41 | Pass |
| Consistency | Tackle team and associated ball carrier are on opposite teams | 100% | 100% | Pass |
| Consistency | isHome and result agree with final score | home team result W | home team result W | Pass |
| Rugby logic | All tries recorded at x > 100 for both teams and both halves | team-relative coordinates, attack towards x = 100 | [101, 102, 102, 102, 101, 102, 101] | Pass |
| Rugby logic | Average kick position is in own half | < 50 | 37.9 | Pass |
| Rugby logic | Halfback passes counted as a breakdown 'decision' | rule to confirm with Partner | 125 of 399 options | Review |

## Missing values in key fields

| Field | Missing |
|---|---|
| FXID | 0.0% |
| teamName | 0.0% |
| playerName | 6.4% |
| MatchTime | 0.0% |
| period | 0.0% |
| x_coord | 0.0% |
| y_coord | 0.0% |
| x_coord_end | 0.0% |
| y_coord_end | 0.0% |
| actionName | 8.1% |
| ActionTypeName | 10.2% |
| ActionResultName | 31.1% |
| PlayNum | 0.0% |
| SetNum | 0.0% |
| assoc_playerName | 67.1% |
| playerpositionName | 6.4% |
| playerShirtNumber | 6.4% |

## Event counts by action and team

| actionName          |   NSW Waratahs |   Queensland Reds |
|:--------------------|---------------:|------------------:|
| Attacking 22 Entry  |              8 |                 8 |
| Attacking Qualities |             64 |                59 |
| Carry               |            141 |                89 |
| Collection          |            376 |               219 |
| Counter Attack      |              6 |                 2 |
| Defensive Action    |             17 |                34 |
| Defensive Exits     |             12 |                14 |
| Goal Kick           |              3 |                 4 |
| Kick                |             37 |                31 |
| Lineout Take        |             14 |                15 |
| Lineout Throw       |             16 |                15 |
| Maul                |              8 |                 1 |
| Missed Tackle       |             22 |                19 |
| Pass                |            222 |               127 |
| Penalty Conceded    |              7 |                12 |
| Period              |              0 |                10 |
| Playmaker Options   |            278 |               121 |
| Possession          |             45 |                39 |
| Ref Review          |              7 |                 6 |
| Restart             |              5 |                 6 |
| Ruck                |            120 |                65 |
| Ruck OOA            |            277 |               193 |
| Scrum               |              8 |                10 |
| Sequences           |             41 |                37 |
| Sub In              |             10 |                 8 |
| Sub Out             |             10 |                 8 |
| Tackle              |            142 |               211 |
| Try                 |              3 |                 4 |
| Turnover            |             20 |                12 |