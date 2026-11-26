import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Unentschieden-Scanner Europa", page_icon="⚽", layout="wide")

st.title("⚽ Europa Unentschieden-Scanner & Serien-Tracker")
st.write("Durchsucht automatisch über 20 europäische Ligen (ohne API-Key).")

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

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def finde_entries(obj):
    if isinstance(obj, dict):
        if "entries" in obj and isinstance(obj["entries"], list):
            return obj["entries"]
        for v in obj.values():
            res = finde_entries(v)
            if res:
                return res
    elif isinstance(obj, list):
        for item in obj:
            res = finde_entries(item)
            if res:
                return res
    return []

@st.cache_data(ttl=1800)
def lade_daten():
    alle_teams = []
    
    for liga_name, liga_code in LIGEN.items():
        url_standings = f"https://espn.com{liga_code}/standings"
        try:
            res = requests.get(url_standings, headers=HEADERS, timeout=8)
            data = res.json()
            entries = finde_entries(data)
            
            for team_data in entries:
                team_name = team_data.get('team', {}).get('displayName', 'Unbekannt')
                stats = {s['name']: s['value'] for s in team_data.get('stats', []) if 'name' in s and 'value' in s}
                
                spiele = int(stats.get('gamesPlayed', 0))
                unentschieden = int(stats.get('ties', 0))
                quote = round((unentschieden / spiele * 100), 1) if spiele > 0 else 0
                
                if quote >= 40 and spiele >= 5:
                    status_info = "🔥 Remis-Spezialist"
                elif unentschieden == 0 and spiele >= 6:
                    status_info = "⚠️ Noch KEIN Remis!"
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
            
    return pd.DataFrame(alle_teams)

if st.button("🔄 Live-Daten neu laden"):
    st.cache_data.clear()

with st.spinner("Scanne über 20 europäische Ligen..."):
    df = lade_daten()

if not df.empty:
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
    st.error("Daten konnten nicht geladen werden. Bitte später erneut versuchen.")
