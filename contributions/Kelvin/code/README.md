# Interactive Rugby Match Analysis from Structured CSV Data

## Week 9 proof of concept

This contribution demonstrates how structured Rugby Union match data can be
turned into an interactive, analyst-directed report. A user selects one match
and one question to investigate; the application then filters the relevant CSV
records, calculates descriptive metrics, and presents tables, charts, event
locations, and conservative rule-based observations.

The prototype addresses the following technical question:

> Can event-level, team-level, and player-level Rugby Union data be processed
> automatically and presented through a simple interface without requiring the
> analyst to write code?

This is not presented as a complete opposition-analysis product. It is a small,
isolated prototype intended to demonstrate a working data pipeline and user
interaction pattern.

## What the prototype demonstrates

The implemented workflow is:

```text
CSV match dataset
        |
        v
match selected by match_id
        |
        v
event, team, player, and metadata rows filtered with pandas
        |
        v
user selects one analysis question
        |
        v
metrics and clearly labelled derived values calculated
        |
        v
Streamlit tables + Plotly charts + factual observations
```

The design is intentionally question-led. The interface does not place every
chart on one dashboard. Instead, the analyst chooses what to investigate, such
as attacking statistics, set pieces, kicking, discipline, scoring, or an
individual player metric.

## Data used

The bundled dataset contains 10 Super Rugby 2026 matches derived from
Sportradar Rugby Union data:

- 10 match metadata rows;
- 3,857 chronological timeline events;
- 20 team-statistics rows, representing two teams per match;
- 459 player-statistics rows; and
- 20 period-score rows.

The application uses the following CSV tables:

| CSV file | Granularity | Purpose in the prototype |
|---|---:|---|
| `match_metadata.csv` | One row per match | Match selector, teams, venue, competition, final score |
| `combined_match_events.csv` | One row per recorded event | Event counts, locations, kicking, turnovers, penalties, scoring |
| `team_statistics.csv` | One row per team per match | Attack, defence, set piece, discipline, broader team comparison |
| `player_statistics.csv` | One row per player per match | Selectable player leaderboards |
| `period_scores.csv` | One row per period per match | Loaded as an available supporting table; not required by current views |

All tables are filtered by `match_id` before calculations are performed. This
prevents records from different matches being combined accidentally.

## Code organisation

The implementation is deliberately small and uses three Python modules:

### `app.py`

Controls the Streamlit user flow:

- included-data mode or uploaded event CSV;
- match selection;
- match-information summary;
- analysis selection; and
- presentation of the selected result.

The file mainly coordinates functions rather than containing the analytics
logic itself.

### `analysis.py`

Contains data-processing responsibilities:

- CSV loading and validation;
- missing-column handling;
- numeric conversion;
- `match_id` filtering;
- team and player metric calculation;
- event filtering and counting;
- scoring-event preparation; and
- rule-based factual observations.

Raw source values remain unchanged internally. Friendly labels are applied only
at display time through a mapping dictionary.

### `charts.py`

Contains Plotly visualisation functions:

- grouped team comparisons;
- single-metric comparisons;
- player leaderboards;
- scoring timelines; and
- a reusable Rugby Union pitch for event locations.

Keeping chart construction separate from calculations makes it possible to
inspect the data logic without also reading the Streamlit interface code.

## Analysis options

| Analysis | Main evidence displayed |
|---|---|
| Match Overview | Final score, possession, tries, selected team statistics |
| Team Performance | Broader comparison of possession, attack, defence, and discipline values |
| Attacking Analysis | Carries, metres, passes, offloads, clean breaks, tries, player leaders |
| Defensive Analysis | Tackles, missed tackles, turnovers won, player leaders |
| Set Piece Analysis | Lineouts won, scrums won/lost, total scrums, set-piece locations |
| Kicking Analysis | `ball_kicked`, `kick_to_touch`, and source-provided kick locations |
| Turnover Analysis | Turnover counts, locations, and the next recorded timeline event |
| Discipline Analysis | Penalties conceded, cards, and `penalty_awarded` locations |
| Event Locations | User-selected event type and team plotted on the pitch |
| Scoring Analysis | Scoring timeline, scorer table, and available scoring locations |
| Player Analysis | User-selected player metric displayed as a table and leaderboard |

Each view includes a **Match observations** section. These statements are
generated from deterministic comparisons of calculated results. No language
model is used, and no tactical intent is inferred.

## Source and calculated metrics

Most displayed values come directly from the CSV data. Examples include:

- ball possession;
- carries and metres run;
- passes, offloads, and clean breaks;
- tackles and missed tackles;
- tries and penalty goals;
- turnovers won;
- lineouts and scrums;
- penalties conceded and cards; and
- exact source event counts.

The prototype calculates only three additional rates:

```text
Metres per carry = meters_run / carries

Tackle success rate = tackles / (tackles + tackle_missed) * 100

Scrum success rate = scrums_won / total_scrums * 100
```

These are explicitly labelled as calculated metrics. A value is left
unavailable when its denominator is zero or missing.

## Rugby pitch visualisation

Event coordinates are plotted over a reusable field created with Plotly shapes.
The visual includes:

- a 0-100 by 0-70 main playing area;
- goal lines;
- halfway and 22-metre lines;
- 5-metre and 15-metre guides; and
- fixed display limits of x = -5 to 115 and y = -5 to 75.

The limits include the complete coordinate range in the supplied dataset while
preventing Plotly from producing misleading automatic ranges. Coordinates are
not changed or clamped.

The plot represents recorded event locations, not player movement. The source
does not explicitly establish attacking direction, so the prototype does not
make left-to-right or territorial interpretations.

## Data-integrity decisions

Several constraints are enforced to avoid overclaiming:

1. Source event terminology is retained. For example, `ball_recycled` is not
   renamed as a ruck, carry, or tackle.
2. Events without a recorded team are not counted as team events.
3. Missing x/y coordinates are excluded only from location plots, not from
   non-spatial event counts.
4. Missing scorer names are displayed as `Not provided`.
5. `ball_kicked` and `kick_to_touch` remain separate source labels; the code
   does not assume that two records represent one unique physical kick.
6. The turnover follow-up category describes only the immediately following
   timeline record, not a reconstructed possession sequence.
7. `penalty_awarded` event locations are not treated as equivalent to the
   box-score field `penalties_conceded`.

## CSV upload behaviour

The included dataset is the primary demonstration mode. The user may instead
upload a compatible event-level CSV. Event-based analyses continue to work in
that mode. Analyses that require team or player box-score tables display a
clear unavailable-data message rather than failing or inventing values.

Validation also provides readable errors for an empty CSV, a missing
`event_type` column, or missing home/away team information.

## Verification completed

The prototype was checked programmatically against the supplied data:

- all 10 matches appear in the selector;
- changing the selected match changes the filtered data;
- all 11 analysis views run for the included dataset;
- all 11 views fail gracefully with an event-only uploaded CSV;
- 3,857 events and the expected team/player tables load successfully;
- missing coordinates and missing scorer information do not cause a crash;
- the included-data mode hides the CSV uploader;
- the Rugby pitch uses fixed, non-extreme axis ranges; and
- a live Streamlit server returned a successful health response.

## Scope and limitations

- Results describe one selected match and cannot establish season-long team
  tendencies.
- The prototype reports recorded data and does not evaluate tactical quality.
- It does not reconstruct possession chains, player movement, or attacking
  direction.
- Data completeness depends on the source provider.
- Upload mode accepts one event-level CSV and therefore cannot reproduce
  team/player box-score analysis unless those tables are part of the included
  dataset.
- The prototype does not include a database, authentication, external API,
  live data, machine learning, or video analysis.

These boundaries are deliberate. The contribution demonstrates a small,
traceable path from structured match data to interactive descriptive analysis
without presenting the output as advanced tactical insight.

## Minimal execution check

From `contributions/Kelvin/code`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m streamlit run app.py
```
