# Public dataset research and selection

## Decision

This proof-of-concept uses the **Rugby-Data Premiership 2024--25 JSON** from
[transientlunatic/Rugby-Data](https://github.com/transientlunatic/Rugby-Data),
pinned by the acquisition script to commit
`90923144567e1613a3d941ba72a54a10a3866194`.

The repository describes its data as scoring information from professional
**rugby union** competitions in JSON and YAML. For this PoC, the pinned
`premiership-2024-2025.json` collection was inspected and contains 93 fixture
records. The downloader preserves the original season file, then splits it into
one raw JSON record per match so that the common pipeline can process and cache
matches independently.

> This dataset is being used to validate the architecture and processing
> workflow. It is not assumed to match the Queensland Reds partner data.

The selection favours real fixture/team/player-linked scoring and line-up
timelines over a richer-looking source that could not support reliable
opposition-level aggregation. It is deliberately **not** described as a
complete Opta-style event feed.

## Candidate comparison

| Candidate | Rugby code and provenance | Real data / scale inspected | Format and fields | Licence / usage position | Suitability for this PoC |
| --- | --- | --- | --- | --- | --- |
| **Rugby-Data -- selected** | Rugby Union; [Rugby-Data repository](https://github.com/transientlunatic/Rugby-Data) describes professional Rugby Union scoring data. | Real professional fixtures; 93 matches in the pinned Premiership 2024--25 file. | JSON fixture records. `home`/`away` teams, final scores, scoring entries (`minute`, `type`, `player`, `value`) and line-up/card/substitution information. | **No explicit repository licence was found during inspection.** Use is limited here to an attributed, non-production Capstone PoC. Raw source files are ignored by Git. Obtain permission before redistribution, publication of raw data, or commercial use. | Best available fit: team and mostly player attribution, minute, score value and multiple matches support an end-to-end opposition-preview workflow. It lacks full play-by-play, location and possession detail. |
| [CodeProcessor/rugby-events-dataset](https://github.com/CodeProcessor/rugby-events-dataset) | The README calls its competition “Dialog Rugby League”; the precise code and usage context should be verified before use. | Real video annotations; inspection at commit `dd2a21da07a77e049d0fa6be7e3c5eff64440e03` found 38 annotation CSVs and 2,296 rows. | Headerless CSV rows with an event label plus start/end video time. Observed labels include ruck, scrum, lineout and kick. No reliable event-level team, player, outcome, coordinates, fixture date or period fields. | Repository declares MIT for its code/data, but linked video/media have separate third-party rights and are not downloaded or bundled by this project. | Useful candidate for generic event-frequency/sequence architecture, but too weak for credible team-specific opposition reporting because actions cannot be attributed to a side or player. A retained candidate adapter documents the mapping approach; it is not the selected report source. |
| [rorybunker/rugby-sequences](https://github.com/rorybunker/rugby-sequences) | Rugby Union; accompanying research data for a Japan Top League sequence-mining study. | Real event-sequence data: 490 labelled passages of play from one team’s 2018 Japan Top League matches, as stated by the repository. | Delimited, ordered event-code sequences; useful for sequence mining and scoring/conceding labels. It does not identify individual matches, named teams, players, timestamp seconds or coordinates. | No explicit repository licence was found during inspection; seek permission before reuse beyond research evaluation. | Strong academic sequence example, but not suitable for a multi-fixture named-opponent preview because team and match identities are missing. |
| Commercial event-data feeds (for example, Sportradar) | Rugby Union data products rather than an open dataset. | Potentially rich live/event coverage, but access is contract/credential controlled. | Provider-specific APIs and terms; event richness cannot be assumed without a contract. | Commercial licence and credentials required. | Relevant future integration category, but not a reproducibly downloadable public source for a student PoC. |

## Why Rugby-Data was selected

The selected source supports the following **real** analysis inputs:

| Requirement | Evidence in the selected source | How the PoC uses it |
| --- | --- | --- |
| Multiple fixtures for a named team | Home and away team names across a complete season collection | Aggregate a selected team across its source fixtures. |
| Event-like timeline | Score events have a minute and type; line-ups include substitution/card times | Build a scoring, line-up and discipline timeline. |
| Player context | Scoring and line-up records normally name a player | Rank scoring-event contribution and show named-card records where supplied. |
| Outcome/value | Score `value` and score type, including missed attempts | Report attempts, made/missed events and source score values. |
| Reproducible acquisition | Raw GitHub URL pinned to a commit in `scripts/download_data.py` | Re-run the acquisition script and retain a local source manifest with hashes. |

The trade-off is important: this is a **scoring and line-up timeline**, not a
full match-event stream. The code therefore does not fabricate tackles, carries,
line breaks, possession, field zones, kick distance, coordinates, verified
period boundaries or tactical causality.

## Actual source limitations and safeguards

- The match identifier used internally is deterministic and generated from the
  source date plus home/away team names because the selected JSON does not expose
  a stable provider match ID in the inspected record.
- `timestamp_seconds` is calculated from the supplied minute. It is not a
  verified half/period boundary, so the report must call time views “recorded
  minute windows”, not first- and second-half analysis.
- `period`, player IDs, team IDs and all field coordinates remain null unless a
  source genuinely supplies them.
- Some source score events can omit a player. The adapter preserves the event
  and emits a validation warning rather than inventing a name.
- Generated `event_type` values are normalised labels (for example,
  `missed_conversion`); the original source label and numeric score value remain
  in canonical `metadata`.
- Results are descriptive candidate observations for analyst review, not
  coaching instructions or causal conclusions.

## Reproducibility record

The acquisition script writes
`data/raw/rugby_data_premiership_2024_2025/source_manifest.json` locally. It
records the pinned commit, original URL, source hash and a source-file hash for
each split fixture. This file is intentionally ignored with the raw data.

The local data profile (`outputs/data_profile.json`) is the authoritative
machine-readable record of the downloaded file, including discovered matches,
event labels, teams, timestamp range and missing-field availability.

