# Technology Research and Justification

## 1. Purpose and Technology Decision

The purpose of this technology research is to identify and justify technologies that support the **P631 – Accelerating Opposition Analysis in Professional Rugby** project. The selected technologies need to work with the rugby event data supplied by the industry partner, support the current analysis workflow, and integrate with the prototype implementation developed by the team.

The technology selection is based on three main considerations:

1. compatibility with the available rugby data;
2. compatibility with the existing prototype developed by Kelvin; and
3. the ability to reduce repetitive manual work involved in opposition analysis.

The current technology direction is based on **Python, Pandas, Streamlit and Plotly**. These technologies are already demonstrated in Kelvin's prototype and therefore provide a lower-risk foundation for further development.

Tableau is treated as the **existing/reference analysis workflow**, while technologies such as SQLite and React/FastAPI are considered potential future improvements rather than technologies required by the current prototype.

The proposed technology architecture is:

```text
Partner / Source Rugby Event Data
              |
              v
       Data Ingestion
              |
              v
   Validation + Normalisation
              |
              v
       Pandas DataFrames
              |
              v
       Analysis Layer
       (Kelvin's Code)
              |
              v
        Streamlit UI
              |
              v
        Plotly Outputs
```

This architecture allows the team to build on the existing implementation rather than replacing working components with an unnecessarily complex technology stack.

---

# 2. Data and Technology Requirements

## 2.1 Partner Dataset

The supplied Tableau workbook provides evidence about the structure of the rugby data used in the project. The dataset is an **event-level dataset**, where individual records contain information about events occurring during rugby matches.

The source contains fields relating to:

- event and player identifiers;
- player names;
- team names;
- match time and period;
- event/action types;
- event results;
- player information;
- event coordinates;
- metres;
- play, set and sequence information;
- home and away teams;
- scores;
- competition;
- season;
- round;
- venue; and
- player position.

Examples of relevant fields include:

`ID`, `FXID`, `PLID`, `playerName`, `teamName`, `MatchTime`, `period`, `x_coord`, `y_coord`, `actionName`, `ActionTypeName`, `ActionResultName`, `Metres`, `PlayNum`, `SetNum`, `sequence_id`, `homeTeamName`, `awayTeamName`, `datePlayed`, `season`, `playerpositionName`, and `competitionName`.

The Tableau workbook also contains analysis views such as:

- **Event Count by Action**
- **Event Locations on Field**
- **Team Event Comparison**

These views demonstrate that the project requires both event-level and aggregated analysis.

For example:

```text
Raw Event Data
      |
      +---- Event Count
      |
      +---- Event Location
      |
      +---- Team Comparison
```

This structure is well suited to a Python-based data-processing pipeline because the system needs to filter, group and aggregate large numbers of event records.

---

# 3. Python

## Purpose

Python is recommended as the main programming language for the project.

Python is responsible for:

- loading source data;
- validating data;
- cleaning and transforming records;
- calculating statistics;
- filtering matches and teams;
- generating analysis results;
- connecting the analysis components; and
- supporting the Streamlit application.

## Justification

Python is particularly suitable because it is already used in Kelvin's prototype.

The current implementation separates the application into several components:

```text
app.py
   |
   +---- User interaction
   |
analysis.py
   |
   +---- Data loading and analysis
   |
charts.py
   |
   +---- Data visualisation
```

This means the team can continue improving the existing implementation instead of introducing another programming language.

Python also has a large ecosystem for data processing and visualisation. This makes it suitable for an application where the primary technical requirement is processing structured rugby event data.

**Decision:** Python is **recommended and already implemented**.

**Source:** Python Software Foundation, [Python CSV Documentation](https://docs.python.org/3/library/csv.html)

---

# 4. Pandas

## Purpose

Pandas is used as the main data-processing library.

It supports:

- CSV loading;
- DataFrame creation;
- data filtering;
- grouping and aggregation;
- numeric conversion;
- missing-value handling;
- calculation of derived metrics; and
- preparation of data for visualisation.

## Justification

The partner dataset consists primarily of structured tabular data. Each event is represented as a row with multiple attributes such as player, team, action, time and location.

This makes Pandas DataFrames appropriate for processing the data.

Kelvin's existing `analysis.py` already uses Pandas to process the rugby datasets. The implementation loads the data, validates required fields, converts values where necessary, filters data by match, and calculates analysis metrics.

For example:

```text
Rugby CSV
    |
    v
Pandas DataFrame
    |
    v
Filter relevant events
    |
    v
Group / aggregate
    |
    v
Analysis results
```

Pandas also allows the same processing logic to be reused across different matches rather than manually preparing each match.

**Decision:** Pandas is **recommended and already implemented**.

**Source:** Pandas Development Team, [Pandas Documentation](https://pandas.pydata.org/docs/getting_started/)

---

# 5. Data Normalisation and Canonical Schema

A key technical issue is that the partner dataset and Kelvin's current prototype do not use exactly the same field names.

Therefore, the project should use a **data normalisation layer** between the source dataset and the analysis code.

The purpose of this layer is to convert source-specific field names into a consistent internal schema.

For example:

| Canonical Field | Partner Dataset | Kelvin Prototype |
|---|---|---|
| `event_id` | `ID` / `FXID` | Event identifier |
| `player_name` | `playerName` | `player_name` |
| `team` | `teamName` | `team` |
| `event_type` | `actionName` | `event_type` |
| `event_result` | `ActionResultName` | Result field |
| `match_time_minute` | `MatchTime` | `match_time_minute` |
| `period` | `period` | `period` |
| `x` | `x_coord` | `x` |
| `y` | `y_coord` | `y` |
| `home_team` | `homeTeamName` | `home_team` |
| `away_team` | `awayTeamName` | `away_team` |
| `season` | `season` | `season` |
| `round` | `roundNumber` | `round` |
| `competition` | `competitionName` | `competition` |
| `venue` | `venueName` | `venue` |

The exact mapping should be validated against the partner's data dictionary before implementation.

The proposed pipeline is therefore:

```text
Partner Dataset
      |
      v
Validation
      |
      v
Field Mapping
      |
      v
Canonical Schema
      |
      v
Kelvin's Analysis Functions
```

This approach is important because it allows the team to reuse Kelvin's analysis code without modifying the entire application whenever the source dataset changes.

It also improves traceability because the original source fields can be retained while standardised fields are created for analysis.

---

# 6. Kelvin's Current Prototype

The technology selection should directly support the implementation already developed by Kelvin.

The current prototype is based on a converted **10-match Super Rugby 2026 dataset derived from Sportradar Rugby Union data**.

The dataset is separated into five main CSV files:

| Dataset | Granularity | Purpose |
|---|---|---|
| `match_metadata.csv` | One row per match | Match information, teams, venue and score |
| `combined_match_events.csv` | One row per event | Event-level analysis and locations |
| `team_statistics.csv` | One row per team per match | Team-level performance |
| `player_statistics.csv` | One row per player per match | Player-level analysis |
| `period_scores.csv` | One row per period | Score progression |

This structure is useful because different types of analysis require different levels of data.

For example:

```text
Match Metadata
      |
      +---- Match Overview

Team Statistics
      |
      +---- Team Performance
      |
      +---- Attacking Analysis
      |
      +---- Defensive Analysis

Player Statistics
      |
      +---- Player Analysis

Match Events
      |
      +---- Kicking Analysis
      |
      +---- Turnover Analysis
      |
      +---- Event Locations
      |
      +---- Scoring Analysis
```

This structure should be preserved when integrating additional partner data.

---

# 7. Streamlit

## Purpose

Streamlit provides the user-facing interface for the current prototype.

Kelvin's implementation allows users to:

- select a match;
- view match information;
- select an analysis type;
- view tables;
- view interactive charts;
- inspect event locations; and
- upload compatible event CSV data.

The current analysis options include:

- Match Overview;
- Team Performance;
- Attacking Analysis;
- Defensive Analysis;
- Set Piece Analysis;
- Kicking Analysis;
- Turnover Analysis;
- Discipline Analysis;
- Event Locations;
- Scoring Analysis; and
- Player Analysis.

## Justification

Streamlit is appropriate because the project is primarily a data-analysis application rather than a general-purpose consumer website.

It allows the team to connect Python processing directly to an interactive browser interface without requiring a separate frontend framework.

This reduces development complexity and allows the team to focus on the rugby analysis itself.

Streamlit also supports widgets, tables, charts and caching mechanisms that can help reduce repeated data loading and calculations.

**Decision:** Streamlit is **recommended and already implemented**.

**Sources:**

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Streamlit App Model](https://docs.streamlit.io/get-started/fundamentals/summary)

---

# 8. Plotly

## Purpose

Plotly is used for interactive data visualisation within the Streamlit application.

Kelvin's `charts.py` currently supports:

- team comparison charts;
- single-metric comparisons;
- event comparison charts;
- player leaderboards;
- scoring timelines; and
- Rugby Union pitch visualisation for event locations.

## Justification

Visualisation is important for opposition analysis because analysts need to identify patterns rather than only read numerical tables.

The existing Tableau workbook already demonstrates this requirement through event-count, field-location and team-comparison views.

Plotly allows similar information to be displayed interactively within the application.

For example:

```text
Processed Rugby Data
        |
        v
     Pandas
        |
        v
   Analysis Result
        |
        v
      Plotly
        |
        v
Interactive Chart
```

The pitch visualisation is particularly relevant because the partner dataset contains event coordinates.

The current implementation also avoids making unsupported assumptions about attacking direction or player movement when these are not explicitly provided by the source data.

**Decision:** Plotly is **recommended and already implemented**.

**Source:** [Plotly Python Documentation](https://plotly.com/python/)

---

# 9. Tableau

## Current Role

Tableau should be treated as the **existing/reference analysis workflow**, rather than a technology that the project must immediately replace.

The supplied Tableau workbook demonstrates several useful analysis patterns:

```text
Event Count by Action
        |
        +---- How often does an event occur?

Event Locations on Field
        |
        +---- Where do recorded events occur?

Team Event Comparison
        |
        +---- How do teams differ?
```

These views provide a useful benchmark for the automated system.

## Technology Decision

The project should aim to reproduce selected useful analysis functions through Python rather than replacing Tableau purely for technological reasons.

The comparison can be represented as:

| Current Workflow | Proposed Prototype |
|---|---|
| Source event data | Source event data |
| Manual preparation | Python validation and normalisation |
| Tableau worksheets | Pandas analysis functions |
| Tableau dashboard | Streamlit interface |
| Tableau visualisations | Plotly visualisations |
| Manual analysis | Repeatable calculations |
| Repeated processing | Future processing-state tracking |

The purpose is therefore to **automate and accelerate repetitive analysis**, while retaining the existing Tableau workflow as a useful reference and validation point.

**Source:** [Tableau Dashboard Documentation](https://help.tableau.com/current/pro/desktop/en-us/dashboards.htm)

---

# 10. Analysis Layer and Kelvin's Code

The technology architecture must directly support Kelvin's existing implementation.

## 10.1 `app.py`

The application layer is responsible for:

- application flow;
- data-source selection;
- match selection;
- analysis selection;
- displaying match information; and
- presenting analysis outputs.

## 10.2 `analysis.py`

The analysis layer is responsible for:

- CSV loading;
- validation;
- missing-column handling;
- numeric conversion;
- match filtering;
- team statistics;
- player statistics;
- event counting;
- kicking analysis;
- turnover analysis;
- discipline analysis;
- scoring analysis;
- event-location filtering; and
- rule-based factual observations.

## 10.3 `charts.py`

The visualisation layer is responsible for:

- team comparison charts;
- metric comparison charts;
- event comparison charts;
- player leaderboards;
- scoring timelines; and
- rugby-pitch event visualisation.

The separation of these responsibilities is beneficial because changes to the interface do not necessarily require changes to the analysis logic.

---

# 11. Current Calculated Metrics

Kelvin's implementation currently calculates a limited set of derived metrics.

For example:

### Metres per Carry

```text
Metres per carry =
metres_run / carries
```

### Tackle Success Rate

```text
Tackle success rate =
tackles / (tackles + tackle_missed) × 100
```

### Scrum Success Rate

```text
Scrum success rate =
scrums_won / total_scrums × 100
```

These calculations should remain clearly distinguished from source-provided statistics.

The system should identify whether a value is:

- directly provided by the source; or
- calculated by the application.

This improves transparency and makes the output easier for analysts to validate.

---

# 12. Data Integrity and Analytical Safety

Rugby event data contains domain-specific terminology and contextual information. Therefore, the system should avoid automatically converting every event into a tactical interpretation.

The current implementation follows several useful principles:

1. Source event terminology is retained.
2. Events without a recorded team are not counted as team events.
3. Missing coordinates are excluded from spatial plots but not automatically removed from other event counts.
4. Missing scorer names are displayed as unavailable rather than invented.
5. `ball_kicked` and `kick_to_touch` remain separate source concepts.
6. Turnover follow-up analysis considers the next recorded timeline event rather than reconstructing an entire possession.
7. `penalty_awarded` locations are not automatically treated as identical to `penalties_conceded`.

These principles are important because the system should produce **traceable evidence-based analysis rather than unsupported tactical claims**.

---

# 13. SQLite

## Purpose

SQLite is a potential future technology for tracking processing state.

It should not be considered a required component of Kelvin's current prototype because the current implementation reads CSV data directly.

If introduced later, SQLite could store:

- match identifiers;
- source file information;
- processing status;
- processing timestamps;
- data-version information;
- generated analysis summaries; and
- cached results.

For example:

```text
New Match / Data File
          |
          v
   Check Processing DB
          |
      +---+---+
      |       |
   Exists    New
      |       |
     Skip    Process
              |
              v
        Save Status
```

This could address a problem identified in the project where historical matches may be repeatedly processed even when only a new match has been added.

SQLite is suitable for an initial prototype because it is serverless and does not require a separate database server.

However, it should be introduced only after the event-processing workflow is stable.

**Decision:** SQLite is **recommended as a future processing-state component**, not as a dependency of the current prototype.

**Source:** [SQLite Serverless Architecture](https://www.sqlite.org/serverless.html)

---


# 14. Proposed End-to-End Technology Architecture

The recommended architecture is:

```text
                  ┌───────────────────────────┐
                  │ Partner / Source Data     │
                  │                           │
                  │ Event-level rugby records │
                  └─────────────┬─────────────┘
                                |
                                v
                  ┌───────────────────────────┐
                  │ Data Ingestion             │
                  │                           │
                  │ CSV / compatible source   │
                  └─────────────┬─────────────┘
                                |
                                v
                  ┌───────────────────────────┐
                  │ Validation + Normalisation│
                  │                           │
                  │ Source → Canonical schema │
                  └─────────────┬─────────────┘
                                |
                                v
                  ┌───────────────────────────┐
                  │ Pandas DataFrames          │
                  │                           │
                  │ Events / Metadata / Stats │
                  └─────────────┬─────────────┘
                                |
                    ┌───────────┴───────────┐
                    |                       |
                    v                       v
          ┌──────────────────┐    ┌──────────────────┐
          │ Analysis Layer   │    │ Future SQLite   │
          │                  │    │ Processing State│
          │ Kelvin functions │    │                  │
          └────────┬─────────┘    └──────────────────┘
                   |
                   v
          ┌──────────────────┐
          │ Streamlit        │
          │ User Interface   │
          └────────┬─────────┘
                   |
                   v
          ┌──────────────────┐
          │ Plotly           │
          │ Interactive Views│
          └──────────────────┘
```

Tableau can remain alongside this architecture as the current/reference workflow and validation benchmark.

---

# 15. Technology Selection Summary

| Technology | Role | Status | Justification |
|---|---|---|---|
| Python | Core processing language | **Implemented** | Matches Kelvin's prototype and supports the data pipeline |
| Pandas | Data processing | **Implemented** | Suitable for event-level tabular data |
| CSV | Data interchange | **Implemented** | Simple and compatible with the current datasets |
| Streamlit | Prototype interface | **Implemented** | Provides a direct Python-to-browser application |
| Plotly | Interactive visualisation | **Implemented** | Supports team comparisons, timelines and event locations |
| Tableau | Existing/reference analysis | **Existing** | Represents the current analysis workflow and benchmark |
| Normalisation layer | Source compatibility | **Required** | Connects partner data to Kelvin's analysis schema |
| SQLite | Processing-state tracking | **Future** | Can prevent unnecessary reprocessing |
| React + FastAPI | Larger web architecture | **Future option** | Useful only if future scalability requires it |

---

# 16. Final Technology Justification

The recommended technology stack is intentionally conservative and evidence-based.

**Python, Pandas, Streamlit and Plotly should form the current prototype stack** because these technologies are already demonstrated in Kelvin's working implementation. This reduces technical risk and allows the team to focus on the project's main objective: accelerating opposition analysis rather than spending unnecessary development time building a completely new software stack.

The partner Tableau dataset also supports this direction. It is an event-level dataset containing player, team, time, location, action, result and match-context information. These characteristics are compatible with Pandas-based DataFrame processing and Plotly-based visualisation.

The most important integration requirement is therefore not replacing Kelvin's code, but creating a **data-normalisation layer** between the partner source schema and Kelvin's canonical event schema.

This allows the original source fields to remain traceable while enabling the existing analysis functions to operate on consistent field names.

The technology architecture can consequently support a progression from:

```text
Manual / Tableau-supported Analysis
              |
              v
Python Data Ingestion
              |
              v
Validation and Normalisation
              |
              v
Automated Pandas Analysis
              |
              v
Interactive Streamlit + Plotly Output
              |
              v
Future Processing-State Database
              |
              v
More Automated Opposition Analysis
```

This approach also supports the work of other team members. Research and workflow analysis can define what information analysts need; the data work can define the source and canonical fields; Kelvin's implementation provides the working processing and visualisation prototype; and the technology architecture connects these components into one coherent system.

The project should therefore prioritise **data compatibility, traceability, reproducibility and reduction of manual work** before introducing more complex technologies such as React/FastAPI or a production database.

---

# 17. Key References

1. Python Software Foundation. [Python CSV Documentation](https://docs.python.org/3/library/csv.html)
2. Pandas Development Team. [Pandas Documentation](https://pandas.pydata.org/docs/getting_started/)
3. Streamlit. [Streamlit Documentation](https://docs.streamlit.io/)
4. Streamlit. [App Model Summary](https://docs.streamlit.io/get-started/fundamentals/summary)
5. Plotly. [Plotly Python Documentation](https://plotly.com/python/)
6. SQLite. [SQLite Serverless Architecture](https://www.sqlite.org/serverless.html)
7. Tableau. [Tableau Dashboard Documentation](https://help.tableau.com/current/pro/desktop/en-us/dashboards.htm)
