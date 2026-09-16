"""Interactive front end for the Rugby Union opposition-analysis PoC.

Run from the project root with::

    streamlit run app/streamlit_app.py

The page intentionally exposes only metrics supported by the selected public
source.  It is a demonstration workflow, not a replacement for partner data or
coaching review.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from rugby_analysis.adapters.rugby_data import RugbyDataJsonAdapter  # noqa: E402
from rugby_analysis.analysis.event_frequency import (  # noqa: E402
    available_teams,
    event_counts,
    events_for_team,
    fixture_context,
)
from rugby_analysis.analysis.scoring import (  # noqa: E402
    discipline_events,
    player_scoring_contributions,
    scoring_breakdown,
    team_scoring_summary,
)
from rugby_analysis.core.pipeline import IncrementalPipeline, load_canonical_events  # noqa: E402


RAW_ROOT = PROJECT_ROOT / "data" / "raw" / "rugby_data_premiership_2024_2025" / "matches"
STORE_PATH = PROJECT_ROOT / "data" / "processed" / "canonical_events.csv"


def run_incremental_processing(force: bool = False) -> dict[str, object]:
    """Normalize newly changed source matches and return a display-friendly summary."""
    adapter = RugbyDataJsonAdapter(RAW_ROOT)
    summary = IncrementalPipeline(PROJECT_ROOT, adapter, RAW_ROOT).run(force=force)
    return summary.to_dict()


def load_store():
    """Read canonical data only; this deliberately never reads source JSON."""
    return load_canonical_events(STORE_PATH)


def _fixture_options(events) -> tuple[list[str], dict[str, str]]:
    context = fixture_context(events)
    if context.empty:
        return [], {}
    labels = {
        row.match_id: f"{row.fixture_label} ({row.match_id})"
        for row in context.itertuples(index=False)
    }
    return context["match_id"].tolist(), labels


def _insight_text(candidate: Any) -> str:
    """Render either the documented candidate-insight object or a mapping."""
    if isinstance(candidate, dict):
        return str(
            candidate.get("observation")
            or candidate.get("statement")
            or candidate.get("headline")
            or candidate.get("insight")
            or candidate
        )
    return str(
        getattr(candidate, "observation", None)
        or getattr(candidate, "statement", None)
        or getattr(candidate, "headline", candidate)
    )


def main() -> None:
    st.set_page_config(page_title="Rugby Opposition Analysis", page_icon="🏉", layout="wide")
    st.title("Rugby Opposition Analysis Pipeline")
    st.caption("Public-data proof of concept | Rugby-Data Premiership 2024–25")

    st.warning(
        "This source contains score attempts/results, line-up substitutions and cards. "
        "It does not provide full play-by-play, possession, tackle/carry/ruck counts, field coordinates, "
        "or validated periods. All observations are descriptive candidates for analyst and coach review."
    )

    raw_count = len(list(RAW_ROOT.glob("*.json"))) if RAW_ROOT.exists() else 0
    status_left, status_middle, status_right = st.columns(3)
    status_left.metric("Raw public matches", raw_count)
    status_middle.metric("Canonical store", "ready" if STORE_PATH.exists() else "not built")
    status_right.metric("Source status", "attributed public PoC")

    with st.expander("Data-use and interpretation limits", expanded=False):
        st.markdown(
            "- The raw source is not bundled in this repository; use the documented downloader first.\n"
            "- The source repository had no explicit licence identified during project research. "
            "Use this only as an attributed, non-production Capstone demonstration until permission is clarified.\n"
            "- Event team and player attribution is used only where supplied by the source. Missing fields remain missing.\n"
            "- A point total derived from source score records is not a substitute for independently audited match scoring."
        )

    controls_left, controls_right = st.columns([2, 3])
    with controls_left:
        force = st.checkbox("Reprocess all raw matches", value=False)
    with controls_right:
        if st.button("Process new or changed raw matches", type="primary", disabled=raw_count == 0):
            with st.spinner("Normalizing public match records…"):
                try:
                    summary = run_incremental_processing(force=force)
                except Exception as error:  # Display an actionable UI error without hiding its cause.
                    st.exception(error)
                else:
                    st.success(
                        f"Processed {summary['processed_matches']} match(es); "
                        f"skipped {summary['skipped_matches']}; "
                        f"canonical events: {summary['total_normalized_events']}."
                    )
                    if summary["warnings"]:
                        st.info("Validation notes: " + " | ".join(map(str, summary["warnings"][:5])))

    events = load_store()
    if events.empty:
        st.info(
            "No canonical events are available yet. Download the pinned public dataset, then use the processing "
            "button above. The setup commands are documented in README.md."
        )
        return

    teams = available_teams(events)
    if not teams:
        st.info("The canonical store does not contain a selectable team attribution.")
        return

    team_name = st.selectbox("Opposition team", teams)
    match_ids, fixture_labels = _fixture_options(events)
    selected_match_ids = st.multiselect(
        "Optional fixture filter",
        options=match_ids,
        format_func=lambda match_id: fixture_labels.get(match_id, match_id),
        help="Leave empty to use every available match for the selected team.",
    )
    scoped_events = events_for_team(events, team_name, selected_match_ids or None)
    st.subheader(f"Supported indicators: {team_name}")
    summary = team_scoring_summary(scoped_events, team_name)
    metric_a, metric_b, metric_c, metric_d = st.columns(4)
    metric_a.metric("Matches with event timeline", int(summary["matches_with_event_timeline"]))
    metric_b.metric("Source score-event value", f"{summary['source_score_event_value_total']:.0f}")
    metric_c.metric(
        "Source value / timeline match", f"{summary['source_score_event_value_per_match']:.1f}"
    )
    metric_d.metric("Tries / recorded match", f"{summary['tries_per_match']:.1f}")

    left, right = st.columns(2)
    with left:
        st.markdown("#### Score-event breakdown")
        st.dataframe(scoring_breakdown(scoped_events), width="stretch", hide_index=True)
        st.markdown("#### Event-type frequency")
        st.dataframe(event_counts(scoped_events), width="stretch", hide_index=True)
    with right:
        st.markdown("#### Scoring contributors")
        st.dataframe(player_scoring_contributions(scoped_events, team_name), width="stretch", hide_index=True)
        st.markdown("#### Discipline records")
        cards = discipline_events(scoped_events, team_name)
        if cards.empty:
            st.caption("No card record was supplied for this selection.")
        else:
            st.dataframe(
                cards[["match_id", "timestamp_seconds", "player_name", "event_type"]],
                width="stretch",
                hide_index=True,
            )

    st.subheader("Candidate observations")
    try:
        from rugby_analysis.insights.rules import generate_candidate_insights

        candidates = generate_candidate_insights(events, team_name, match_ids=selected_match_ids or None)
    except ImportError:
        st.caption("Candidate-insight module is not yet available in this checkout.")
    except Exception as error:
        st.caption(f"Candidate insights could not be generated: {error}")
    else:
        if not candidates:
            st.caption("No rule-based candidate observation met its stated sample or threshold conditions.")
        else:
            for candidate in candidates:
                st.write("• " + _insight_text(candidate))

    if st.button("Generate manager-facing HTML preview"):
        try:
            from rugby_analysis.reporting.preview import generate_opposition_preview

            report_path = generate_opposition_preview(
                PROJECT_ROOT, team_name, match_ids=selected_match_ids or None
            )
        except Exception as error:
            st.exception(error)
        else:
            st.success(f"Preview written to: {report_path}")
            st.caption("Open the local HTML file in a browser. It retains the same public-data limitations.")


if __name__ == "__main__":
    main()
