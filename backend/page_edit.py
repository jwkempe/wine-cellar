import pandas as pd
import streamlit as st

from database import get_bottles, update_bottle, delete_bottle
from ui_auth import require_auth


def _bottle_label(row: pd.Series) -> str:
    vintage_str = "NV" if pd.isna(row["vintage"]) else str(int(row["vintage"]))
    wine_name_str = f" {row['wine_name']}" if row["wine_name"] and not pd.isna(row["wine_name"]) else ""
    appellation_str = f" {row['appellation']}" if row["appellation"] and not pd.isna(row["appellation"]) else ""
    varietal_str = f" {row['varietal']}" if row["varietal"] and not pd.isna(row["varietal"]) else ""
    return f"{vintage_str} {row['winery']}{wine_name_str}{appellation_str}{varietal_str}"


def render() -> None:
    st.markdown("# Edit a Bottle")
    st.markdown('<div class="page-subtitle">Update your records</div>', unsafe_allow_html=True)

    if not require_auth():
        st.stop()

    df = get_bottles()
    if df.empty:
        st.info("No bottles in your cellar yet.")
        return

    bottle_options = {_bottle_label(row): int(row["id"]) for _, row in df.iterrows()}
    selected = st.selectbox("Select a bottle", list(bottle_options.keys()))
    bottle_id = bottle_options[selected]
    bottle = df[df["id"] == bottle_id].iloc[0]

    st.markdown('<div class="section-label" style="margin-top:1.5rem;">Wine Details</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        winery = st.text_input("Winery", value=bottle["winery"])
        region = st.text_input("Region", value=bottle["region"])
        varietal = st.text_input("Varietal", value=bottle["varietal"])
        no_vintage = st.toggle("Non-Vintage (NV)", value=bottle["vintage"] is None or pd.isna(bottle["vintage"]))
        vintage = None if no_vintage else st.number_input(
            "Vintage", min_value=1900, max_value=2100,
            value=int(bottle["vintage"]) if not pd.isna(bottle["vintage"]) else 2020
        )
    with col2:
        wine_name = st.text_input("Wine Name", value=str(bottle["wine_name"] or ""))
        appellation = st.text_input("Appellation", value=str(bottle["appellation"] or ""))
        quantity = st.number_input(
            "Bottles in Cellar", min_value=0,
            value=int(bottle["quantity"]) if not pd.isna(bottle["quantity"]) else 0
        )

    col1, col2 = st.columns(2)
    with col1:
        drink_from = st.number_input(
            "Drink From", min_value=1900, max_value=2100,
            value=int(bottle["drink_from"]) if not pd.isna(bottle["drink_from"]) else 2024
        )
    with col2:
        drink_by = st.number_input(
            "Drink By", min_value=1900, max_value=2100,
            value=int(bottle["drink_by"]) if not pd.isna(bottle["drink_by"]) else 2030
        )

    expert_notes = st.text_area("Expert Tasting Notes", value=str(bottle["expert_notes"] or ""), height=100)

    st.markdown('<div class="section-label" style="margin-top:1rem;">Your Notes</div>', unsafe_allow_html=True)
    your_notes = st.text_area("Tasting Notes", value=str(bottle["your_notes"] or ""), height=100)
    not_tried = st.toggle(
        "I haven't tried this wine yet",
        value=bottle["your_rating"] is None or pd.isna(bottle["your_rating"])
    )
    your_rating = None if not_tried else st.number_input(
        "Your Rating (0–100)", min_value=0.0, max_value=100.0,
        value=float(bottle["your_rating"]) if not pd.isna(bottle["your_rating"]) else 90.0,
        step=0.5
    )

    st.markdown("")
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("Save Changes"):
            update_bottle(bottle_id, winery, wine_name, region, appellation, varietal,
                          vintage, quantity, drink_from, drink_by, your_notes, your_rating, expert_notes)
            st.success("Bottle updated.")
            st.rerun()
    with col2:
        if st.button("Delete Bottle"):
            delete_bottle(bottle_id)
            st.warning("Deleted from your cellar.")
