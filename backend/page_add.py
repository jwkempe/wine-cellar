import streamlit as st

from database import add_bottle
from ai import lookup_wine_info
from ui_auth import require_auth


def render() -> None:
    st.markdown("# Add a Bottle")
    st.markdown('<div class="page-subtitle">Catalog a new wine</div>', unsafe_allow_html=True)

    if not require_auth():
        st.stop()

    col1, col2 = st.columns(2)
    with col1:
        winery = st.text_input("Winery")
        region = st.text_input("Region", placeholder="e.g. Burgundy, Napa Valley")
        varietal = st.text_input("Varietal", placeholder="e.g. Pinot Noir, Cabernet Sauvignon")
        no_vintage = st.toggle("Non-Vintage (NV)")
        vintage = None if no_vintage else st.number_input("Vintage", min_value=1900, max_value=2100, value=2020)
    with col2:
        wine_name = st.text_input("Wine Name", placeholder="e.g. Reserve, Special Selection")
        appellation = st.text_input("Appellation", placeholder="e.g. Pommard, Stags Leap District")
        quantity = st.number_input("Bottles in Cellar", min_value=1, value=1)

    st.markdown('<div class="section-label" style="margin-top:1.5rem;">Drink Window & Tasting Notes</div>', unsafe_allow_html=True)

    if st.button("Lookup Drink Window & Tasting Notes"):
        if winery and varietal and region:
            with st.spinner("Consulting the sommelier..."):
                result = lookup_wine_info(winery, varietal, region, vintage, appellation)
                for line in result.strip().split("\n"):
                    if line.startswith("DRINK_FROM:"):
                        st.session_state["drink_from"] = int(line.replace("DRINK_FROM:", "").strip())
                    elif line.startswith("DRINK_BY:"):
                        st.session_state["drink_by"] = int(line.replace("DRINK_BY:", "").strip())
                    elif line.startswith("EXPERT_NOTES:"):
                        st.session_state["expert_notes"] = line.replace("EXPERT_NOTES:", "").strip()
            st.success("Done — review the details below and adjust if needed.")
        else:
            st.warning("Please fill in Winery, Varietal, and Region before looking up.")

    col1, col2 = st.columns(2)
    with col1:
        drink_from = st.number_input("Drink From", min_value=1900, max_value=2100, value=st.session_state.get("drink_from", 2024))
    with col2:
        drink_by = st.number_input("Drink By", min_value=1900, max_value=2100, value=st.session_state.get("drink_by", 2030))

    expert_notes = st.text_area("Expert Tasting Notes", value=st.session_state.get("expert_notes", ""), height=100)

    st.markdown('<div class="section-label" style="margin-top:1.5rem;">Your Notes</div>', unsafe_allow_html=True)
    your_notes = st.text_area("Tasting Notes", height=100)
    not_tried = st.toggle("I haven't tried this wine yet")
    your_rating = None if not_tried else st.number_input("Your Rating (0–100)", min_value=0.0, max_value=100.0, value=90.0, step=0.5)

    st.markdown("")
    if st.button("Add to Cellar"):
        add_bottle(winery, wine_name, region, appellation, varietal, vintage,
                   quantity, drink_from, drink_by, your_notes, your_rating, expert_notes)
        for key in ["drink_from", "drink_by", "expert_notes"]:
            st.session_state.pop(key, None)
        vintage_label = vintage if vintage else "NV"
        st.success(f"{vintage_label} {winery} {wine_name} added to your cellar.")
