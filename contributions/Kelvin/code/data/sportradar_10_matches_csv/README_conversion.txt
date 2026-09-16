Sportradar 10-match JSON -> CSV conversion

Created from: sportradar_10_matches.zip

Files:
- individual_match_events/: 10 CSV files, one per match, one row per timeline event.
- combined_match_events.csv: all timeline events combined into one file.
- match_metadata.csv: one row per match.
- team_statistics.csv: one row per team per match, using Sportradar boxscore statistics.
- player_statistics.csv: one row per player per match, using Sportradar player statistics.
- period_scores.csv: period-by-period scores when provided.

Row counts:
- Matches: 10
- Timeline events: 3857
- Team-stat rows: 20
- Player-stat rows: 459
- Period-score rows: 20

Important:
- Event terminology is kept faithful to the source (for example ball_recycled is not renamed as ruck).
- competitor=home/away is additionally mapped to the actual team in the 'team' column.
- Nested player information is flattened into scorer/substitution/player columns, and the original players array is also kept in players_json.
- CSV files use UTF-8 with BOM for easier opening in Excel.
