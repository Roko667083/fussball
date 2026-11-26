import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Unentschieden-Scanner", page_icon="⚽", layout="wide")
st.title("⚽ Unentschieden-Scanner (1., 2. & 3. Bundesliga + Österreich)")

LIGEN = {
    "🇩🇪 1. Bundesliga": "bl1",
    "🇩🇪 2. Bundesliga": "bl2",
    "🇩🇪 3. Liga": "bl3",
    "🇦🇹 Österreich Bundesliga": "öbl1"
}

@st.cache_data(ttl=1800)
def lade_daten():
    alle_teams = []
    for liga_name, code in LIGEN.items():
        for jahr in ["2026", "2025"]:
            url = f"https://openligadb.de{code}/{jahr}"
            try:
                res = requests.get(url, timeout=8)
                if res.status_code == 200 and len(res.json()) > 0:
                    for t in res.json():
                        sp = int(t.get("matches", 0))
                        remis = int(t.get("draw", 0))
                        alle_teams.append({
                            "Mannschaft": t.get("teamName"),
                            "Liga": liga_name,
                            "Spiele": sp,
                            "Unentschieden": remis,
                            "Quote (%)": round((remis / sp * 100), 1) if sp > 0 else 0
                        })
                    break
            except Exception:
                continue
    return pd.DataFrame(alle_teams)

if st.button("🔄 Live-Daten aktualisieren"):
    st.cache_data.clear()

df = lade_daten()

if not df.empty:
    ansicht = st.selectbox("Sortierung:", ["🏆 Meiste Unentschieden", "📈 Höchste Quote (%)", "⚠️ Noch KEIN Remis"])
    if ansicht == "🏆 Meiste Unentschieden":
        df = df.sort_values(by=["Unentschieden", "Quote (%)"], ascending=False)
    elif ansicht == "📈 Höchste Quote (%)":
        df = df.sort_values(by=["Quote (%)", "Unentschieden"], ascending=False)
    else:
        df = df[(df["Unentschieden"] == 0) & (df["Spiele"] >= 3)].sort_values(by="Spiele", ascending=False)
    df = df.reset_index(drop=True)
    df.index += 1
    st.dataframe(df, use_container_width=True)
else:
    st.error("Keine Daten geladen.")
