# 🏉 Rugby Opposition Analysis

### QUT IT Capstone — P631
**Accelerating Opposition Analysis in Professional Rugby**

This repository supports our QUT Capstone project investigating how the opposition analysis workflow in professional rugby can be improved through data processing, analysis, automation and reporting.

The project is undertaken in collaboration with the **Queensland Reds High Performance Program**.

---

## 🎯 Project Overview

Opposition analysis is an important part of preparing for upcoming matches. Analysts review previous matches, identify patterns and extract information that can support coaches and players in their preparation.

Our project explores opportunities to reduce repetitive manual work and improve this workflow through areas such as:

- data collection and preparation;
- structured match-event processing;
- opposition performance analysis;
- automated insight generation;
- data visualisation;
- automated reporting; and
- prototype tools that support opposition analysis.

The project is currently under active development as part of the QUT IT Capstone program.

---

## 📁 Repository Structure

```text
rugby-opposition-analysis/
│
├── contributions/
│   └── <team-member>/
│       ├── code/
│       ├── weekly/
│       ├── reports/
│       └── notes/
│
├── source-code/
├── meetings/
├── reports/
├── research/
├── deliverables/
│
├── .gitignore
└── README.md
```

### `contributions/`

Contains individual work completed by each team member throughout the project.

Each team member has their own workspace:

```text
contributions/<team-member>/
├── code/       # Individual implementation and prototypes
├── weekly/     # Weekly contribution records
├── reports/    # Individual reports or analysis outputs
└── notes/      # Research notes and working documents
```

These folders help document individual development work and provide evidence of each member's contribution throughout the Capstone project.

---

### `source-code/`

Contains the **shared team implementation**.

Individual ideas and prototypes may initially be developed inside a team member's contribution folder. Work that is reviewed and agreed upon by the team can later be integrated into this shared source-code area.

---

### `meetings/`

Contains meeting notes, decisions and action items from:

- team meetings;
- tutor meetings; and
- industry partner meetings.

---

### `reports/`

Contains shared reports and project documentation prepared by the team.

---

### `research/`

Contains research, references, technical investigation and project discovery work.

---

### `deliverables/`

Contains final or submitted project deliverables produced throughout the Capstone project.

---

## 👥 Team Collaboration

The repository is structured to support both **individual contribution tracking** and **shared team development**.

Each team member can work independently inside their own contribution folder while still keeping the official team implementation separate.

Contribution history can also be reviewed through:

- Git commits;
- branches;
- pull requests;
- code reviews; and
- weekly contribution records.

---

## 🔄 Development Approach

The team follows a simple development flow:

```text
Individual Development
        ↓
contributions/<team-member>/
        ↓
Team Discussion / Review
        ↓
source-code/
        ↓
Shared Team Implementation
```

This structure allows team members to experiment and develop ideas independently while keeping the agreed team implementation clear and organised.

---

## 🧪 Testing

Individual implementations may include automated tests where appropriate.

The shared team implementation should be tested before changes are integrated into the main project codebase.

For Python-based components, tests may be run using:

```bash
python -m pytest
```

Testing requirements will continue to evolve as the project develops.

---

## 📊 Project Workflow

The project may investigate a workflow similar to:

```text
Match Data
    ↓
Data Ingestion
    ↓
Event Normalisation
    ↓
Structured Match Events
    ↓
Performance Analysis
    ↓
Insight Generation
    ↓
Opposition Report / Visualisation
```

This workflow is expected to evolve as the team receives feedback from tutors and the industry partner.

---

## 🔐 Data & Confidentiality

This repository may be used for project collaboration and assessment purposes.

To protect project and partner information:

- sensitive industry-partner data should not be committed;
- credentials, API keys and environment files should not be committed;
- large downloaded or generated datasets should be excluded where appropriate;
- local environments and temporary files should be excluded from version control; and
- only data suitable for public use should be included in the repository.

Relevant files and directories should be excluded through `.gitignore`.

---

## 🎓 Project Context

| Item | Details |
|---|---|
| University | Queensland University of Technology (QUT) |
| Unit | IT Capstone |
| Project | P631 — Accelerating Opposition Analysis in Professional Rugby |
| Industry Partner | Queensland Reds High Performance Program |
| Project Area | Sports Analytics / Data Processing / Automation |

---

## 🚧 Project Status

This repository is a **work in progress**.

The project structure, requirements, analysis methods and technical implementation will continue to evolve as the team receives feedback from tutors and the industry partner.

---

## 📌 Notes

The contents of individual contribution folders represent work completed by individual team members and may include experimental or exploratory implementations.

The contents of `source-code/` will represent work that has been reviewed and adopted as part of the shared team solution.
