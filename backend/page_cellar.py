import datetime
import streamlit as st

from database import get_bottles
from ui_table import render_wine_table


def render() -> None:
    st.markdown("# My Cellar")
    st.markdown('<div class="page-subtitle">Collection Overview</div>', unsafe_allow_html=True)

    df = get_bottles()
    current_year = datetime.datetime.now().year

    if df.empty:
        st.info("Your cellar is empty. Add your first bottle to begin building your collection.")
        return

    total_bottles = df["quantity"].sum()
    ready = df[(df["drink_from"] <= current_year) & (df["drink_by"] >= current_year)]
    avg_rating = df["your_rating"].dropna().mean()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Bottles", int(total_bottles))
    col2.metric("Unique Wines", len(df))
    col3.metric("Ready to Drink", len(ready))
    col4.metric("Avg Rating", f"{avg_rating:.1f}" if not __import__("math").isnan(avg_rating) else "—")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        varietal_options = ["All Varietals"] + sorted(df["varietal"].dropna().unique().tolist())
        selected_varietal = st.selectbox("Varietal", varietal_options)
    with col2:
        region_options = ["All Regions"] + sorted(df["region"].dropna().unique().tolist())
        selected_region = st.selectbox("Region", region_options)

    filtered = df.copy()
    if selected_varietal != "All Varietals":
        filtered = filtered[filtered["varietal"] == selected_varietal]
    if selected_region != "All Regions":
        filtered = filtered[filtered["region"] == selected_region]

    st.caption(f"{len(filtered)} of {len(df)} wines")
    st.divider()

    render_wine_table(filtered, current_year)
