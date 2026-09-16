# PROJECT: Rugby Opposition Preview Automation

## 1. Python

### Purpose
- Use Python as the main programming language for the data-processing pipeline.
- Process rugby event CSV files and perform data extraction, cleaning and analysis.
- Connect different parts of the system, such as CSV processing, analysis, database storage and potentially the user interface.
- Help automate tasks that are currently performed manually.

### Evidence
- The industry partner's existing workflow already uses Python notebooks/scripts for processing rugby data and performing analysis.
- The partner discussed the possibility of combining or improving the existing extraction and analysis scripts.
- The project involves processing rugby event data stored in CSV files, making Python a relevant language for the proposed automation pipeline.

### Potential Benefits
- **Easy integration:** The team can build on technologies already used by the industry partner rather than introducing a completely different programming language.
- **Suitable for data processing:** Python has a large ecosystem for CSV processing, data analysis, databases and web applications.
- **Reusable code:** Existing Python analysis logic may be reusable or adaptable instead of being rebuilt from scratch.
- **Simple development:** Python can help the team develop and test the prototype efficiently.

### Consideration
The team should first understand the existing Python notebooks and determine which parts can be reused, improved or converted into a more automated pipeline.

### Source
[Python Documentation - CSV Module](https://docs.python.org/3/library/csv.html)

---

## 2. Pandas

### Purpose
- Use Pandas for data cleaning, filtering and analysis.
- Convert rugby event data into structured `DataFrame` objects.
- Filter events based on event type, player, timestamp, location or other relevant fields.
- Perform grouping and aggregation to produce useful statistics.
- Prepare data for further analysis or visualisation.

### Evidence
The rugby data supplied by the industry partner consists of CSV files where each row represents an event. The data can contain information such as event ID/type, player, timestamp, location and event-specific information. A game can contain approximately 5,000 events.

This type of structured, tabular data is suitable for a DataFrame-based approach.

### Potential Benefits
- **DataFrame support:** Pandas provides a `DataFrame` structure designed for tabular data.
- **Easy filtering:** The team can select specific event types or players without manually processing every row.
- **Grouping and aggregation:** Useful for calculating statistics such as the number of kicks, tackles, line breaks or other events.
- **CSV support:** Pandas can directly read and write CSV files.
- **Useful for analysis:** Pandas provides functions for cleaning, transforming and summarising data.

### Example Use

```
Rugby CSV
    ↓
Pandas DataFrame
    ↓
Filter relevant events
    ↓
Group / calculate statistics
    ↓
Analysis results
```

For example:

```
All events
    ↓
event_type = "Kick"
    ↓
Kicking events
    ↓
Calculate statistics
```

### Consideration
Pandas is an additional Python package, so it needs to be installed and managed as a project dependency. The team should also test its memory and processing performance with the larger datasets supplied by the partner.

### Source
[Pandas Documentation - Getting Started](https://pandas.pydata.org/docs/getting_started/)

---

## 3. SQLite

### Purpose
- Store information about games that have already been processed.
- Keep metadata about each rugby game.
- Store processing status and potentially extracted analysis results.
- Help the system identify new games that still need to be processed.

### Evidence
One issue identified by the industry partner is that the current workflow can repeatedly process old games.

For example:

```
Round 9:
Process Games 1-8

Round 10:
Process Games 1-9
```

This means previously processed games may be processed again instead of only processing the newly added game. The partner discussed investigating whether the system could identify missing/new games and avoid unnecessary reprocessing.

### Potential Benefits
- **Avoid repeated processing:** The system can record which games have already been processed.
- **Simple deployment:** SQLite does not require a separate database server.
- **Single database file:** The database can be stored locally as one file.
- **Low configuration:** SQLite is serverless and does not require a separate database service.
- **Suitable for a prototype:** If the application is initially used locally or by a small number of users, SQLite could provide a simple way to manage processing information.

### Possible Database Structure

```
Games
--------------------------------
game_id
game_date
team
opponent
competition
processed
processed_date
```

Possible workflow:

```
New CSV files
      ↓
Check SQLite
      ↓
Already processed?
   ↙          ↘
 YES           NO
  ↓             ↓
Skip        Process game
                ↓
          Save status
                ↓
             SQLite
```

### Risk / Consideration
- The team needs to design an appropriate database structure.
- The actual dataset size and expected number of users should be tested.
- SQLite may not be the best choice if the final system requires many simultaneous users or a central multi-user database.
- SQLite should therefore initially be treated as a potential solution that needs to be tested with real project data.

### Sources
[SQLite Documentation](https://www.sqlite.org/docs.html)

[SQLite - Serverless Architecture](https://www.sqlite.org/serverless.html)

---

## 4. Streamlit

### Purpose
- Provide a simple user interface for the rugby preview automation system.
- Allow users to select teams, games or analysis types.
- Allow users to start the processing pipeline.
- Display generated statistics and analysis results.
- Potentially display tables, charts and filtering options.

### Proposed Interface

```
Rugby Opposition Preview

Team:
[ Select Team ▼ ]

Opponent:
[ Select Opponent ▼ ]

Games:
[ Last 4 Games ▼ ]

Analysis:
☑ Kicking
☑ Tackling
☑ Line Breaks
☑ Breakdown

[ Generate Preview ]

Processing...
✓ Data loaded
✓ Events processed
✓ Analysis completed

[ View Results ]
```

### Potential Benefits
- **Python-based:** Streamlit works with Python, allowing the team to connect the interface directly to the Python processing pipeline.
- **Fast prototyping:** A functional interface can be developed without building a separate frontend application.
- **Interactive widgets:** Streamlit supports buttons, dropdowns, filters and other interactive components.
- **Tables and charts:** Useful for displaying rugby statistics and analysis results.
- **Caching:** Streamlit provides caching mechanisms that can help avoid repeatedly performing expensive calculations or loading the same data.
- **Suitable for a data-focused application:** Streamlit is designed for interactive data applications.

### Example Architecture

```
                 Streamlit UI
                      ↓
              Python Processing
                      ↓
             Pandas / Analysis
                ↙         ↘
             SQLite       CSV
```

### Risk / Consideration
Streamlit has a particular execution model where the Python script can rerun when users interact with widgets. For expensive analysis, the team would need to use caching and structure the application carefully.

It also provides less frontend flexibility than a dedicated frontend framework such as React.

### Sources
[Streamlit Documentation](https://docs.streamlit.io/)

[Streamlit - Basic Concepts](https://docs.streamlit.io/get-started/fundamentals/main-concepts)

---

## 5. Alternative: React + FastAPI

### Purpose
An alternative approach would be to build a more traditional full web application.

```
React
Frontend / UI
     ↓
FastAPI
Backend / API
     ↓
Python Processing
     ↓
Pandas + SQLite
```

### React
React could be used to create the frontend interface.

Potential features:
- Team selection
- Game selection
- Interactive tables
- Charts
- Filtering
- Navigation between different analysis sections
- More customised user interface

React uses reusable components to build user interfaces, allowing a larger application to be divided into smaller UI components.

### FastAPI
FastAPI could provide the backend API between the frontend and Python processing system.

Example:

```
React
   ↓
GET /games
   ↓
FastAPI
   ↓
Python
   ↓
SQLite
```

FastAPI is a Python web framework designed for building APIs.

### Advantages
- **More flexible frontend:** React provides greater control over the design and behaviour of the user interface.
- **Clear separation:** Frontend, backend and data-processing components can be separated.
- **Scalable architecture:** This approach provides a stronger foundation if the system eventually becomes a larger web application.
- **API-based design:** Other applications could potentially communicate with the processing system through the API.

### Disadvantages
- **Higher complexity:** The team would need to work with React, JavaScript/TypeScript, FastAPI and Python.
- **More development effort:** More components need to be designed, connected and maintained.
- **More technologies to learn:** This could increase the learning curve for a student team.
- **Potentially unnecessary for the first prototype:** If the main goal is to demonstrate automated rugby data processing, a simpler Python + Streamlit solution may require less development overhead.

### Sources
[React Documentation](https://react.dev/)

[FastAPI Documentation](https://fastapi.tiangolo.com/)

---

# Overall Proposed Technology Structure

One possible architecture to investigate is:

```
                 ┌──────────────────┐
                 │    Streamlit     │
                 │   User Interface │
                 └────────┬─────────┘
                          │
                          ↓
                 ┌──────────────────┐
                 │      Python      │
                 │ Processing Logic │
                 └────────┬─────────┘
                          │
                ┌─────────┴─────────┐
                ↓                   ↓
        ┌──────────────┐    ┌──────────────┐
        │    Pandas    │    │    SQLite    │
        │ Data Analysis│    │ Game Tracking│
        └──────┬───────┘    └──────────────┘
               │
               ↓
        ┌──────────────┐
        │ Rugby CSV    │
        │ Event Files  │
        └──────────────┘
```

## Preliminary Justification

**Python** could be used as the core processing language because it aligns with the existing industry workflow. **Pandas** could be investigated for cleaning, filtering and aggregating rugby event data. **SQLite** could be investigated for tracking which games have already been processed, helping reduce unnecessary reprocessing. **Streamlit** could provide a simple interface for running the analysis and displaying results. **React + FastAPI** could remain an alternative if the project later requires a more complex web application.

This is a proposed technology direction for investigation rather than a confirmed technology stack from the industry partner. The exact choices should be tested against the real project data and requirements.

---

# Main Sources

1. [Python Documentation](https://docs.python.org/3/library/csv.html)
2. [Pandas Documentation](https://pandas.pydata.org/docs/getting_started/)
3. [SQLite Documentation](https://www.sqlite.org/docs.html)
4. [SQLite Serverless Architecture](https://www.sqlite.org/serverless.html)
5. [Streamlit Documentation](https://docs.streamlit.io/)
6. [React Documentation](https://react.dev/)
7. [FastAPI Documentation](https://fastapi.tiangolo.com/)
