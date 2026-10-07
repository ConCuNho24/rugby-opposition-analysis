# Queensland Reds Opposition Analysis Prototype

## Overview

This IFB398 Capstone prototype explores how parts of the Queensland Reds opposition-analysis workflow can be automated using recorded match event data.

The application loads authorised event files, validates and transforms the supplied data, then presents selected fixture and team analysis through a Streamlit interface. The main aim is to reduce repetitive data preparation so that more time can be spent interpreting results and communicating useful information to coaches.

## Week 11 prototype

The earlier project prototype used public rugby data to explore match-event processing and visualisation.

The Week 11 version moves to the representative Queensland Reds event schema and focuses on analysis that can be supported directly by the supplied Partner data.

The earlier public-data prototype is retained separately in:

```text
prototype_match_analysis/
```

## Workflow

```text
Partner XLSX / CSV
        ↓
Load and validate
        ↓
Transform event data
        ↓
Run rugby analysis
        ↓
Streamlit visualisation
```

## Current features

| Feature | Description |
| --- | --- |
| **Data upload** | Upload one or more authorised XLSX or CSV event files. Files are processed in memory and validated before analysis. |
| **Fixture and team selection** | Select a fixture and then focus the analysis on one team from that match. |
| **Overview** | Provides a simple summary of the selected fixture, team and available event data. |
| **Key Insights** | Generates short factual observations from calculated event statistics. |
| **Game Intervals** | Groups recorded event activity into 10-minute MatchTime intervals. |
| **Event Replay** | Displays recorded events sequentially on the rugby field. Event-specific visual cues are used for ball movement, contact, evasion, breakdown and other event types. Where a single event contains valid start and end coordinates, the recorded event path can also be visualised. |
| **Kicking** | Analyses kick types, outcomes, kickers, listed player positions, recorded receipt-contest status and field locations. |
| **Linebreaks** | Analyses recorded Initial Break events, including player, position, location and team-level achieved/conceded counts. |
| **Breakdown Choices** | Analyses recorded Playmaker Options such as Pass, Carry and Kick together with receiver context and field position. |
| **Tackling** | Analyses tackle outcomes, missed tackles, first-tackler records, tackle height, dominant-tackle qualifiers and linked evasion records where available. |

## Project structure

```text
analysis_week11/
├── app/
│   └── streamlit_app.py
│
├── src/
│   └── week11_analysis/
│       ├── data/
│       ├── analysis/
│       └── visualisation/
│
├── tests/
├── docs/
├── data/
│   └── raw/              # local Partner data, ignored by Git
│
├── outputs/              # generated local outputs, ignored by Git
├── requirements.txt
├── .gitignore
└── README.md
```

## Main implementation areas

The main code is organised into separate stages so that analysis logic is not tied directly to the Streamlit interface.

```text
src/week11_analysis/data/
    Data loading, validation and transformation

src/week11_analysis/analysis/
    Kicking, linebreak, breakdown, tackling,
    interval, insight and replay-related analysis

src/week11_analysis/visualisation/
    Rugby pitch and chart visualisation

app/streamlit_app.py
    Streamlit application and user interaction

tests/
    Automated tests for data processing,
    analysis and Event Replay behaviour
```

## Run locally

### 1. Open the project

From the repository root:

```powershell
cd contributions\Kelvin\analysis_week11
```

### 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Set the source path

```powershell
$env:PYTHONPATH = "src"
```

### 5. Start the application

```powershell
python -m streamlit run app\streamlit_app.py
```

Streamlit will display the local address in the terminal.

## Using the prototype

1. Start the Streamlit application.
2. Upload one or more authorised XLSX or CSV event files.
3. Select a fixture.
4. Select a team.
5. Open the required analysis page.

The normal workflow uses uploaded files rather than fixed local paths.

An **Advanced / Development input** is also available for local development when a file path is more convenient.

## Testing

From `analysis_week11`, run:

```powershell
$env:PYTHONPATH = "src"
python -m pytest -v
```

The test suite covers areas including:

- data loading and validation;
- event transformation;
- XLSX and CSV handling;
- multi-file input;
- kicking analysis;
- linebreak analysis;
- breakdown analysis;
- tackling analysis;
- game intervals and Key Insights;
- Event Replay ordering and event effects;
- pitch visualisation behaviour.

With the authorised representative Partner workbook available locally, the current project passes:

```text
93 passed
```

Some regression checks use the local Partner workbook and are designed to skip when that ignored file is not available. Partner source data is not required to be committed to GitHub.

## Event Replay

Event Replay visualises the sequence and location of recorded match events.

Different event categories use different visual cues where appropriate, including:

- ball travel;
- player advance;
- tackle/contact;
- missed-tackle evasion;
- breakdown events;
- set pieces;
- scoring events;
- administrative events.

Where the source contains valid start and end coordinates for the same event, the replay can show movement between those two recorded points.

The replay is event-based. It does not reconstruct continuous player tracking or infer missing player positions between separate events.

Further detail is available in:

```text
docs/event_effect_coverage.md
```

## Current limitations

The prototype is currently limited by the data and definitions available at this stage of the project.

- Current Partner validation is mainly based on one representative fixture.
- Multi-match opponent trends and competition comparisons require additional fixtures.
- Official Queensland Reds field-zone definitions have not yet been confirmed, so Breakdown Choices currently uses relative field-position bands rather than official zones.
- Event Replay uses recorded event coordinates rather than continuous GPS or player-tracking data.
- True Ball-in-Play duration is not calculated from the current event file.
- Some Partner-specific analytical definitions still require confirmation before they can be reproduced reliably.

## Documentation

Additional project documentation is available under `docs/`.

### `week11_scope.md`

Explains the change from the earlier public-data prototype to the current Partner-schema prototype and summarises the current project scope.

### `source_feature_mapping.md`

Maps Partner data fields and event concepts to the corresponding prototype features.

### `pdf_coverage_matrix.md`

Compares the current prototype with the supplied opposition-preview example and identifies supported areas and remaining gaps.

### `event_effect_coverage.md`

Documents the event categories used by Event Replay and their visual treatment.

### `event_replay_manual_checklist.md`

Provides a simple manual checklist for reviewing Event Replay behaviour.

## Data handling

Partner-provided source files remain local and are excluded from Git.

The repository `.gitignore` excludes local or generated content including:

```text
data/raw/*
outputs/*
.venv/
__pycache__/
.pytest_cache/
```

Partner data should only be used and shared in accordance with the project team's authorised access.

## Next steps

The main next steps are:

- validate the pipeline against additional Partner fixtures;
- develop multi-match opposition analysis once more fixtures are available;
- confirm Partner-specific definitions such as field zones and other analytical measures;
- confirm the preferred final reporting/output format with the project team;
- continue validating the prototype with the tutor and Partner before Phase 2 development.