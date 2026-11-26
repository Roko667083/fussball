import io
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Unentschieden-Scanner Europa", page_icon="⚽", layout="wide")

st.title("⚽ Europa Unentschieden-Scanner & Serien-Tracker")
st.write("Durchsucht automatisch europäische Top- & 2. Ligen (ohne API-Key).")

SAISONEN = ["2627", "2526"]

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

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

@st.cache_data(ttl=1800)
def lade_daten():
    alle_teams = []
    fehler_log = []
    
    for liga_name, code in LIGEN.items():
        df_liga = None
        for saison in SAISONEN:
            url = f"https://football-data.co.uk{saison}/{code}.csv"
            try:
                res = requests.get(url, headers=HEADERS, timeout=10)
                if res.status_code == 200 and "HomeTeam" in res.text:
                    df_liga = pd.read_csv(io.StringIO(res.text))
                    break
            except Exception as e:
                fehler_log.append(f"{liga_name}: {e}")
        
        if df_liga is None or df_liga.empty:
            continue
            
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
                status = f"⏳ Seit {ohne_remis_seit} Sp. kein Remis"
            else:
                status = "Normal"
            
            alle_teams.append({
                "Mannschaft": team,
                "Liga": liga_name,
                "Spiele": spiele,
                "Unentschieden": remis,
                "Quote (%)": quote,
                "Heim / Auswärts": f"{remis_heim} / {remis_ausw}",
                "Ohne Remis seit": f"{ohne_remis_seit} Sp.",
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
