import io
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Unentschieden-Scanner", page_icon="⚽", layout="wide")
st.title("⚽ Europa Unentschieden-Scanner")

LIGEN = {
    "🇩🇪 1. Bundesliga": "D1",
    "🇩🇪 2. Bundesliga": "D2",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": "E0",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Championship": "E1",
    "🇪🇸 La Liga": "SP1",
    "🇮🇹 Serie A": "I1",
    "🇫🇷 Ligue 1": "F1",
    "🇳🇱 Eredivisie": "N1",
    "🇵🇹 Primeira Liga": "P1",
    "🇹🇷 Süper Lig": "T1"
}

@st.cache_data(ttl=1800)
def lade_daten():
    teams_liste = []
    headers = {"User-Agent": "Mozilla/5.0"}
    
    for liga, code in LIGEN.items():
        for saison in ["2627", "2526"]:
            url = f"https://football-data.co.uk{saison}/{code}.csv"
            try:
                r = requests.get(url, headers=headers, timeout=10)
                if r.status_code == 200 and "HomeTeam" in r.text:
                    df = pd.read_csv(io.StringIO(r.text)).dropna(subset=["HomeTeam", "AwayTeam", "FTR"])
                    for t in set(df["HomeTeam"]).union(set(df["AwayTeam"])):
                        h = df[df["HomeTeam"] == t]
                        a = df[df["AwayTeam"] == t]
                        sp = len(h) + len(a)
                        remis = len(h[h["FTR"] == "D"]) + len(a[a["FTR"] == "D"])
                        teams_liste.append({
                            "Mannschaft": t,
                            "Liga": liga,
                            "Spiele": sp,
                            "Unentschieden": remis,
                            "Quote (%)": round(remis / sp * 100, 1) if sp > 0 else 0
                        })
                    break
            except Exception:
                continue
    return pd.DataFrame(teams_liste)

if st.button("🔄 Aktualisieren"):
    st.cache_data.clear()

df = lade_daten()

if not df.empty:
    min_sp = st.slider("Mindestanzahl Spiele:", 0, 30, 5)
    df_f = df[df["Spiele"] >= min_sp].sort_values(by=["Unentschieden", "Quote (%)"], ascending=False).reset_index(drop=True)
    df_f.index += 1
    st.dataframe(df_f.head(40), use_container_width=True)
else:
    st.warning("Aktuell keine Verbindung zum Datenserver möglich. Bitte in 1 Minute erneut auf 'Aktualisieren' klicken.")
