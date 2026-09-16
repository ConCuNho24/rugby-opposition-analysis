# Incremental-processing performance demonstration

## Purpose

The performance evidence is about the mechanism, not a benchmark contest. This
small public source is unlikely to show dramatic elapsed-time savings. The useful
demonstration is that a canonical match file is created once, source content is
hashed, and unchanged sources are skipped rather than sent through the adapter
again.

## Observed real-data run

The following figures are **observed from the completed local real-data run**,
not estimates:

| Item | Observed result |
| --- | ---: |
| Pinned source match records downloaded | 93 |
| Canonical events in the combined store | 4,848 |
| Populated source-match timelines observed by the run | 92 |
| Verification forced normalisation elapsed time | 2.431 seconds |
| Immediately following unchanged rerun | 0 processed, 93 skipped, 0.303 seconds |

The difference between raw source-record count and populated timelines should be
kept visible during data-quality review. It must not be reframed as 93 distinct
team/opponent analytical samples without checking source identity and the
adapter's deterministic-match-ID rule.

## Reproduce the incremental behaviour

Run these commands from the project root in PowerShell after completing
[Data acquisition and profiling](data_setup.md).

```powershell
# Rebuild every currently discovered source record and capture the actual output.
python scripts/run_pipeline.py --force 2>&1 | Tee-Object -FilePath outputs\force_run.log

# Run unchanged input again. The summary should show zero processed matches
# and the discovered matches as skipped.
python scripts/run_pipeline.py 2>&1 | Tee-Object -FilePath outputs\incremental_rerun.log
```

The second command is the important proof: it must use the existing manifest
and per-match canonical files. It must not reinterpret the source data or claim
a performance result until its own printed elapsed time is captured.

For a later genuine source fixture, add the new source-schema JSON file to:

```text
data\raw\rugby_data_premiership_2024_2025\matches\
```

Then run:

```powershell
python scripts/run_pipeline.py 2>&1 | Tee-Object -FilePath outputs\new_match_run.log
```

Expected mechanism:

```text
existing unchanged files -> skipped
new/changed file          -> normalised once
combined canonical store  -> rebuilt from canonical per-match files
```

Do not copy or hand-edit a fixture merely to create a “new match” demo: that
would turn the evidence into synthetic data. Use a genuine later source record
or demonstrate this case through the automated incremental test fixture.

## Force rebuild

Use the explicit force option when intentionally discarding incremental reuse:

```powershell
python scripts/run_pipeline.py --force
```

A force rebuild is useful after changing adapter mapping semantics or recovering
from corrupted processed output. It is not the normal weekly workflow.

## Interpretation

- Runtime includes source discovery, content hashing, canonical CSV writing and
  rebuilding the combined store.
- A hash calculation is a lightweight cache/integrity read. Only new/changed
  matches enter the source-event normalisation pass.
- Timing varies with machine, Python environment, disk and antivirus activity.
  Report a run's printed elapsed time rather than comparing it directly with
  another computer.
- The report and analysis modules read `canonical_events.csv`, not raw match
  files; this is the central reduction in repeated extraction work.
