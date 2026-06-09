import streamlit as st

from database import get_bottles
from ai import get_wine_for_meal


def render() -> None:
    st.markdown("# What's for Dinner?")
    st.markdown('<div class="page-subtitle">Find the right bottle for your meal</div>', unsafe_allow_html=True)

    meal = st.text_area(
        "Describe your meal",
        placeholder="e.g. Grilled salmon with lemon butter and roasted asparagus",
        height=100,
    )

    st.markdown("")
    if st.button("Find a Pairing", disabled=not meal.strip()):
        df = get_bottles()
        with st.spinner("Consulting the sommelier..."):
            suggestion = get_wine_for_meal(meal.strip(), df)
        st.divider()
        st.markdown(suggestion)
