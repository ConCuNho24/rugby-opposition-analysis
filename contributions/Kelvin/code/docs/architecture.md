# Architecture and process-once design

## Architectural hypothesis

The proof-of-concept tests this proposition:

> An external rugby data source can be mapped into one internal event model,
> processed once per changed match, reused by several descriptive analyses, and
> turned into an analyst-review opposition preview.

```text
Pinned public source JSON                 Future partner CSV(s)
          |                                         |
          v                                         v
 RugbyDataJsonAdapter                     PartnerAdapter (not yet implemented)
          |                                         |
          +------------------+----------------------+
                             v
                    CanonicalEvent contract
                             |
                             v
          Incremental per-match canonical CSV store
                             |
                             v
       Combined canonical_events.csv (no raw read downstream)
             |                  |                   |
             v                  v                   v
        descriptive metrics   rule insights      HTML / Streamlit preview
```

## Components

| Component | Responsibility | Must not do |
| --- | --- | --- |
| `scripts/download_data.py` | Acquire a pinned public source, retain provenance and split source records into one raw match file each. | Change source semantics or quietly substitute a moving branch. |
| `adapters/rugby_data.py` | Convert source score, line-up, card and substitution records into `CanonicalEvent`. | Leak raw JSON fields into downstream modules or fabricate unsupported events. |
| `core/schema.py` | Define and validate the source-independent record contract. | Require fields the source lacks. |
| `core/pipeline.py` | Discover matches, calculate content hashes, process only changed raw matches, persist per-match canonical CSVs, rebuild the combined store. | Run separate raw-file extraction passes for every analysis. |
| `core/manifest.py` | Persist `raw file -> hash -> processed match` evidence. | Treat a changed source file as current. |
| `analysis/` | Read the combined canonical store and calculate only data-supported metrics. | Know dataset-specific headers or reread raw JSON. |
| `insights/` | Turn thresholded descriptive comparisons into structured candidate observations. | Make coaching recommendations or causal claims. |
| `reporting/` and `app/` | Present evidence, sample size, caveats and generated charts/report paths. | Bypass canonical data. |

## Incremental processing lifecycle

1. The downloader creates a separate raw JSON file for each selected source
   fixture.
2. `IncrementalPipeline` discovers these files and calculates a SHA-256 content
   hash for each one.
3. It consults `data/state/processing_manifest.json`.
4. A matching hash with an existing per-match canonical CSV is skipped.
5. A new, changed or forced source match is normalised **once** by its adapter
   and written to `data/processed/matches/<match_id>.csv`.
6. The combined `data/processed/canonical_events.csv` store is rebuilt from the
   canonical per-match files.
7. All analysis, chart, insight and report work reads the combined canonical
   store. It does not revisit the source raw match JSON.

The hash pass is an integrity/cache check. The meaningful source-event parsing
and normalisation pass occurs once per changed match rather than once per
analysis module.

## Why per-match canonical files

A source season file is convenient to download but not sufficient to prove
incremental behaviour. Splitting it into match records gives the manifest a
clear unit of work:

```text
First run:    each source match -> canonical match file
Second run:   same hashes       -> matches skipped, 0 re-normalised
New match:    one new hash      -> existing matches skipped; new match normalised
--force:      all files         -> all re-normalised deliberately
```

Actual timing and counts are recorded in
[performance_demo.md](performance_demo.md), not in a static pre-run claim.

## Source isolation and second-adapter proof

`ReformattedPublicSampleAdapter` reads
`data/synthetic/reformatted_public_sample.csv`, a three-row, deliberately
reformatted fixture. It proves that differently named source fields can produce
the same `CanonicalEvent` representation and reuse generic analysis code.

It is explicitly **SYNTHETIC -- FOR ARCHITECTURE TESTING ONLY**:

- it is not a second data provider;
- it is never acquired, profiled or combined with real Rugby-Data outputs; and
- it must never appear in a real opposition report.

The future `PartnerAdapterPlaceholder` deliberately raises `NotImplementedError`.
That is a safeguard: it prevents invented Opta/partner mappings before the
partner actually supplies headers, qualifier semantics, identifiers and
coordinate conventions.

## Data-flow guardrails

- Canonical optional fields remain null where the source lacks them.
- Source-specific values live in `metadata` and are documented by the adapter.
- Deterministic rules can surface a candidate pattern, but the report calls for
  analyst/video review rather than a coaching action.
- Report titles and caveats identify this source as public Rugby-Data, not
  Queensland Reds/Opta data.

