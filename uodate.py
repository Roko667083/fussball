
import os
import json
import time
import urllib.request

token = os.environ.get("TOKEN", "").strip()
ligen = [
    ("1. Bundesliga", "BL1"),
    ("Premier League", "PL"),
    ("Championship", "ELC"),
    ("La Liga", "PD"),
    ("Serie A", "SA"),
    ("Ligue 1", "FL1"),
    ("Eredivisie", "DED"),
    ("Primeira Liga", "PPL"),
]

teams = []
for name, code in ligen:
    url = f"https://football-data.org{code}/standings"
    req = urllib.request.Request(url, headers={"X-Auth-Token": token})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode())
            for s in data.get("standings", []):
                if s.get("type") == "TOTAL":
                    for row in s.get("table", []):
                        sp = row.get("playedGames", 0)
                        remis = row.get("draw", 0)
                        teams.append({
                            "name": row["team"].get("shortName") or row["team"].get("name"),
                            "liga": name,
                            "spiele": sp,
                            "remis": remis,
                            "quote": round(remis / sp * 100, 1) if sp > 0 else 0,
                        })
    except Exception as e:
        print("Fehler:", name, e)
    time.sleep(6.5)

with open("daten.json", "w", encoding="utf-8") as f:
    json.dump(teams, f, ensure_ascii=False)
