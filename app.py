import io
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Unentschieden-Scanner Europa", page_icon="⚽", layout="wide")

st.title("⚽ Europa Unentschieden-Scanner & Serien-Tracker")
st.write("Durchsucht automatisch 20 europäische Top- & 2. Ligen (ohne API-Key).")

# Aktuelle Saison 2026/2027 (Code: 2627) bei Football-Data.co.uk
SAISON = "2627"

LIGEN = {
    "🇩🇪 1. Bundesliga": "D1",
    "🇩🇪 2. Bundesliga": "D2",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": "E0",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Championship (2. Liga)": "E1",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 League One (3. Liga)": "E2",
    "🇪🇸 La Liga": "SP1",
    "🇪🇸 La Liga 2": "SP2",
    "🇮🇹 Serie A": "I1",
    "🇮🇹 Serie B": "I2",
    "🇫🇷 Ligue 1": "F1",
    "🇫🇷 Ligue 2": "F2",
    "🇳🇱 Eredivisie": "N1",
    "🇵🇹 Primeira Liga": "P1",
    "🇹🇷 Süper Lig": "T1",
    "🇧🇪 Jupiler Pro League": "B1",
    "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Premiership": "SC0",
    "🇬🇷 Super League": "G1"
}

@st.cache_data(ttl=1800)
def lade_daten():
    alle_teams = []
    
    for liga_name, code in LIGEN.items():
        url = f"https://football-data.co.uk{SAISON}/{code}.csv"
        try:
            res = requests.get(url, timeout=8)
            if res.status_code != 200:
                continue
            
            df_liga = pd.read_csv(io.StringIO(res.text))
            df_liga = df_liga.dropna(subset=["HomeTeam", "AwayTeam", "FTR"])
            
            teams = set(df_liga["HomeTeam"]).union(set(df_liga["AwayTeam"]))
            
            for team in teams:
                heim = df_liga[df_liga["HomeTeam"] == team]
                ausw = df_liga[df_liga["AwayTeam"] == team]
                
                spiele = len(heim) + len(ausw)
                remis_heim = len(heim[heim["FTR"] == "D"])
                remis_ausw = len(ausw[ausw["FTR"] == "D"])
                unentschieden = remis_heim + remis_ausw
                quote = round((unentschieden / spiele * 100), 1) if spiele > 0 else 0
                
                # Letzte Spiele dieses Teams prüfen (Serie ohne Remis)
                alle_spiele_team = df_liga[(df_liga["HomeTeam"] == team) | (df_liga["AwayTeam"] == team)]
                ohne_remis_seit = 0
                for _, row in alle_spiele_team.iloc[::-1].iterrows():
                    if row["FTR"] == "D":
                        break
                    ohne_remis_seit += 1
                
                if quote >= 40 and spiele >= 5:
                    status = "🔥 Remis-Spezialist"
                elif unentschieden == 0 and spiele >= 6:
                    status = "⚠️ Noch KEIN Remis!"
                elif ohne_remis_seit >= 8:
                    status = f"⏳ Seit {ohne_remis_seit} Spielen kein Remis"
                else:
                    status = "Normal"
                
                alle_teams.append({
                    "Mannschaft": team,
                    "Liga": liga_name,
                    "Spiele": spiele,
                    "Unentschieden": unentschieden,
                    "Quote (%)": quote,
                    "Heim / Auswärts Remis": f"{remis_heim} / {remis_ausw}",
                    "Ohne Remis seit": f"{ohne_remis_seit} Sp.",
                    "Trend": status
                })
        except Exception:
            continue
            
    return pd.DataFrame(alle_teams)

if st.button("🔄 Live-Daten neu laden"):
    st.cache_data.clear()

with st.spinner("Lade aktuelle Spieldaten aus Europa..."):
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
    st.error("Daten konnten aktuell nicht abgerufen werden.")
