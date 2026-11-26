import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Unentschieden-Scanner Europa", page_icon="⚽", layout="wide")

st.title("⚽ Europa Unentschieden-Scanner & Serien-Tracker")
st.write("Durchsucht automatisch über 20 europäische Ligen (ohne API-Key).")

# Erweiterte Liste europäischer Ligen (ESPN Codes)
LIGEN = {
    "🇩🇪 1. Bundesliga": "ger.1",
    "🇩🇪 2. Bundesliga": "ger.2",
    "🇩🇪 3. Liga": "ger.3",
    "🇦🇹 Österreich Bundesliga": "aut.1",
    "🇨🇭 Schweiz Super League": "sui.1",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": "eng.1",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Championship (2. Liga)": "eng.2",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 League One (3. Liga)": "eng.3",
    "🇪🇸 La Liga": "esp.1",
    "🇪🇸 La Liga 2": "esp.2",
    "🇮🇹 Serie A": "ita.1",
    "🇮🇹 Serie B": "ita.2",
    "🇫🇷 Ligue 1": "fra.1",
    "🇫🇷 Ligue 2": "fra.2",
    "🇳🇱 Eredivisie": "ned.1",
    "🇵🇹 Primeira Liga": "por.1",
    "🇹🇷 Süper Lig": "tur.1",
    "🇧🇪 Jupiler Pro League": "bel.1",
    "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Premiership": "sco.1",
    "🇬🇷 Super League": "gre.1"
}

@st.cache_data(ttl=1800) # Aktualisiert alle 30 Minuten
def lade_daten():
    alle_teams = []
    
    for liga_name, liga_code in LIGEN.items():
        # 1. Tabelle abrufen
        url_standings = f"https://espn.com{liga_code}/standings"
        # 2. Letzte Spiele (Scoreboard) für Serien-Check abrufen
        url_scores = f"https://espn.com{liga_code}/scoreboard"
        
        try:
            res = requests.get(url_standings, timeout=5)
            data = res.json()
            entries = data['children']['standings']['entries']
            
            # Letzte Ergebnisse der Liga prüfen (ob letztes Spiel Remis war)
            letztes_remis = set()
            try:
                res_s = requests.get(url_scores, timeout=4).json()
                for event in res_s.get('events', []):
                    status = event['status']['type']['completed']
                    if status:
                        comp = event['competitions']['competitors']
                        if comp['score'] == comp['score']:
                            letztes_remis.add(comp['team']['displayName'])
                            letztes_remis.add(comp['team']['displayName'])
            except Exception:
                pass

            for team_data in entries:
                team_name = team_data['team']['displayName']
                stats = {s['name']: s['value'] for s in team_data['stats']}
                
                spiele = int(stats.get('gamesPlayed', 0))
                unentschieden = int(stats.get('ties', 0))
                quote = round((unentschieden / spiele * 100), 1) if spiele > 0 else 0
                
                # Status-Badge berechnen
                if quote >= 40 and spiele >= 5:
                    status_info = "🔥 Remis-Spezialist"
                elif unentschieden == 0 and spiele >= 6:
                    status_info = "⚠️ Noch KEIN Remis!"
                elif team_name in letztes_remis:
                    status_info = "🤝 Zuletzt Remis"
                else:
                    status_info = "Normal"
                
                alle_teams.append({
                    "Mannschaft": team_name,
                    "Liga": liga_name,
                    "Spiele": spiele,
                    "Unentschieden": unentschieden,
                    "Quote (%)": quote,
                    "Trend / Hinweis": status_info
                })
        except Exception:
            continue
            
    df = pd.DataFrame(alle_teams)
    return df

if st.button("🔄 Live-Daten neu laden"):
    st.cache_data.clear()

with st.spinner("Scanne über 20 europäische Ligen..."):
    df = lade_daten()

if not df.empty:
    # Filter-Optionen in der Seitenleiste / oben
    col1, col2 = st.columns(2)
    with col1:
        min_spiele = st.slider("Mindestanzahl Spiele:", 0, 30, 5)
    with col2:
        ansicht = st.selectbox("Sortierung / Filter:", [
            "🏆 Meiste Unentschieden (Gesamt)",
            "📈 Höchste Unentschieden-Quote (%)",
            "⚠️ Teams komplett OHNE Unentschieden (Überfällig)"
        ])

    df_gefiltert = df[df["Spiele"] >= min_spiele].copy()

    if ansicht == "🏆 Meiste Unentschieden (Gesamt)":
        df_gefiltert = df_gefiltert.sort_values(by=["Unentschieden", "Quote (%)"], ascending=[False, False])
    elif ansicht == "📈 Höchste Unentschieden-Quote (%)":
        df_gefiltert = df_gefiltert.sort_values(by=["Quote (%)", "Unentschieden"], ascending=[False, False])
    else:
        df_gefiltert = df_gefiltert[df_gefiltert["Unentschieden"] == 0].sort_values(by="Spiele", ascending=False)

    df_gefiltert = df_gefiltert.reset_index(drop=True)
    df_gefiltert.index += 1

    st.dataframe(df_gefiltert.head(40), use_container_width=True)
else:
    st.error("Daten konnten nicht geladen werden. Bitte klicke oben auf 'Live-Daten neu laden'.")
