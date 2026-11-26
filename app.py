import time
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Unentschieden-Scanner Europa", page_icon="⚽", layout="wide")

st.title("⚽ Europa Unentschieden-Scanner & Serien-Tracker")
st.write("Nutzt die offizielle Football-Data.org Schnittstelle für aktuelle Top-Ligen.")

api_key = st.text_input("🔑 Dein kostenloser Football-Data.org API-Key:", type="password")

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
                                "Mannschaft": row.get("team", {}).get("shortName") or row.get("team", {}).get("name"),
                                "Liga": liga_name,
                                "Spiele": spiele,
                                "Unentschieden": remis,
                                "Quote (%)": quote,
                                "Trend": status
                            })
            time.sleep(0.7)
        except Exception:
            continue
            
    return pd.DataFrame(alle_teams)

if not api_key:
    st.info("👆 Bitte gib oben deinen kostenlosen API-Key von Football-Data.org ein, um die Tabellen zu laden.")
else:
    if st.button("🔄 Live-Daten neu laden"):
        st.cache_data.clear()

    with st.spinner("Lade aktuelle Ligen aus Europa (dauert ca. 6 Sekunden)..."):
        df = lade_daten(api_key)

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
        st.error("Keine Daten geladen. Bitte prüfe, ob dein API-Key richtig kopiert wurde.")
