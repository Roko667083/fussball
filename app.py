import time
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Unentschieden-Scanner Europa", page_icon="⚽", layout="wide")
st.title("⚽ Europa Unentschieden-Scanner")

api_key = st.text_input("🔑 Dein Football-Data.org API-Token:", type="password")

LIGEN = {
    "🇩🇪 1. Bundesliga": "BL1",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": "PL",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Championship (2. Liga)": "ELC",
    "🇪🇸 La Liga": "PD",
    "🇮🇹 Serie A": "SA",
    "🇫🇷 Ligue 1": "FL1",
    "🇳🇱 Eredivisie": "DED",
    "🇵🇹 Primeira Liga": "PPL"
}

@st.cache_data(ttl=1800)
def lade_daten(token):
    alle_teams = []
    headers = {"X-Auth-Token": token.strip()}
    for liga_name, code in LIGEN.items():
        url = f"https://football-data.org{code}/standings"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                for standing in res.json().get("standings", []):
                    if standing.get("type") == "TOTAL":
                        for row in standing.get("table", []):
                            sp = row.get("playedGames", 0)
                            remis = row.get("draw", 0)
                            alle_teams.append({
                                "Mannschaft": row.get("team", {}).get("shortName") or row.get("team", {}).get("name"),
                                "Liga": liga_name,
                                "Spiele": sp,
                                "Unentschieden": remis,
                                "Quote (%)": round((remis / sp * 100), 1) if sp > 0 else 0
                            })
            time.sleep(0.7)
        except Exception:
            continue
    return pd.DataFrame(alle_teams)

if api_key:
    with st.spinner("Lade Ligen..."):
        df = lade_daten(api_key)
    if not df.empty:
        ansicht = st.selectbox("Filter:", ["🏆 Meiste Unentschieden", "📈 Höchste Quote (%)", "⚠️ Noch KEIN Remis"])
        if ansicht == "🏆 Meiste Unentschieden":
            df = df.sort_values(by=["Unentschieden", "Quote (%)"], ascending=False)
        elif ansicht == "📈 Höchste Quote (%)":
            df = df.sort_values(by=["Quote (%)", "Unentschieden"], ascending=False)
        else:
            df = df[(df["Unentschieden"] == 0) & (df["Spiele"] >= 4)].sort_values(by="Spiele", ascending=False)
        df = df.reset_index(drop=True)
        df.index += 1
        st.dataframe(df.head(50), use_container_width=True)
    else:
        st.error("Bitte prüfe deinen Token – es wurden keine Daten zurückgegeben.")
