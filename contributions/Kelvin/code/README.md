# Rugby Match Analysis Prototype

This is a small Week 9 proof of concept for interactively exploring one Rugby
Union match at a time. It uses CSV data, pandas calculations, Plotly charts,
and a Streamlit web interface.

The app is intentionally descriptive. It does not use an LLM, reconstruct
possessions, infer attacking direction, or make tactical claims from one match.
It is isolated from the repository's main rugby-analysis pipeline.

## CSV dataset

The standalone GitHub contribution reads its included 10-match dataset from:

```text
data\sportradar_10_matches_csv
```

When this prototype is run from its original repository-root location, it can
also use `data\raw\sportradar_10_matches_csv`. The app automatically prefers
the bundled folder when it exists.

The important files are:

- `match_metadata.csv`: one row per match, including teams, competition,
  season, venue, final score, and event count.
- `combined_match_events.csv`: all chronological timeline events for all 10
  matches, including source event type, team, time, score, and available x/y
  coordinates.
- `team_statistics.csv`: one row per team per match with possession, carries,
  metres, tackles, set pieces, discipline, and other box-score statistics.
- `player_statistics.csv`: player-level match statistics used for leaderboards.
- `period_scores.csv`: period-level scores. It is loaded for possible simple
  extensions but is not required by the current charts.
- `individual_match_events/`: one compatible event CSV per match. These files
  can be used to demonstrate upload mode.

The old JSON sample may still exist in the prototype folder for preservation,
but the application does not read it and no JSON file is required.

## Files in this prototype

- `app.py`: Streamlit page, data-source choice, match selector, and the 11
  analysis views.
- `analysis.py`: CSV loading, validation, match filtering, calculations, label
  mappings, and rule-based observations.
- `charts.py`: comparison charts, player charts, scoring timeline, and reusable
  rugby-pitch plotting.
- `requirements.txt`: Streamlit, pandas, and Plotly only.

## Install and run on Windows PowerShell

Open PowerShell and run these commands one at a time:

```powershell
cd C:\IFB398\rugby-opposition-analysis\prototype_match_analysis

python -m venv .venv

.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt

python -m streamlit run app.py
```

Inside the team repository, use the contribution directory instead:

```powershell
cd C:\IFB398\rugby-opposition-analysis\contributions\Kelvin\code
```

Then run the same virtual-environment, install, and Streamlit commands shown
above.

After the last command, Streamlit normally opens the application in the default
browser. If it does not, open the local address printed in PowerShell, usually:

```text
http://localhost:8501
```

If PowerShell blocks activation, run this in the same PowerShell window and
then repeat the activation command:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

This changes policy only for the current PowerShell process.

## Use the included 10-match dataset

1. Leave **Use included CSV dataset** selected.
2. The upload control remains hidden in this mode.
3. Choose one of the 10 fixtures from **Select match**.
4. Confirm the teams, final score, venue, and timeline-event count.
5. Choose one item from **Choose analysis**.
6. Use any additional team, event, or player-metric selector shown by that
   analysis.

Changing the match filters events, team statistics, player statistics, and
period scores using `match_id` before the selected analysis is calculated.

## Upload another event CSV

1. Clear **Use included CSV dataset**.
2. The match selector disappears and **Upload a compatible event-level CSV**
   appears.
3. Upload `combined_match_events.csv` or one file from
   `individual_match_events/`.
4. If the uploaded CSV contains multiple match IDs, choose the required match
   after upload.

At minimum, the upload needs an `event_type` column and must identify the home
and away teams. A file compatible with the included event CSVs provides the best
result.

Only one event CSV is uploaded in this deliberately small prototype. Therefore,
event analyses continue to work, while pages requiring `team_statistics.csv` or
`player_statistics.csv` show a friendly unavailable-data message.

## Application workflow

```text
included or uploaded CSV
        -> validate with pandas
        -> select match_id
        -> filter relevant CSV rows
        -> choose one analysis
        -> calculate metrics
        -> display tables, charts, pitch locations, and factual observations
```

## Available analyses

1. **Match Overview**: final score, possession, tries, and selected team
   statistics. Uploaded event-only data falls back to event counts.
2. **Team Performance**: a broader team comparison plus calculated metres per
   carry and tackle success rate.
3. **Attacking Analysis**: carries, metres, passes, offloads, clean breaks,
   tries, try assists, and selectable player leaders.
4. **Defensive Analysis**: tackles, missed tackles, turnovers won, calculated
   tackle success, and defensive player leaders.
5. **Set Piece Analysis**: lineouts won, scrum statistics, calculated scrum
   success, and selectable set-piece event locations.
6. **Kicking Analysis**: source `ball_kicked` and `kick_to_touch` counts shown
   with friendly labels, plus kick locations.
7. **Turnover Analysis**: turnover event counts, locations, and classification
   of only the next recorded timeline event.
8. **Discipline Analysis**: penalties conceded, yellow cards, red cards, and
   `penalty_awarded` event locations.
9. **Event Locations**: any available event type filtered by team.
10. **Scoring Analysis**: scoring timeline, scorer table, and optional scoring
    locations.
11. **Player Analysis**: a team and metric selector with a short leaderboard.

## Source metrics and calculated metrics

Values such as carries, metres run, tackles, missed tackles, turnovers won,
scrums won, tries, cards, and penalties conceded come directly from the CSV
source data.

The prototype calculates only these clearly labelled values:

```text
Metres per carry = meters_run / carries

Tackle success rate = tackles / (tackles + tackle_missed) * 100

Scrum success rate = scrums_won / total_scrums * 100
```

A calculated value is left unavailable when its denominator is zero or missing.

## Rugby pitch visualisation

Location views draw a reusable pitch with:

- the 0-100 by 0-70 playing area;
- goal lines, halfway line, and 22-metre lines;
- optional 5-metre and 15-metre guides;
- fixed display limits of x = -5 to 115 and y = -5 to 75.

The slightly wider fixed limits keep the real source coordinates visible,
including a few points just outside the main playing area, while preventing
Plotly from creating extreme automatic ranges. Source coordinates are neither
changed nor clamped.

The plot shows recorded event locations only. It does not represent player
movement and does not infer which direction a team was attacking.

## Recommended 3-5 minute tutor demonstration

1. Start on **Match Overview** with Highlanders vs Crusaders and explain that
   the match was selected from `match_metadata.csv`, then filtered by
   `match_id` across the other CSVs.
2. Open **Team Performance** and point out the difference between source
   statistics and the two clearly labelled calculated metrics.
3. Open **Kicking Analysis**, switch teams, and show recorded kick locations on
   the fixed rugby pitch.
4. Open **Event Locations**, choose a team and another event type to demonstrate
   flexible pandas filtering.
5. Finish with **Player Analysis** or **Scoring Analysis** to show that the same
   selected match supports both team-level and player/event-level questions.

Before presenting, click **Don't show again** on any Streamlit helper popup such
as "Help agents write better apps". The prototype does not use unsupported CSS
to hide Streamlit system interface elements.

## Limitations to mention

- Results describe one selected match and do not establish long-term team
  tendencies or tactical superiority.
- Source event names remain unchanged internally. For example,
  `ball_recycled` is not renamed as a ruck, carry, or tackle.
- `ball_kicked` and `kick_to_touch` are separate source records; the app does
  not assume they are unique physical kicks.
- A turnover's following category is only the next recorded event, not a
  reconstructed possession sequence.
- `penalty_awarded` event locations are kept separate from the team box-score
  field `penalties_conceded`.
- Some source events have no team, scorer, or coordinates. They are handled
  safely but cannot be reconstructed.
- The coordinate system does not explicitly confirm attacking direction.
- Upload mode accepts one event-level CSV, so detailed team/player pages require
  the included dataset.
