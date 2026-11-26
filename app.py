import io
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Unentschieden-Scanner Europa", page_icon="⚽", layout="wide")

st.title("⚽ Europa Unentschieden-Scanner & Serien-Tracker")
st.write("Durchsucht automatisch europäische Top- & 2. Ligen (ohne API-Key).")

# 1. OpenLigaDB (für 1., 2. & 3. Bundesliga - extrem zuverlässig)
OPENLIGA = {
    "🇩🇪 1. Bundesliga": "bl1",
    "🇩🇪 2. Bundesliga": "bl2",
    "🇩🇪 3. Liga": "bl3"
}

# 2. Football-Data.co.uk (für alle anderen europäischen Ligen, Saison 26/27 & 25/26 als Backup)
FD_LIGEN = {
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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

@st.cache_data(ttl=1800)
def lade_daten():
    alle_teams = []
    
    # Teil A: Deutsche Ligen über OpenLigaDB laden
    for liga_name, kuerzel in OPENLIGA.items():
        for jahr in ["2026", "2025"]:
            url = f"https://openligadb.de{kuerzel}/{jahr}"
            try:
                res = requests.get(url, timeout=8)
                if res.status_code == 200 and len(res.json()) > 0:
                    for t in res.json():
                        spiele = int(t.get("matches", 0))
                        remis = int(t.get("draw", 0))
                        quote = round((remis / spiele * 100), 1) if spiele > 0 else 0
                        
                        if quote >= 40 and spiele >= 5:
                            status = "🔥 Remis-Spezialist"
                        elif remis == 0 and spiele >= 6:
                            status = "⚠️ Noch KEIN Remis!"
                        else:
                            status = "Normal"
                            
                        alle_teams.append({
                            "Mannschaft": t.get("teamName", "Unbekannt"),
                            "Liga": liga_name,
                            "Spiele": spiele,
                            "Unentschieden": remis,
                            "Quote (%)": quote,
                            "Heim / Auswärts": "- / -",
                            "Ohne Remis seit": "-",
                            "Trend": status
                        })
                    break
            except Exception:
                continue

    # Teil B: Europäische Ligen über Football-Data laden
    for liga_name, code in FD_LIGEN.items():
        for saison in ["2627", "2526"]:
            url = f"https://football-data.co.uk{saison}/{code}.csv"
            try:
                res = requests.get(url, headers=HEADERS, timeout=8)
                if res.status_code == 200 and "HomeTeam" in res.text:
                    df_liga = pd.read_csv(io.StringIO(res.text)).dropna(subset=["HomeTeam", "AwayTeam", "FTR"])
                    if df_liga.empty:
                        continue
                        
                    teams = set(df_liga["HomeTeam"]).union(set(df_liga["AwayTeam"]))
                    for team in teams:
                        heim = df_liga[df_liga["HomeTeam"] == team]
                        ausw = df_liga[df_liga["AwayTeam"] == team]
                        
                        spiele = len(heim) + len(ausw)
                        remis_heim = len(heim[heim["FTR"] == "D"])
                        remis_ausw = len(ausw[ausw["FTR"] == "D"])
                        remis = remis_heim + remis_ausw
                        quote = round((remis / spiele * 100), 1) if spiele > 0 else 0
                        
                        alle_spiele = df_liga[(df_liga["HomeTeam"] == team) | (df_liga["AwayTeam"] == team)]
                        ohne_remis = 0
                        for _, row in alle_spiele.iloc[::-1].iterrows():
                            if row["FTR"] == "D":
                                break
                            ohne_remis += 1
                            
                        if quote >= 40 and spiele >= 5:
                            status = "🔥 Remis-Spezialist"
                        elif remis == 0 and spiele >= 6:
                            status = "⚠️ Noch KEIN Remis!"
                        elif ohne_remis >= 8:
                            status = f"⏳ Seit {ohne_remis} Sp. kein Remis"
                        else:
                            status = "Normal"
                            
                        alle_teams.append({
                            "Mannschaft": team,
                            "Liga": liga_name,
                            "Spiele": spiele,
                            "Unentschieden": remis,
                            "Quote (%)": quote,
                            "Heim / Auswärts": f"{remis_heim} / {remis_ausw}",
                            "Ohne Remis seit": f"{ohne_remis} Sp.",
                            "Trend": status
                        })
                    break
            except Exception:
                continue
                
    return pd.DataFrame(alle_teams)

if st.button("🔄 Live-Daten aktualisieren"):
    st.cache_data.clear()

with st.spinner("Scanne europäische Ligen..."):
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
    st.error("Daten konnten nicht geladen werden. Bitte klicke oben auf 'Live-Daten aktualisieren'.")
