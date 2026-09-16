# Rugby Opposition Analysis Pipeline

A local, source-independent Rugby Union opposition-analysis proof of concept for
**IFB398 IT Capstone Phase 1**: P631 - Queensland Rugby Union / Queensland Reds,
“Accelerating opposition analysis in professional rugby”.

## What this proves

This project does not claim to solve opposition analysis or replace an analyst.
It demonstrates a reusable software architecture that can:

1. acquire a public rugby data source reproducibly;
2. isolate source-specific parsing behind an adapter;
3. normalise a match only once into a common event model;
4. skip unchanged raw matches on later runs;
5. reuse canonical events across descriptive analysis, rule-based candidate
   observations, charts and an HTML preview; and
6. provide a documented path for a future Queensland Reds partner-data adapter.

The underlying hypothesis is:

> Source abstraction -> efficient event processing -> reusable analysis ->
> candidate insight generation -> automated opposition reporting.

## Architecture

```text
Public Rugby-Data JSON                 Future partner CSV
          |                                      |
          v                                      v
 RugbyDataJsonAdapter                  PartnerAdapter (future)
          |                                      |
          +-------------- CanonicalEvent --------+
                              |
                              v
        per-match canonical CSVs + hash manifest
                              |
                              v
                 canonical_events.csv store
                   |        |        |
                   v        v        v
              analyses  insights  charts / HTML / Streamlit
```

The adapter is the only layer that knows public-source fields. Everything
downstream reads the canonical store, not raw JSON. See
[architecture documentation](docs/architecture.md).

## Public data selection

The selected real source is the public
[Rugby-Data repository](https://github.com/transientlunatic/Rugby-Data), using
a commit-pinned Premiership 2024-25 JSON collection. It was selected over the
other candidates because it provides multiple real named fixtures plus
team-attributed score events, event minutes, score values, player names where
present, line-up substitutions and cards.

The current selected source supports:

| Supported by the public source | Not supported by the public source |
| --- | --- |
| Fixture, team and published final score context | Full on-ball play-by-play |
| Score-event type, minute, source value and often player | Possession or phase ownership |
| Substitution and card timeline records | Tackles, carries, rucks, line breaks or kick distance |
| Team/player descriptive scoring contribution | Field coordinates or spatial zones |
| Source-minute windows | Verified halves/periods |
| Multi-fixture team aggregation | Provider/player IDs in the inspected JSON |

The raw source is a **scoring/line-up/card timeline**, not an Opta-equivalent
feed. Missing data stay missing; the project does not invent coordinates,
tackles, carries, outcomes, player IDs or tactical claims.

### Data-use boundary

No explicit licence was found in the selected source repository during project
research. It is used here only as an attributed, non-production Capstone PoC.
Raw public source data, generated stores and reports are ignored by Git. Obtain
permission before raw-data redistribution, public release or commercial use.

Read the full comparison and limitations in
[dataset_research.md](docs/dataset_research.md).

## Clean setup on Windows PowerShell

Open PowerShell and run the following from a clean checkout. The commands do not
require a global Python install beyond the Windows `py` launcher.

```powershell
Set-Location 'C:\IFB398\rugby-opposition-analysis'

py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks virtual-environment activation, run this **for the current
PowerShell session only**, then activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Run the end-to-end demo

From the activated virtual environment and project root:

```powershell
# 1. Acquire the pinned public JSON and split it into source-match files.
python scripts/download_data.py

# 2. Inspect the actual downloaded fields and availability before analysis.
python scripts/profile_data.py

# 3. Build/reuse the canonical store. This processes new/changed matches only.
python scripts/run_pipeline.py

# 4. Generate a manager-facing HTML preview for a real selectable team.
python scripts/run_pipeline.py --team "Bath Rugby"

# 5. Start the local UI.
python -m streamlit run app/streamlit_app.py
```

The final command opens a local browser tab. Stop the app with `Ctrl+C` in the
PowerShell window.

### Streamlit workflow

1. Run the downloader once, or use the documented copied raw directory when
   working on a network-restricted machine.
2. Open the Streamlit app.
3. Use **Process new or changed raw matches**. Leave **Reprocess all raw
   matches** unticked for ordinary incremental use.
4. Select an opposition team.
5. Optionally select a subset of its source fixtures. Leaving it empty uses all
   available team-attributed timeline fixtures.
6. Review only the supported score-event, contributor and card indicators.
7. Click **Generate manager-facing HTML preview** and open the reported local
   HTML path.

The UI and report label candidate observations as descriptive prompts for analyst
and video review. They are not tactical recommendations.

## Outputs

| Path | Meaning |
| --- | --- |
| `data/raw/rugby_data_premiership_2024_2025/source_manifest.json` | Local provenance: pinned URL/commit, source hashes and fixture information. |
| `outputs/data_profile.json` | Actual source schema, availability, event types, teams and data-quality notes. |
| `data/processed/matches/*.csv` | One canonical CSV per processed source match. |
| `data/processed/canonical_events.csv` | Combined canonical store used by all downstream modules. |
| `data/state/processing_manifest.json` | File hash cache proving whether a source match needs reprocessing. |
| `outputs/charts/*.png` | Generated source-supported chart images. |
| `outputs/reports/*_opposition_preview.html` | Manager-facing local HTML previews. |

The first acquisition/profile run observed **93 source match records**, **92
fixtures with a populated event timeline**, and **4,848 canonical events**. One
published fixture has a final score but no detailed timeline/line-up records, so
event-based rates do not treat it as an available event-timeline match. Source
score-event values are intentionally kept distinct from published final scores;
the profile records known reconciliation differences.

## Incremental processing demo

A normal pipeline rerun hashes the source files and skips unchanged match files.
Capture the real output from your machine with:

```powershell
python scripts/run_pipeline.py --force 2>&1 | Tee-Object -FilePath outputs\force_run.log
python scripts/run_pipeline.py 2>&1 | Tee-Object -FilePath outputs\incremental_rerun.log
```

The first command deliberately reprocesses the current source. The second should
show zero processed matches when no raw file has changed. Adding a genuine later
source-format match file under
`data\raw\rugby_data_premiership_2024_2025\matches\` should process just that
file on the next non-force run.

The completed verification force run processed all 93 source records in
**2.431 seconds**; the immediately following unchanged rerun skipped all 93 in
**0.303 seconds**. Timing varies by computer; use the run's console summary as
evidence for a specific machine. Details and safeguards are in
[performance_demo.md](docs/performance_demo.md).

## Tests

Run the automated suite from the activated environment:

```powershell
python -m pytest
```

The suite covers canonical-schema validation, selected-source adaptation,
incremental manifest behaviour, supported analytics, rule-based insights,
report generation and the deliberately reformatted second-adapter fixture.

## Second-adapter evidence

`data/synthetic/reformatted_public_sample.csv` is a tiny **SYNTHETIC - FOR
ARCHITECTURE TESTING ONLY** fixture. Its differently named fields are mapped by
`ReformattedPublicSampleAdapter` to the same canonical representation. It is
never mixed into public-data profile, analysis, charts or reports.

This is evidence that a new input format needs an adapter, not a rewrite of the
pipeline.

## Future Queensland Reds integration

When partner files arrive, do **not** point them at the public adapter. Profile
their actual files and implement a header-aware `PartnerAdapter`. The reusable
parts are the canonical schema, incremental pipeline/manifest, storage
convention, analysis interfaces, insight structure, reporting engine and UI
architecture. Mapping rules, validation and new rugby analyses must be driven by
the real partner schema and agreed with analysts.

See [partner_integration.md](docs/partner_integration.md) for the step-by-step
integration and data-governance plan.

## Project map

```text
app/                         Streamlit interface
docs/                        Research, data, architecture and integration notes
scripts/                     Download, profile and incremental-run entry points
src/rugby_analysis/
  adapters/                  Public, synthetic-format and partner placeholder adapters
  core/                      Canonical schema, pipeline and manifest
  analysis/                  Only public-data-supported metrics
  insights/                  Deterministic candidate-observation rules
  reporting/                 Charts and HTML report generator
data/                         Raw (ignored), processed (ignored), state and synthetic fixture
outputs/                      Generated profile, charts and reports (ignored)
tests/                        Automated checks
```

## Important limitations

- Results use public English Premiership source data, not Queensland Reds data.
- This is not a predictive, causal or coaching-decision system.
- The public source does not support spatial, possession, tackle/carry/ruck,
  line-break, kick-distance or verified-half analysis.
- Player attribution and score values are only as complete as the public record.
- Automatic patterns need analyst judgement and footage/context review.
- Source permission/licensing must be clarified before any redistribution or
  production/commercial use.
- No partner data schema is assumed or fabricated.

## Recommended next Capstone steps

1. Obtain an approved, small partner data extract and profile it with analysts.
2. Agree an event/qualifier and coordinate mapping dictionary before writing a
   partner adapter.
3. Validate canonical metrics against known Tableau/notebook outputs.
4. Add partner-supported modules (for example, spatial, tackle, kick or phase
   analysis) only after definitions and data quality are confirmed.
5. Gather analyst feedback on the report layout, thresholds and useful
   candidate-observation wording.
