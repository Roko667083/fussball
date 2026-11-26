import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Unentschieden-Scanner Europa", page_icon="⚽", layout="wide")

st.title("⚽ Europa Unentschieden-Scanner & Serien-Tracker")
st.write("Durchsucht automatisch europäische Top- & 2. Ligen (ohne API-Key).")

SAISONEN = ["2026-27", "2025-26"]

LIGEN = {
    "🇩🇪 1. Bundesliga": "de.1.json",
    "🇩🇪 2. Bundesliga": "de.2.json",
    "🇩🇪 3. Liga": "de.3.json",
    "🇦🇹 Österreich Bundesliga": "at.1.json",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": "en.1.json",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Championship (2. Liga)": "en.2.json",
    "🇪🇸 La Liga": "es.1.json",
    "🇪🇸 La Liga 2": "es.2.json",
    "🇮🇹 Serie A": "it.1.json",
    "🇮🇹 Serie B": "it.2.json",
    "🇫🇷 Ligue 1": "fr.1.json",
    "🇫🇷 Ligue 2": "fr.2.json",
    "🇳🇱 Eredivisie": "nl.1.json",
    "🇵🇹 Primeira Liga": "pt.1.json"
}

@st.cache_data(ttl=1800)
def lade_daten():
    alle_teams = []
    fehler_log = []
    
    for liga_name, datei in LIGEN.items():
        data = None
        for saison in SAISONEN:
            url = f"https://githubusercontent.com{saison}/{datei}"
            try:
                res = requests.get(url, timeout=8)
                if res.status_code == 200:
                    data = res.json()
                    break
            except Exception as e:
                fehler_log.append(f"{liga_name}: {e}")
        
        if not data:
            continue

        matches = data.get("matches", [])
        team_stats = {}
        
        for m in matches:
            score_dict = m.get("score")
            if not isinstance(score_dict, dict):
                continue
            ft = score_dict.get("ft")
            if not isinstance(ft, list) or len(ft) < 2:
                continue
            
            t1 = m.get("team1")
            t2 = m.get("team2")
            g1, g2 = ft[0], ft[1]
            
            if not t1 or not t2 or g1 is None or g2 is None:
                continue
            
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
            
    return pd.DataFrame(alle_teams), fehler_log

if st.button("🔄 Live-Daten neu laden"):
    st.cache_data.clear()

with st.spinner("Lade europäische Spieldaten..."):
    df, fehler = lade_daten()

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
    if fehler:
        st.write("Details:", fehler[:3])
