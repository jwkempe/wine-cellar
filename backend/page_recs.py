import streamlit as st

from database import get_bottles
from ai import get_recommendations


def render() -> None:
    st.markdown("# Recommendations")
    st.markdown('<div class="page-subtitle">Curated for your palate</div>', unsafe_allow_html=True)

    df = get_bottles()
    if df.empty:
        st.info("Add bottles and rate them to unlock personalized recommendations.")
        return

    st.markdown(
        '<p style="color:rgba(240,234,216,0.5);font-size:0.85rem;margin-bottom:1.5rem;">'
        "Based on your highest-rated bottles, our sommelier will suggest wines you're likely to love."
        "</p>",
        unsafe_allow_html=True,
    )
    if st.button("Generate Recommendations"):
        with st.spinner("Analyzing your taste profile..."):
            recommendation = get_recommendations(df)
        st.divider()
        st.markdown(recommendation)
