import os
import streamlit as st

CELLAR_PASSWORD = os.getenv("CELLAR_PASSWORD", "")


def require_auth() -> bool:
    """Show a password gate. Returns True if authenticated, False otherwise."""
    if st.session_state.get("authenticated"):
        return True

    st.markdown('<div class="section-label" style="margin-top:1rem;">Authentication Required</div>', unsafe_allow_html=True)
    st.markdown('<p style="color:rgba(240,234,216,0.45);font-size:0.85rem;margin-bottom:1.5rem;">This section requires a password to access.</p>', unsafe_allow_html=True)

    col1, _ = st.columns([2, 3])
    with col1:
        pwd = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Enter password")
        if st.button("Unlock"):
            if pwd == CELLAR_PASSWORD:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Incorrect password.")
    return False
