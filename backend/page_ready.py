import datetime
import streamlit as st

from database import get_bottles
from ui_table import render_wine_table


def render() -> None:
    st.markdown("# Ready to Drink")
    st.markdown('<div class="page-subtitle">In their drinking window now</div>', unsafe_allow_html=True)

    current_year = datetime.datetime.now().year
    df = get_bottles()

    if df.empty:
        st.info("No bottles in your cellar yet.")
        return

    ready = df[(df["drink_from"] <= current_year) & (df["drink_by"] >= current_year)]
    if ready.empty:
        st.info("Nothing is currently in its drinking window.")
        return

    label = "bottle" if len(ready) == 1 else "bottles"
    st.success(f"{len(ready)} {label} ready to drink right now.")
    st.divider()
    render_wine_table(ready, current_year)
