"""Generate an HTML opposition preview from the canonical event store only."""

from __future__ import annotations

from datetime import UTC, datetime
from os.path import relpath
from pathlib import Path
from typing import Iterable

from jinja2 import BaseLoader, Environment, select_autoescape

from rugby_analysis.analysis.event_frequency import fixture_context
from rugby_analysis.analysis.scoring import discipline_events, player_scoring_contributions, scoring_breakdown
from rugby_analysis.core.pipeline import load_canonical_events
from rugby_analysis.insights.rules import generate_candidate_insights, team_events, team_fixture_ids, team_metrics
from rugby_analysis.reporting.charts import filename_slug, generate_team_charts


REPORT_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Opposition preview - {{ team_name }}</title>
  <style>
    :root { --ink:#132238; --blue:#1565c0; --pale:#eef5fc; --line:#dce3ea; --muted:#5c6875; --amber:#975a00; }
    * { box-sizing:border-box; }
    body { max-width:1160px; margin:0 auto; padding:32px 24px 56px; color:var(--ink); background:#fff; font-family:Arial,Helvetica,sans-serif; line-height:1.45; }
    header { border-bottom:4px solid var(--blue); padding-bottom:18px; margin-bottom:22px; }
    h1 { font-size:2rem; margin:0 0 4px; } h2 { font-size:1.25rem; margin:32px 0 12px; } h3 { font-size:1rem; margin:0 0 8px; }
    .eyebrow { font-size:.78rem; color:var(--blue); font-weight:700; text-transform:uppercase; letter-spacing:.06em; }
    .muted, small { color:var(--muted); } .notice { background:#fff8e8; border-left:4px solid #e4a526; padding:12px 15px; margin:16px 0; }
    .metrics { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:12px; margin:14px 0; }
    .metric { background:var(--pale); border:1px solid #d4e4f3; padding:14px; border-radius:6px; } .metric .value { font-size:1.55rem; font-weight:700; color:var(--blue); }
    .metric .label { font-size:.82rem; color:var(--muted); } .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(310px,1fr)); gap:20px; }
    table { width:100%; border-collapse:collapse; font-size:.9rem; margin:10px 0; } th,td { border-bottom:1px solid var(--line); padding:8px; text-align:left; vertical-align:top; } th { background:#f5f7f9; }
    .insight { border-left:4px solid var(--blue); background:#f7fbff; padding:12px 14px; margin:10px 0; } .insight p { margin:0 0 5px; }
    figure { margin:18px 0 28px; border:1px solid var(--line); padding:12px; } figure img { width:100%; height:auto; display:block; } figcaption { color:var(--muted); font-size:.82rem; margin-top:7px; }
    ul { padding-left:20px; } footer { border-top:1px solid var(--line); margin-top:36px; padding-top:14px; color:var(--muted); font-size:.85rem; }
    @media print { body { padding:12px; } figure { break-inside:avoid; } }
  </style>
</head>
<body>
  <header>
    <div class="eyebrow">Rugby Opposition Analysis Pipeline - public-data proof of concept</div>
    <h1>Opposition preview: {{ team_name }}</h1>
    <div class="muted">Generated {{ generated_at }} | Source: Rugby-Data Premiership 2024-25 public JSON</div>
  </header>

  <div class="notice"><strong>Interpretation boundary.</strong> This report surfaces descriptive candidate observations from a public scoring/line-up timeline. It is not a coaching recommendation and should be reviewed with match footage and domain expertise.</div>

  <h2>Scope and summary</h2>
  <p>{{ fixture_count }} fixture(s) with team-attributed timeline records were selected. The processed store contains {{ total_canonical_matches }} fixture timeline(s) in total.</p>
  <div class="metrics">
    <div class="metric"><div class="value">{{ fixture_count }}</div><div class="label">Fixtures with timeline records</div></div>
    <div class="metric"><div class="value">{{ official_score_per_fixture }}</div><div class="label">Published final score / timeline fixture</div></div>
    <div class="metric"><div class="value">{{ source_value_per_fixture }}</div><div class="label">Source score-event value / fixture</div></div>
    <div class="metric"><div class="value">{{ tries_per_fixture }}</div><div class="label">Tries / fixture</div></div>
    <div class="metric"><div class="value">{{ yellow_cards }}</div><div class="label">Recorded yellow cards</div></div>
  </div>

  <h2>Candidate observations</h2>
  {% if insights %}
    {% for insight in insights %}
      <article class="insight">
        <p><strong>{{ insight.category|replace('_', ' ')|title }}</strong></p>
        <p>{{ insight.statement }}</p>
        <small>Evidence: {{ insight.metric }}{% if insight.team_value is not none %} = {{ '%.3f'|format(insight.team_value) }}{% endif %}; sample: {{ insight.sample_matches }} fixture(s). {{ insight.confidence_note }}</small>
      </article>
    {% endfor %}
  {% else %}
    <p class="muted">No rule-based observation crossed its threshold for this selection.</p>
  {% endif %}

  <div class="grid">
    <section>
      <h2>Score-event breakdown</h2>
      {% if score_breakdown %}
      <table><thead><tr><th>Event type</th><th>Attempts</th><th>Made</th><th>Missed</th><th>Source value</th></tr></thead><tbody>
      {% for row in score_breakdown %}<tr><td>{{ row.event_type }}</td><td>{{ row.attempts }}</td><td>{{ row.made }}</td><td>{{ row.missed }}</td><td>{{ row.points }}</td></tr>{% endfor %}
      </tbody></table>
      {% else %}<p class="muted">No score-event records are available.</p>{% endif %}
    </section>
    <section>
      <h2>Scoring contributors</h2>
      {% if players %}
      <table><thead><tr><th>Player</th><th>Events</th><th>Source value</th><th>Event share</th></tr></thead><tbody>
      {% for row in players %}<tr><td>{{ row.player_name }}</td><td>{{ row.events }}</td><td>{{ row.source_score_event_value }}</td><td>{{ '%.0f%%'|format(row.team_event_share * 100) }}</td></tr>{% endfor %}
      </tbody></table>
      {% else %}<p class="muted">No player-attributed scoring records are available.</p>{% endif %}
    </section>
  </div>

  <h2>Fixtures used</h2>
  <table><thead><tr><th>Date</th><th>Round</th><th>Fixture</th><th>Published final score</th><th>Timeline records</th></tr></thead><tbody>
  {% for fixture in fixtures %}<tr><td>{{ fixture.match_date }}</td><td>{{ fixture.round }}</td><td>{{ fixture.fixture_label }}</td><td>{{ fixture.home_team }} {{ fixture.home_final_score }} - {{ fixture.away_final_score }} {{ fixture.away_team }}</td><td>{{ fixture.event_count }}</td></tr>{% endfor %}
  </tbody></table>

  <h2>Charts</h2>
  {% for chart in charts %}
  <figure><img src="{{ chart.path }}" alt="{{ chart.caption }}"><figcaption>{{ chart.caption }}</figcaption></figure>
  {% endfor %}

  <h2>Recorded discipline events</h2>
  {% if cards %}
  <table><thead><tr><th>Fixture ID</th><th>Minute</th><th>Player</th><th>Record</th></tr></thead><tbody>
  {% for card in cards %}<tr><td>{{ card.match_id }}</td><td>{{ card.minute }}</td><td>{{ card.player_name }}</td><td>{{ card.event_type }}</td></tr>{% endfor %}
  </tbody></table>
  {% else %}<p class="muted">No card record was supplied for this selection.</p>{% endif %}

  <h2>Data limitations</h2>
  <ul>
    <li>The public source is a scoring/line-up/card timeline, not full play-by-play. It does not support possession, tackle, carry, ruck, line-break, kick-distance or spatial analysis.</li>
    <li>It provides event minute but not a verified period boundary; timing charts use source-minute windows only.</li>
    <li>One published fixture in the downloaded season has a final score but no detailed timeline, so event-based rates exclude it.</li>
    <li>Source score-event values are kept separate from published final scores. In particular, penalty-try values can differ from final score accounting.</li>
    <li>This public source validates the architecture only; it is not assumed to match Queensland Reds/partner data or workflow.</li>
  </ul>
  <footer>Automatically generated descriptive preview. Analyst review, footage and partner-approved data remain essential.</footer>
</body>
</html>"""


def _rows(frame) -> list[dict[str, object]]:
    """Convert a DataFrame to template-safe primitive records."""
    if frame.empty:
        return []
    return frame.where(frame.notna(), None).to_dict(orient="records")


def generate_opposition_preview(
    project_root: Path, team_name: str, match_ids: Iterable[str] | None = None
) -> Path:
    """Write a manager-readable HTML preview and associated PNG charts.

    This function reads ``data/processed/canonical_events.csv`` only. It never
    reads the raw source directory, demonstrating downstream reuse of the
    normalized event store.
    """
    project_root = Path(project_root)
    events = load_canonical_events(project_root / "data" / "processed" / "canonical_events.csv")
    selected_fixture_ids = team_fixture_ids(events, team_name, match_ids)
    if not selected_fixture_ids:
        raise ValueError(f"No team-attributed canonical fixture records found for {team_name!r}.")
    selected_events = team_events(events, team_name, selected_fixture_ids)
    metrics = team_metrics(selected_events, team_name)
    report_directory = project_root / "outputs" / "reports"
    chart_directory = project_root / "outputs" / "charts"
    report_directory.mkdir(parents=True, exist_ok=True)
    report_path = report_directory / f"{filename_slug(team_name)}_opposition_preview.html"
    chart_paths = generate_team_charts(events, team_name, chart_directory, selected_fixture_ids)

    fixture_rows = fixture_context(events)
    fixture_rows = fixture_rows.loc[fixture_rows["match_id"].isin(selected_fixture_ids)].copy()
    fixture_rows = fixture_rows.sort_values("match_id", kind="stable")
    cards = discipline_events(selected_events, team_name).copy()
    if not cards.empty:
        cards["minute"] = (cards["timestamp_seconds"].astype(float) / 60).round(0).astype(int)
    score_rows = scoring_breakdown(selected_events)
    players = player_scoring_contributions(selected_events, team_name)
    insights = [item.to_dict() for item in generate_candidate_insights(events, team_name, selected_fixture_ids)]
    chart_captions = {
        "event_profile": "Source-recorded event profile for the selected team.",
        "scoring_by_fixture": "Source score-event values by selected fixture (not a final-score reconstruction).",
        "scoring_timing": "Source score-event values by source-minute window (not verified periods).",
    }
    template = Environment(loader=BaseLoader(), autoescape=select_autoescape(default_for_string=True)).from_string(
        REPORT_TEMPLATE
    )
    html = template.render(
        team_name=team_name,
        generated_at=datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        fixture_count=len(selected_fixture_ids),
        total_canonical_matches=int(events["match_id"].nunique()),
        official_score_per_fixture=f"{float(metrics['official_final_score_per_fixture']):.1f}",
        source_value_per_fixture=f"{float(metrics['source_score_event_value_per_fixture']):.1f}",
        tries_per_fixture=f"{float(metrics['tries_per_fixture']):.2f}",
        yellow_cards=int(metrics["yellow_cards"]),
        insights=insights,
        fixtures=_rows(fixture_rows),
        score_breakdown=_rows(score_rows),
        players=_rows(players),
        cards=_rows(cards[["match_id", "minute", "player_name", "event_type"]]) if not cards.empty else [],
        charts=[
            {
                "path": Path(relpath(path, start=report_directory)).as_posix(),
                "caption": chart_captions[name],
            }
            for name, path in chart_paths.items()
        ],
    )
    report_path.write_text(html, encoding="utf-8")
    return report_path
