import time
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Unentschieden-Scanner Europa", page_icon="⚽", layout="wide")

st.title("⚽ Europa Unentschieden-Scanner")
st.write("Durchsucht europäische Top- & 2. Ligen über dein Football-Data.org Konto.")

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
    fehler_meldungen = []
    headers = {"X-Auth-Token": token.strip()}
    
    for liga_name, code in LIGEN.items():
        url = f"https://football-data.org{code}/standings"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                for standing in data.get("standings", []):
                    if standing.get("type") == "TOTAL":
                        for row in standing.get("table", []):
                            spiele = row.get("playedGames", 0)
                            remis = row.get("draw", 0)
                            quote = round((remis / spiele * 100), 1) if spiele > 0 else 0
                            
                            if quote >= 40 and spiele >= 5:
                                status = "🔥 Remis-Spezialist"
                            elif remis == 0 and spiele >= 6:
                                status = "⚠️ Noch KEIN Remis!"
                            else:
                                status = "Normal"
                                
                            alle_teams.append({
                                "Mannschaft": row["team"].get("shortName") or row["team"].get("name"),
                                "Liga": liga_name,
                                "Spiele": spiele,
                                "Unentschieden": remis,
                                "Quote (%)": quote,
                                "Trend": status
                            })
            else:
                fehler_meldungen.append(f"{liga_name}: Status {res.status_code} ({res.text[:80]})")
        except Exception as e:
            fehler_meldungen.append(f"{liga_name}: {str(e)}")
        
        time.sleep(0.7)
            
    return pd.DataFrame(alle_teams), fehler_meldungen

if api_key:
    with st.spinner("Lade offizielle Tabellen aus Europa (dauert ca. 6 Sekunden)..."):
        df, fehler = lade_daten(api_key)
        
    if not df.empty:
        col1, col2 = st.columns(2)
        with col1:
            min_spiele = st.slider("Mindestanzahl Spiele:", 0, 30, 5)
        with col2:
            ansicht = st.selectbox("Sortierung:", [
                "🏆 Meiste Unentschieden (Gesamt)",
                "📈 Höchste Unentschieden-Quote (%)",
                "⚠️ Teams OHNE Unentschieden"
            ])
            
        df_f = df[df["Spiele"] >= min_spiele].copy()
        if ansicht == "🏆 Meiste Unentschieden (Gesamt)":
            df_f = df_f.sort_values(by=["Unentschieden", "Quote (%)"], ascending=False)
        elif ansicht == "📈 Höchste Unentschieden-Quote (%)":
            df_f = df_f.sort_values(by=["Quote (%)", "Unentschieden"], ascending=False)
        else:
            df_f = df_f[df_f["Unentschieden"] == 0].sort_values(by="Spiele", ascending=False)
            
        df_f = df_f.reset_index(drop=True)
        df_f.index += 1
        st.dataframe(df_f.head(50), use_container_width=True)
    else:
        st.error("Keine Daten geladen.")
        if fehler:
            st.write("Rückmeldung vom Server:", fehler)
else:
    st.info("👆 Bitte füge oben deinen API-Token von football-data.org ein.")
