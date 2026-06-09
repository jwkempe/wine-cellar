import os
import streamlit as st
from dotenv import load_dotenv

import page_cellar
import page_add
import page_edit
import page_ready
import page_pairings
import page_recs
import page_meal
from database import init_db

load_dotenv()

st.set_page_config(
    page_title="Wine Cellar",
    page_icon="🍷",
    layout="wide",
    initial_sidebar_state="expanded",
)

with open(os.path.join(os.path.dirname(__file__), "styles.css")) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

init_db()

with st.sidebar:
    st.markdown("## Wine Cellar")
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:0.65rem;letter-spacing:0.2em;text-transform:uppercase;color:rgba(240,234,216,0.25);margin-bottom:0.5rem;">Navigation</p>', unsafe_allow_html=True)
    page = st.radio(
        "",
        ["My Cellar", "Add a Bottle", "Edit a Bottle", "Ready to Drink", "Food Pairings", "What's for Dinner?", "Recommendations"],
        label_visibility="collapsed",
    )
    st.markdown('<div class="sidebar-divider" style="margin-top:2rem;"></div>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:0.62rem;letter-spacing:0.1em;color:rgba(240,234,216,0.2);margin-top:1rem;">Powered by Claude</p>', unsafe_allow_html=True)

PAGES = {
    "My Cellar": page_cellar,
    "Add a Bottle": page_add,
    "Edit a Bottle": page_edit,
    "Ready to Drink": page_ready,
    "Food Pairings": page_pairings,
    "What's for Dinner?": page_meal,
    "Recommendations": page_recs,
}

PAGES[page].render()
