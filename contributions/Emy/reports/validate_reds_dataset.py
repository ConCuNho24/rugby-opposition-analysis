"""
P631 Data Understanding and Validation
Author: Ngoc Ha Nguyen (n12248746), Team T243

Runs repeatable data-quality and rugby-logic checks on a Partner event file
(XLSX or CSV, one row per recorded event) and writes the results to Markdown.

Usage:
    python validate_reds_dataset.py <event_file.xlsx|.csv> [output.md]
"""
import sys
from pathlib import Path

import pandas as pd

KEY_FIELDS = [
    "FXID", "teamName", "playerName", "MatchTime", "period", "x_coord", "y_coord",
    "x_coord_end", "y_coord_end", "actionName", "ActionTypeName", "ActionResultName",
    "PlayNum", "SetNum", "assoc_playerName", "playerpositionName", "playerShirtNumber",
]

results = []  # (area, check, expected, actual, status)


def check(area, name, expected, actual, ok):
    results.append((area, name, str(expected), str(actual), "Pass" if ok else ("Review" if ok is None else "Fail")))


def load(path):
    p = Path(path)
    return pd.read_excel(p) if p.suffix.lower() in (".xlsx", ".xls") else pd.read_csv(p)


def main(path, out_path):
    df = load(path)
    n = len(df)

    # 1. Structure
    check("Structure", "Event rows", "> 0", n, n > 0)
    check("Structure", "Fixtures in file", "1 or more", df["FXID"].nunique(), df["FXID"].nunique() >= 1)
    check("Structure", "Teams per fixture", 2, df.groupby("FXID")["teamName"].nunique().max(),
          df.groupby("FXID")["teamName"].nunique().max() == 2)
    check("Structure", "Duplicate event IDs", 0, df["ID"].duplicated().sum(), df["ID"].duplicated().sum() == 0)
    empty = [c for c in df.columns if df[c].isna().all()]
    check("Structure", "Fully empty columns", "none", ", ".join(empty) or "none", None if empty else True)
    const = [c for c in df.columns if df[c].nunique(dropna=False) == 1]
    check("Structure", "Constant columns (match metadata repeated per row)", "expected for one fixture", len(const), None)

    # 2. Completeness
    for c in ["playerName", "actionName", "ActionTypeName", "ActionResultName"]:
        pct = round(df[c].isna().mean() * 100, 1)
        check("Completeness", f"Missing {c}", "low or explained", f"{pct}%", None if pct > 0 else True)
    team_level = df[df["playerName"].isna()]["actionName"].value_counts(dropna=False).to_dict()
    check("Completeness", "Events without a player are team-level events", "Possession, Sequences, Period and similar",
          team_level, None)
    unlabelled = df[df["actionName"].isna()]["action"].value_counts().to_dict()
    check("Completeness", "Action codes without a name", "none", unlabelled, None if unlabelled else True)
    zero_end = round(((df["x_coord_end"] == 0) & (df["y_coord_end"] == 0)).mean() * 100, 1)
    check("Completeness", "End coordinates stored as 0,0", "appears to mean not recorded, to confirm with Partner", f"{zero_end}% of rows", None)

    # 3. Validity
    t = df["MatchTime"]
    check("Validity", "MatchTime stored as MMSS (seconds part 0 to 59)", "all <= 59", int((t % 100).max()), (t % 100).max() <= 59)
    mt_sec = (t // 100) * 60 + t % 100
    check("Validity", "Match length after MMSS conversion (minutes)", "about 80 plus stoppage", round(mt_sec.max() / 60, 1),
          75 <= mt_sec.max() / 60 <= 95)
    check("Validity", "Periods", "1 and 2", sorted(df["period"].unique().tolist()), set(df["period"].unique()) <= {1, 2})
    out_x = df[(df["x_coord"] < 0) | (df["x_coord"] > 100)]
    check("Validity", "x_coord outside 0 to 100", "in-goal events only (tries and similar)",
          out_x["actionName"].value_counts().to_dict(), None)
    check("Validity", "y_coord range", "0 to 70", f"{df['y_coord'].min()} to {df['y_coord'].max()}",
          df["y_coord"].between(0, 70).all())
    back = int((df["ps_timestamp"].diff() < 0).sum())
    check("Validity", "Rows where timestamp goes backwards", "0, or sort before analysis", back, None if back else True)

    # 4. Consistency
    first = df.iloc[0]
    pts = {}
    for team in df["teamName"].unique():
        tries = (df["actionName"].eq("Try") & df["teamName"].eq(team)).sum()
        gk = df[df["actionName"].eq("Goal Kick") & df["teamName"].eq(team)]
        conv = (gk["ActionTypeName"].eq("Conversion") & gk["ActionResultName"].eq("Goal Kicked")).sum()
        pen = (gk["ActionTypeName"].isin(["Penalty Goal", "Drop Goal"]) & gk["ActionResultName"].eq("Goal Kicked")).sum()
        pts[team] = int(tries * 5 + conv * 2 + pen * 3)
    home, away = first["homeTeamName"], first["awayTeamName"]
    ft = (int(first["hometeamFTscore"]), int(first["awayteamFTscore"]))
    check("Consistency", "Points reproduced from Try and Goal Kick events equal final score",
          f"{home} {ft[0]}, {away} {ft[1]}", f"{home} {pts.get(home)}, {away} {pts.get(away)}",
          (pts.get(home), pts.get(away)) == ft)
    h1 = df[df["period"].eq(1)]
    ht_pts = {}
    for team in df["teamName"].unique():
        tries1 = (h1["actionName"].eq("Try") & h1["teamName"].eq(team)).sum()
        gk1 = h1[h1["actionName"].eq("Goal Kick") & h1["teamName"].eq(team)]
        conv1 = (gk1["ActionTypeName"].eq("Conversion") & gk1["ActionResultName"].eq("Goal Kicked")).sum()
        pen1 = (gk1["ActionTypeName"].isin(["Penalty Goal", "Drop Goal"]) & gk1["ActionResultName"].eq("Goal Kicked")).sum()
        ht_pts[team] = int(tries1 * 5 + conv1 * 2 + pen1 * 3)
    ht = (int(first["hometeamHTscore"]), int(first["awayteamHTscore"]))
    check("Consistency", "First-half points reproduced from events equal half-time score",
          f"{home} {ht[0]}, {away} {ht[1]}", f"{home} {ht_pts.get(home)}, {away} {ht_pts.get(away)}",
          (ht_pts.get(home), ht_pts.get(away)) == ht)
    check("Consistency", "Running score never decreases", 0,
          int((df["hometeamCurrentScore"].diff() < 0).sum() + (df["awayteamCurrentScore"].diff() < 0).sum()),
          (df["hometeamCurrentScore"].diff() < 0).sum() + (df["awayteamCurrentScore"].diff() < 0).sum() == 0)
    check("Consistency", "Final running score equals recorded FT score", ft,
          (int(df["hometeamCurrentScore"].max()), int(df["awayteamCurrentScore"].max())),
          (df["hometeamCurrentScore"].max(), df["awayteamCurrentScore"].max()) == ft)
    tk = df[df["actionName"].eq("Tackle")]
    mt = df[df["actionName"].eq("Missed Tackle")]
    check("Consistency", "Tackle result 'Missed' equals Missed Tackle events", len(mt),
          int(tk["ActionResultName"].eq("Missed").sum()), tk["ActionResultName"].eq("Missed").sum() == len(mt))
    opp = (tk["teamName"] != tk["assoc_playerTeamName"]).mean()
    check("Consistency", "Tackle team and associated ball carrier are on opposite teams", "100%", f"{opp:.0%}", opp == 1)
    home_res = df.loc[df["isHome"].eq("Y"), "result"].iloc[0]
    expected_res = "W" if ft[0] > ft[1] else ("L" if ft[0] < ft[1] else "D")
    check("Consistency", "isHome and result agree with final score", f"home team result {expected_res}",
          f"home team result {home_res}", home_res == expected_res)

    # 5. Rugby logic
    tries = df[df["actionName"].eq("Try")]
    check("Rugby logic", "All tries recorded at x > 100 for both teams and both halves",
          "team-relative coordinates, attack towards x = 100", tries["x_coord"].tolist(), (tries["x_coord"] > 100).all())
    kx = df[df["actionName"].eq("Kick")]["x_coord"].mean()
    check("Rugby logic", "Average kick position is in own half", "< 50", round(kx, 1), kx < 50)
    pm = df[df["actionName"].eq("Playmaker Options")]
    hb_pass = int((pm["ActionTypeName"].eq("Halfback at Breakdown") & pm["ActionResultName"].eq("Playmaker Option - Pass")).sum())
    check("Rugby logic", "Halfback passes counted as a breakdown 'decision'",
          "rule to confirm with Partner", f"{hb_pass} of {len(pm)} options", None)

    # Write report
    lines = [
        "# Data Validation Results",
        "",
        f"Source file: `{Path(path).name}`. Rows: {n}. Columns: {df.shape[1]}.",
        "",
        "| Area | Check | Expected | Actual | Status |",
        "|---|---|---|---|---|",
    ]
    for r in results:
        lines.append("| " + " | ".join(x.replace("|", ",") for x in r) + " |")
    lines += ["", "## Missing values in key fields", "", "| Field | Missing |", "|---|---|"]
    for c in KEY_FIELDS:
        if c in df:
            lines.append(f"| {c} | {df[c].isna().mean():.1%} |")
    lines += ["", "## Event counts by action and team", "",
              df.groupby(["actionName", "teamName"]).size().unstack(fill_value=0).to_markdown()]
    Path(out_path).write_text("\n".join(lines), encoding="utf-8")
    summary = pd.Series([r[4] for r in results]).value_counts().to_dict()
    print(f"Wrote {out_path}. Summary: {summary}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: python validate_reds_dataset.py <event_file> [output.md]")
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "validation_results.md")
