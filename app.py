import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Unentschieden-Scanner Europa", page_icon="⚽", layout="wide")

st.title("⚽ Europa Unentschieden-Scanner & Serien-Tracker")
st.write("Durchsucht automatisch europäische Top- & 2. Ligen (ohne API-Key).")

# Direkte, blockfreie OpenFootball-Datenquellen auf GitHub (Saison 2026/27)
LIGEN = {
    "🇩🇪 1. Bundesliga": "https://githubusercontent.com",
    "🇩🇪 2. Bundesliga": "https://githubusercontent.com",
    "🇩🇪 3. Liga": "https://githubusercontent.com",
    "🇦🇹 Österreich Bundesliga": "https://githubusercontent.com",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": "https://githubusercontent.com",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Championship (2. Liga)": "https://githubusercontent.com",
    "🇪🇸 La Liga": "https://githubusercontent.com",
    "🇪🇸 La Liga 2": "https://githubusercontent.com",
    "🇮🇹 Serie A": "https://githubusercontent.com",
    "🇮🇹 Serie B": "https://githubusercontent.com",
    "🇫🇷 Ligue 1": "https://githubusercontent.com",
    "🇫🇷 Ligue 2": "https://githubusercontent.com",
    "🇳🇱 Eredivisie": "https://githubusercontent.com",
    "🇵🇹 Primeira Liga": "https://githubusercontent.com"
}

@st.cache_data(ttl=1800)
def lade_daten():
    alle_teams = []
    
    for liga_name, url in LIGEN.items():
        try:
            res = requests.get(url, timeout=10)
            if res.status_code != 200:
                continue
            
            data = res.json()
            matches = data.get("matches", [])
            
            team_stats = {}
            
            for m in matches:
                score = m.get("score", {}).get("ft")
                if not score or len(score) < 2:
                    continue
                
                t1 = m.get("team1")
                t2 = m.get("team2")
                g1, g2 = score[0], score[1]
                
                for t in (t1, t2):
                    if t not in team_stats:
                        team_stats[t] = {
                            "spiele": 0,
                            "remis": 0,
                            "remis_heim": 0,
                            "remis_ausw": 0,
                            "ohne_remis": 0
                        }
                
                team_stats[t1]["spiele"] += 1
                team_stats[t2]["spiele"] += 1
                
                if g1 == g2:
                    team_stats[t1]["remis"] += 1
                    team_stats[t1]["remis_heim"] += 1
                    team_stats[t1]["ohne_remis"] = 0
                    
                    team_stats[t2]["remis"] += 1
                    team_stats[t2]["remis_ausw"] += 1
                    team_stats[t2]["ohne_remis"] = 0
                else:
                    team_stats[t1]["ohne_remis"] += 1
                    team_stats[t2]["ohne_remis"] += 1
            
            for team, s in team_stats.items():
                spiele = s["spiele"]
                remis = s["remis"]
                quote = round((remis / spiele * 100), 1) if spiele > 0 else 0
                ohne = s["ohne_remis"]
                
                if quote >= 40 and spiele >= 5:
                    status = "🔥 Remis-Spezialist"
                elif remis == 0 and spiele >= 6:
                    status = "⚠️ Noch KEIN Remis!"
                elif ohne >= 8:
                    status = f"⏳ Seit {ohne} Sp. kein Remis"
                else:
                    status = "Normal"
                
                alle_teams.append({
                    "Mannschaft": team,
                    "Liga": liga_name,
                    "Spiele": spiele,
                    "Unentschieden": remis,
                    "Quote (%)": quote,
                    "Heim / Auswärts": f"{s['remis_heim']} / {s['remis_ausw']}",
                    "Ohne Remis seit": f"{ohne} Sp.",
                    "Trend": status
                })
        except Exception:
            continue
            
    return pd.DataFrame(alle_teams)

if st.button("🔄 Live-Daten neu laden"):
    st.cache_data.clear()

with st.spinner("Lade europäische Spieldaten..."):
    df = lade_daten()

if not df.empty:
    col1, col2, col3 = st.columns(3)
    with col1:
        min_spiele = st.slider("Mindestanzahl Spiele:", 0, 30, 5)
    with col2:
        ansicht = st.selectbox("Sortierung / Filter:", [
            "🏆 Meiste Unentschieden (Gesamt)",
            "📈 Höchste Unentschieden-Quote (%)",
            "⚠️ Teams komplett OHNE Unentschieden (Überfällig)"
        ])
    with col3:
        gewaehlte_ligen = st.multiselect("Ligen filtern (leer = alle):", sorted(df["Liga"].unique()))

    df_gefiltert = df[df["Spiele"] >= min_spiele].copy()
    
    if gewaehlte_ligen:
        df_gefiltert = df_gefiltert[df_gefiltert["Liga"].isin(gewaehlte_ligen)]

    if ansicht == "🏆 Meiste Unentschieden (Gesamt)":
        df_gefiltert = df_gefiltert.sort_values(by=["Unentschieden", "Quote (%)"], ascending=[False, False])
    elif ansicht == "📈 Höchste Unentschieden-Quote (%)":
        df_gefiltert = df_gefiltert.sort_values(by=["Quote (%)", "Unentschieden"], ascending=[False, False])
    else:
        df_gefiltert = df_gefiltert[df_gefiltert["Unentschieden"] == 0].sort_values(by="Spiele", ascending=False)

    df_gefiltert = df_gefiltert.reset_index(drop=True)
    df_gefiltert.index += 1

    st.dataframe(df_gefiltert.head(50), use_container_width=True)
else:
    st.error("Daten konnten nicht geladen werden.")
