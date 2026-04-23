import pandas as pd
import streamlit as st

from database import get_bottles
from ai import get_pairing_suggestion


def _bottle_label(row: pd.Series) -> str:
    vintage_str = "NV" if pd.isna(row["vintage"]) else str(int(row["vintage"]))
    wine_name_str = f" {row['wine_name']}" if row["wine_name"] and not pd.isna(row["wine_name"]) else ""
    return f"{vintage_str} {row['winery']}{wine_name_str} — {row['varietal']}"


def render() -> None:
    st.markdown("# Food Pairings")
    st.markdown('<div class="page-subtitle">Sommelier recommendations</div>', unsafe_allow_html=True)

    df = get_bottles()
    if df.empty:
        st.info("No bottles in your cellar yet.")
        return

    bottle_options = {_bottle_label(row): int(row["id"]) for _, row in df.iterrows()}
    selected = st.selectbox("Select a bottle", list(bottle_options.keys()))
    bottle_id = bottle_options[selected]
    bottle = df[df["id"] == bottle_id].iloc[0]

    st.markdown("")
    if st.button("Get Pairing Suggestions"):
        with st.spinner("Consulting the sommelier..."):
            suggestion = get_pairing_suggestion(
                bottle["winery"], bottle["varietal"], bottle["region"],
                bottle["vintage"], bottle["your_notes"], bottle["expert_notes"]
            )
        st.divider()
        st.markdown(suggestion)
