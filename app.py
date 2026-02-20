import streamlit as st
import streamlit.components.v1 as components
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
import anthropic
import datetime
from dotenv import load_dotenv
import os

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
CELLAR_PASSWORD = os.getenv("CELLAR_PASSWORD", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Wine Cellar",
    page_icon="🍷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Premium CSS injection ─────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400&family=DM+Sans:wght@300;400;500&display=swap');

/* ── Root variables ── */
:root {
    --bg-primary: #0e0d0c;
    --bg-secondary: #161412;
    --bg-card: #1c1917;
    --bg-card-hover: #221f1b;
    --border: #2e2a25;
    --border-subtle: #1f1c18;
    --gold: #c9a84c;
    --gold-light: #e2c47a;
    --gold-dim: rgba(201, 168, 76, 0.15);
    --cream: #f0ead8;
    --cream-dim: rgba(240, 234, 216, 0.6);
    --cream-faint: rgba(240, 234, 216, 0.15);
    --wine: #8b2635;
    --wine-light: #b84455;
    --text-primary: #f0ead8;
    --text-secondary: rgba(240, 234, 216, 0.6);
    --text-muted: rgba(240, 234, 216, 0.3);
    --success: #5a8a5a;
    --warning: #a07840;
}

/* ── Global resets ── */
html, body, .stApp {
    background-color: var(--bg-primary) !important;
    font-family: 'DM Sans', sans-serif !important;
    color: var(--text-primary) !important;
}

/* ── Sidebar collapse button fix ── */
[data-testid="stSidebarCollapseButton"] button {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 2px !important;
    color: var(--gold) !important;
}

[data-testid="stSidebarCollapseButton"] button:hover {
    border-color: var(--gold) !important;
    background: var(--gold-dim) !important;
}

/* Hide the text label, keep the icon */
[data-testid="stSidebarCollapseButton"] button span:not(:has(svg)) {
    display: none !important;
}

[data-testid="stSidebarCollapseButton"] button svg {
    color: var(--gold) !important;
    fill: var(--gold) !important;
}

/* Also catch the collapsed state button */
[data-testid="collapsedControl"] {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 0 2px 2px 0 !important;
    color: var(--gold) !important;
}

[data-testid="collapsedControl"]:hover {
    border-color: var(--gold) !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: var(--bg-secondary) !important;
    border-right: 1px solid var(--border) !important;
}

[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span {
    color: var(--text-secondary) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    font-family: 'Cormorant Garamond', serif !important;
    color: var(--gold) !important;
    font-weight: 300 !important;
    letter-spacing: 0.05em !important;
    text-transform: none !important;
    font-size: 1.8rem !important;
}

[data-testid="stSidebar"] .stRadio label {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: var(--text-secondary) !important;
    padding: 0.5rem 0 !important;
    transition: color 0.2s !important;
}

[data-testid="stSidebar"] .stRadio label:hover {
    color: var(--gold-light) !important;
}

[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] div:first-child {
    border-color: var(--border) !important;
    background: transparent !important;
}

/* ── Main content area ── */
.main .block-container {
    padding: 2.5rem 3rem 4rem !important;
    max-width: 1400px !important;
}

/* ── Page titles ── */
h1 {
    font-family: 'Cormorant Garamond', serif !important;
    font-weight: 300 !important;
    font-size: 3rem !important;
    color: var(--cream) !important;
    letter-spacing: 0.02em !important;
    margin-bottom: 0.25rem !important;
    line-height: 1.1 !important;
}

h2 {
    font-family: 'Cormorant Garamond', serif !important;
    font-weight: 400 !important;
    font-size: 1.6rem !important;
    color: var(--cream) !important;
}

h3 {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    color: var(--gold) !important;
}

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 2px !important;
    padding: 1.25rem 1.5rem !important;
    transition: border-color 0.2s !important;
}

[data-testid="metric-container"]:hover {
    border-color: var(--gold) !important;
}

[data-testid="metric-container"] [data-testid="stMetricLabel"] {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    color: var(--text-muted) !important;
}

[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'Cormorant Garamond', serif !important;
    font-weight: 300 !important;
    font-size: 2.4rem !important;
    color: var(--cream) !important;
}

/* ── Buttons ── */
.stButton > button {
    background: transparent !important;
    border: 1px solid var(--gold) !important;
    color: var(--gold) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    border-radius: 2px !important;
    padding: 0.6rem 1.8rem !important;
    transition: all 0.2s !important;
    font-weight: 400 !important;
}

.stButton > button:hover {
    background: var(--gold-dim) !important;
    border-color: var(--gold-light) !important;
    color: var(--gold-light) !important;
    transform: translateY(-1px) !important;
}

.stButton > button:active {
    transform: translateY(0) !important;
}

/* ── Inputs ── */
.stTextInput input,
.stNumberInput input,
.stTextArea textarea {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 2px !important;
    color: var(--text-primary) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.9rem !important;
    transition: border-color 0.2s !important;
}

.stTextInput input:focus,
.stNumberInput input:focus,
.stTextArea textarea:focus {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 1px var(--gold-dim) !important;
    outline: none !important;
}

.stTextInput label,
.stNumberInput label,
.stTextArea label,
.stSelectbox label,
.stCheckbox label {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: var(--text-muted) !important;
    margin-bottom: 0.25rem !important;
}

/* Selectbox */
[data-baseweb="select"] > div {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 2px !important;
    color: var(--text-primary) !important;
}

[data-baseweb="select"] > div:hover {
    border-color: var(--gold) !important;
}

[data-baseweb="popover"] {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
}

[role="option"] {
    background-color: var(--bg-card) !important;
    color: var(--text-primary) !important;
    font-family: 'DM Sans', sans-serif !important;
}

[role="option"]:hover, [aria-selected="true"] {
    background-color: var(--bg-card-hover) !important;
    color: var(--gold-light) !important;
}

/* ── Toggles ── */
/* Track */
[data-baseweb="toggle"] > div {
    background-color: #2e2a25 !important;
    border: 1px solid #3e3a35 !important;
}

/* Track - checked */
[data-testid="stToggle"] input:checked ~ div,
[data-baseweb="toggle"] input:checked + div,
[data-baseweb="toggle"][aria-checked="true"] > div {
    background-color: #c9a84c !important;
    border-color: #c9a84c !important;
}

/* Thumb */
[data-baseweb="toggle"] > div > div {
    background-color: #f0ead8 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.4) !important;
}

/* Label */
[data-testid="stToggle"] label,
[data-testid="stToggle"] p {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.08em !important;
    color: rgba(240, 234, 216, 0.55) !important;
    text-transform: none !important;
}

/* ── Placeholder text ── */
.stTextInput input::placeholder,
.stTextArea textarea::placeholder,
.stNumberInput input::placeholder,
input::placeholder,
textarea::placeholder {
    color: rgba(240, 234, 216, 0.35) !important;
    opacity: 1 !important;
}

/* ── Divider ── */
hr {
    border-color: var(--border) !important;
    margin: 1.5rem 0 !important;
}

/* ── Alerts ── */
.stAlert {
    border-radius: 2px !important;
    border-left-width: 2px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
}

/* ── Spinner ── */
.stSpinner > div {
    border-top-color: var(--gold) !important;
}

/* ── Caption ── */
.stCaption {
    font-family: 'DM Sans', sans-serif !important;
    color: var(--text-muted) !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.05em !important;
}

/* ── Markdown body ── */
.stMarkdown p {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.9rem !important;
    line-height: 1.7 !important;
    color: var(--text-secondary) !important;
}

/* ── Page subtitle ── */
.page-subtitle {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.72rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--gold);
    margin-top: -0.5rem;
    margin-bottom: 2rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.page-subtitle::before {
    content: '';
    display: inline-block;
    width: 24px;
    height: 1px;
    background: var(--gold);
}

/* ── Section label ── */
.section-label {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--text-muted);
    padding: 0.5rem 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.25rem;
}

/* ── Custom wine table ── */
.wine-table-wrap {
    width: 100%;
    overflow-x: auto;
    margin-top: 0.5rem;
}

.wine-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.82rem;
}

.wine-table thead tr {
    border-bottom: 1px solid #2e2a25;
}

.wine-table thead th {
    font-size: 0.62rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: rgba(240, 234, 216, 0.3);
    font-weight: 400;
    padding: 0 1.25rem 0.75rem 0;
    text-align: left;
    white-space: nowrap;
    cursor: pointer;
    user-select: none;
    transition: color 0.15s;
}

.wine-table thead th:hover {
    color: rgba(240, 234, 216, 0.7);
}

.wine-table thead th.sort-asc,
.wine-table thead th.sort-desc {
    color: var(--gold) !important;
}

.wine-table thead th .sort-arrow {
    display: inline-block;
    margin-left: 0.35rem;
    opacity: 0;
    font-size: 0.55rem;
    transition: opacity 0.15s;
    vertical-align: middle;
}

.wine-table thead th:hover .sort-arrow {
    opacity: 0.4;
}

.wine-table thead th.sort-asc .sort-arrow,
.wine-table thead th.sort-desc .sort-arrow {
    opacity: 1;
}

.wine-table tbody tr {
    border-bottom: 1px solid #1f1c18;
    transition: background-color 0.15s;
}

.wine-table tbody tr:hover {
    background-color: #1c1917;
}

.wine-table tbody td {
    padding: 0.9rem 1.25rem 0.9rem 0;
    color: rgba(240, 234, 216, 0.85);
    vertical-align: middle;
    white-space: nowrap;
}

.wine-table .td-wine {
    white-space: normal;
    min-width: 200px;
}

.wine-name {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1rem;
    font-weight: 400;
    color: #f0ead8;
    display: block;
    line-height: 1.3;
}

.wine-meta {
    font-size: 0.7rem;
    color: rgba(240, 234, 216, 0.35);
    display: block;
    margin-top: 0.15rem;
    letter-spacing: 0.04em;
}

.td-vintage {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.05rem;
    font-weight: 300;
    color: rgba(240, 234, 216, 0.45);
    min-width: 56px;
}

.td-qty {
    text-align: center;
    color: rgba(240, 234, 216, 0.45);
    min-width: 40px;
}

.td-window {
    min-width: 110px;
    color: rgba(240, 234, 216, 0.4);
    font-size: 0.78rem;
    letter-spacing: 0.02em;
}

.td-rating {
    min-width: 130px;
}

.rating-bar-bg {
    background: #2e2a25;
    border-radius: 1px;
    height: 2px;
    width: 72px;
    display: inline-block;
    vertical-align: middle;
    margin-right: 0.6rem;
    position: relative;
    top: -1px;
}

.rating-bar-fill {
    background: linear-gradient(90deg, #c9a84c, #e2c47a);
    border-radius: 1px;
    height: 2px;
    display: block;
}

.rating-score {
    font-size: 0.8rem;
    color: rgba(240, 234, 216, 0.55);
    vertical-align: middle;
    font-variant-numeric: tabular-nums;
}

.badge-ready {
    display: inline-block;
    font-size: 0.55rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #5a8a5a;
    border: 1px solid rgba(90, 138, 90, 0.5);
    border-radius: 2px;
    padding: 0.1rem 0.35rem;
    margin-left: 0.5rem;
    vertical-align: middle;
    position: relative;
    top: -1px;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--bg-secondary); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: var(--gold); }

/* ── Chrome cleanup ── */
header[data-testid="stHeader"] { background: transparent !important; border-bottom: none !important; }
footer { display: none !important; }
#MainMenu { display: none !important; }

.sidebar-divider { width: 100%; height: 1px; background: var(--border); margin: 1rem 0; }
</style>
""", unsafe_allow_html=True)


# ── Database setup ──────────────────────────────────────────────────────────

def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS bottles (
            id SERIAL PRIMARY KEY,
            winery TEXT,
            wine_name TEXT,
            region TEXT,
            appellation TEXT,
            varietal TEXT,
            vintage INTEGER,
            quantity INTEGER,
            drink_from INTEGER,
            drink_by INTEGER,
            your_notes TEXT,
            your_rating REAL,
            expert_notes TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_bottle(winery, wine_name, region, appellation, varietal, vintage, quantity, drink_from, drink_by, your_notes, your_rating, expert_notes):
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        INSERT INTO bottles (winery, wine_name, region, appellation, varietal, vintage, quantity, drink_from, drink_by, your_notes, your_rating, expert_notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (winery, wine_name, region, appellation, varietal, vintage, quantity, drink_from, drink_by, your_notes, your_rating, expert_notes))
    conn.commit()
    conn.close()

def get_bottles():
    conn = psycopg2.connect(DATABASE_URL)
    df = pd.read_sql_query("SELECT * FROM bottles ORDER BY id", conn)
    conn.close()
    for col in ["vintage", "quantity", "drink_from", "drink_by", "your_rating"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def update_bottle(id, winery, wine_name, region, appellation, varietal, vintage, quantity, drink_from, drink_by, your_notes, your_rating, expert_notes):
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        UPDATE bottles SET
            winery=%s, wine_name=%s, region=%s, appellation=%s, varietal=%s, vintage=%s,
            quantity=%s, drink_from=%s, drink_by=%s, your_notes=%s,
            your_rating=%s, expert_notes=%s
        WHERE id=%s
    ''', (winery, wine_name, region, appellation, varietal, vintage, quantity, drink_from, drink_by, your_notes, your_rating, expert_notes, id))
    conn.commit()
    conn.close()

def delete_bottle(id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM bottles WHERE id=%s", (id,))
    conn.commit()
    conn.close()


# ── Auth helper ──────────────────────────────────────────────────────────────

def require_auth():
    """Shows a password gate. Returns True if authenticated, False otherwise."""
    if st.session_state.get("authenticated"):
        return True

    st.markdown('<div class="section-label" style="margin-top:1rem;">Authentication Required</div>', unsafe_allow_html=True)
    st.markdown('<p style="color:rgba(240,234,216,0.45);font-size:0.85rem;margin-bottom:1.5rem;">This section requires a password to access.</p>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 3])
    with col1:
        pwd = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Enter password")
        if st.button("Unlock"):
            if pwd == CELLAR_PASSWORD:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Incorrect password.")
    return False


# ── Helper: render custom HTML wine table ─────────────────────────────────────

def escape_js(s):
    """Escape a string for safe embedding in a JS string literal."""
    if not s:
        return ""
    return str(s).replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace("\n", " ").replace("\r", "")

def render_wine_table(df, current_year=None):
    if current_year is None:
        current_year = datetime.datetime.now().year

    rows_html = ""
    for _, row in df.iterrows():
        vintage_str = "NV" if pd.isna(row["vintage"]) else str(int(row["vintage"]))
        wine_name_str = str(row["wine_name"]) if row["wine_name"] and not pd.isna(row["wine_name"]) else ""
        appellation_str = str(row["appellation"]) if row["appellation"] and not pd.isna(row["appellation"]) else ""
        varietal_str = str(row["varietal"]) if row["varietal"] and not pd.isna(row["varietal"]) else ""
        region_str = str(row["region"]) if row["region"] and not pd.isna(row["region"]) else ""
        expert_notes_str = str(row["expert_notes"]) if row["expert_notes"] and not pd.isna(row["expert_notes"]) else ""
        your_notes_str = str(row["your_notes"]) if row["your_notes"] and not pd.isna(row["your_notes"]) else ""

        display_name = str(row["winery"])
        if wine_name_str:
            display_name += f" {wine_name_str}"

        sub_parts = [p for p in [appellation_str or varietal_str, region_str] if p]
        sub_line = " · ".join(sub_parts)

        try:
            df_val = int(row["drink_from"])
            db_val = int(row["drink_by"])
            window_str = f"{df_val} – {db_val}"
            is_ready = df_val <= current_year <= db_val
            window_years = db_val - current_year
            if is_ready:
                window_pct = max(0, min(100, int((db_val - current_year) / max(db_val - df_val, 1) * 100)))
            else:
                window_pct = 0
        except:
            window_str = "—"
            is_ready = False
            window_pct = 0
            df_val = ""
            db_val = ""

        ready_badge = '<span class="badge-ready">Ready</span>' if is_ready else ""

        if pd.isna(row["your_rating"]):
            rating_html = '<span style="color:rgba(240,234,216,0.2);font-size:0.75rem;letter-spacing:0.1em;">Not rated</span>'
            rating_detail_html = '<span class="detail-empty">Not yet rated</span>'
        else:
            score = float(row["your_rating"])
            bar_width = int((score / 100) * 72)
            rating_html = f'''<span class="rating-bar-bg"><span class="rating-bar-fill" style="width:{bar_width}px;"></span></span><span class="rating-score">{score:.0f}</span>'''
            big_bar_width = int((score / 100) * 120)
            rating_detail_html = f'''<div class="detail-rating-row"><span class="detail-rating-score">{score:.0f}</span><span class="detail-rating-bar-bg"><span class="detail-rating-bar-fill" style="width:{big_bar_width}px;"></span></span></div>'''

        vintage_sort = str(int(row["vintage"])) if not pd.isna(row["vintage"]) else "0"
        window_sort = str(int(row["drink_from"])) if not pd.isna(row["drink_from"]) else "0"
        rating_sort = str(float(row["your_rating"])) if not pd.isna(row["your_rating"]) else "0"
        qty = int(row['quantity']) if not pd.isna(row['quantity']) else 0

        # Detail panel HTML
        expert_html = f'<p class="detail-notes-text">{escape_js(expert_notes_str)}</p>' if expert_notes_str else '<span class="detail-empty">No expert notes</span>'
        your_notes_html = f'<p class="detail-notes-text">{escape_js(your_notes_str)}</p>' if your_notes_str else '<span class="detail-empty">No tasting notes added yet</span>'
        
        window_bar_html = ""
        if df_val and db_val:
            window_bar_html = f'''
            <div class="detail-window-bar-wrap">
                <div class="detail-window-bar-bg">
                    <div class="detail-window-bar-fill" style="width:{window_pct}%"></div>
                </div>
                <div class="detail-window-labels">
                    <span>{df_val}</span><span>{db_val}</span>
                </div>
            </div>
            '''

        detail_html = f'''
        <div class="detail-panel">
            <div class="detail-grid">
                <div class="detail-col">
                    <div class="detail-section-label">Expert Notes</div>
                    {expert_html}
                    <div class="detail-section-label" style="margin-top:1.25rem;">Your Notes</div>
                    {your_notes_html}
                    <div class="detail-section-label" style="margin-top:1.25rem;">Your Rating</div>
                    {rating_detail_html}
                </div>
                <div class="detail-col">
                    <div class="detail-section-label">Drink Window</div>
                    <div class="detail-window-str">{"Ready now" if is_ready else window_str}</div>
                    {window_bar_html}
                    <a class="detail-pairing-btn" href="#" onclick="return false;">Get Food Pairings &#8594;</a>
                </div>
            </div>
        </div>
        '''

        rows_html += f"""<tr class="data-row" onclick="toggleDetail(this)">
            <td class="td-expand">&#9654;</td>
            <td class="td-vintage" data-sort="{vintage_sort}">{vintage_str}</td>
            <td class="td-wine" data-sort="{display_name}">
                <span class="wine-name">{display_name}{ready_badge}</span>
                <span class="wine-meta">{sub_line}</span>
            </td>
            <td class="td-qty" data-sort="{qty}">{qty}</td>
            <td class="td-window" data-sort="{window_sort}">{window_str}</td>
            <td class="td-rating" data-sort="{rating_sort}">{rating_html}</td>
        </tr>
        <tr class="detail-row" style="display:none;">
            <td colspan="6">{detail_html}</td>
        </tr>"""

    table_id = f"winetable_{abs(hash(str(df.index.tolist()))) % 100000}"
    num_rows = len(df)
    table_height = max(200, min(num_rows * 62 + 60, 1200))

    components.html(f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400&family=DM+Sans:wght@300;400;500&display=swap');
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: transparent; font-family: 'DM Sans', sans-serif; }}
    .wine-table-wrap {{ width: 100%; overflow-x: auto; }}
    .wine-table {{ width: 100%; border-collapse: collapse; font-family: 'DM Sans', sans-serif; font-size: 0.82rem; }}
    .wine-table thead tr {{ border-bottom: 1px solid #2e2a25; }}
    .wine-table thead th {{
        font-size: 0.62rem; letter-spacing: 0.18em; text-transform: uppercase;
        color: rgba(240,234,216,0.3); font-weight: 400; padding: 0 1.25rem 0.75rem 0;
        text-align: left; white-space: nowrap; cursor: pointer; user-select: none;
        transition: color 0.15s;
    }}
    .wine-table thead th:first-child {{ width: 20px; cursor: default; }}
    .wine-table thead th:hover {{ color: rgba(240,234,216,0.7); }}
    .wine-table thead th.sort-asc, .wine-table thead th.sort-desc {{ color: #c9a84c; }}
    .sort-arrow {{ display: inline-block; margin-left: 0.35rem; opacity: 0; font-size: 0.55rem; transition: opacity 0.15s; }}
    .wine-table thead th:hover .sort-arrow {{ opacity: 0.4; }}
    .wine-table thead th.sort-asc .sort-arrow, .wine-table thead th.sort-desc .sort-arrow {{ opacity: 1; }}
    .data-row {{ border-bottom: 1px solid #1f1c18; transition: background-color 0.15s; cursor: pointer; }}
    .data-row:hover {{ background-color: #1c1917; }}
    .data-row.expanded {{ background-color: #1c1917; border-bottom: none; }}
    .detail-row td {{ padding: 0; border-bottom: 1px solid #2e2a25; }}
    .wine-table tbody td {{ padding: 0.9rem 1.25rem 0.9rem 0; color: rgba(240,234,216,0.85); vertical-align: middle; white-space: nowrap; }}
    .td-expand {{ width: 20px; color: rgba(240,234,216,0.2); font-size: 0.5rem; transition: transform 0.2s, color 0.2s; padding-right: 0.5rem !important; }}
    .data-row.expanded .td-expand {{ transform: rotate(90deg); color: #c9a84c; }}
    .td-wine {{ white-space: normal; min-width: 200px; }}
    .wine-name {{ font-family: 'Cormorant Garamond', serif; font-size: 1rem; font-weight: 400; color: #f0ead8; display: block; line-height: 1.3; }}
    .wine-meta {{ font-size: 0.7rem; color: rgba(240,234,216,0.35); display: block; margin-top: 0.15rem; letter-spacing: 0.04em; }}
    .td-vintage {{ font-family: 'Cormorant Garamond', serif; font-size: 1.05rem; font-weight: 300; color: rgba(240,234,216,0.45); min-width: 56px; }}
    .td-qty {{ text-align: center; color: rgba(240,234,216,0.45); min-width: 40px; }}
    .td-window {{ min-width: 110px; color: rgba(240,234,216,0.4); font-size: 0.78rem; letter-spacing: 0.02em; }}
    .td-rating {{ min-width: 130px; }}
    .rating-bar-bg {{ background: #2e2a25; border-radius: 1px; height: 2px; width: 72px; display: inline-block; vertical-align: middle; margin-right: 0.6rem; position: relative; top: -1px; }}
    .rating-bar-fill {{ background: linear-gradient(90deg, #c9a84c, #e2c47a); border-radius: 1px; height: 2px; display: block; }}
    .rating-score {{ font-size: 0.8rem; color: rgba(240,234,216,0.55); vertical-align: middle; }}
    .badge-ready {{ display: inline-block; font-size: 0.55rem; letter-spacing: 0.14em; text-transform: uppercase; color: #5a8a5a; border: 1px solid rgba(90,138,90,0.5); border-radius: 2px; padding: 0.1rem 0.35rem; margin-left: 0.5rem; vertical-align: middle; position: relative; top: -1px; }}
    /* Detail panel */
    .detail-panel {{ padding: 1.5rem 1.5rem 1.75rem 2rem; background: #161412; animation: fadeIn 0.2s ease; }}
    @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(-4px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    .detail-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 2.5rem; }}
    .detail-section-label {{ font-size: 0.6rem; letter-spacing: 0.2em; text-transform: uppercase; color: rgba(240,234,216,0.25); margin-bottom: 0.5rem; }}
    .detail-notes-text {{ font-size: 0.85rem; line-height: 1.7; color: rgba(240,234,216,0.6); font-style: italic; white-space: normal; max-width: 480px; }}
    .detail-empty {{ font-size: 0.78rem; color: rgba(240,234,216,0.2); letter-spacing: 0.05em; }}
    .detail-rating-row {{ display: flex; align-items: center; gap: 0.75rem; margin-top: 0.25rem; }}
    .detail-rating-score {{ font-family: 'Cormorant Garamond', serif; font-size: 1.8rem; font-weight: 300; color: #c9a84c; line-height: 1; }}
    .detail-rating-bar-bg {{ background: #2e2a25; border-radius: 1px; height: 3px; width: 120px; display: inline-block; }}
    .detail-rating-bar-fill {{ background: linear-gradient(90deg, #c9a84c, #e2c47a); border-radius: 1px; height: 3px; display: block; }}
    .detail-window-str {{ font-family: 'Cormorant Garamond', serif; font-size: 1.4rem; font-weight: 300; color: rgba(240,234,216,0.7); margin-bottom: 0.75rem; }}
    .detail-window-bar-wrap {{ margin-top: 0.25rem; }}
    .detail-window-bar-bg {{ background: #2e2a25; border-radius: 1px; height: 3px; width: 100%; max-width: 180px; margin-bottom: 0.4rem; }}
    .detail-window-bar-fill {{ background: #5a8a5a; border-radius: 1px; height: 3px; transition: width 0.4s ease; }}
    .detail-window-labels {{ display: flex; justify-content: space-between; max-width: 180px; font-size: 0.65rem; color: rgba(240,234,216,0.25); letter-spacing: 0.08em; }}
    .detail-pairing-btn {{ display: inline-block; margin-top: 1.5rem; font-size: 0.7rem; letter-spacing: 0.15em; text-transform: uppercase; color: #c9a84c; text-decoration: none; border: 1px solid rgba(201,168,76,0.3); border-radius: 2px; padding: 0.45rem 0.9rem; transition: all 0.2s; }}
    .detail-pairing-btn:hover {{ background: rgba(201,168,76,0.1); border-color: #c9a84c; }}
    </style>
    </head>
    <body>
    <div class="wine-table-wrap">
        <table class="wine-table" id="{table_id}">
            <thead>
                <tr>
                    <th></th>
                    <th data-col="1" data-type="num">Vintage<span class="sort-arrow">&#9650;</span></th>
                    <th data-col="2" data-type="str">Wine<span class="sort-arrow">&#9650;</span></th>
                    <th data-col="3" data-type="num" style="text-align:center;">Qty<span class="sort-arrow">&#9650;</span></th>
                    <th data-col="4" data-type="num">Drink Window<span class="sort-arrow">&#9650;</span></th>
                    <th data-col="5" data-type="num">Rating<span class="sort-arrow">&#9650;</span></th>
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
    </div>
    <script>
    function toggleDetail(row) {{
        row.classList.toggle("expanded");
        var detailRow = row.nextElementSibling;
        if (detailRow && detailRow.classList.contains("detail-row")) {{
            detailRow.style.display = detailRow.style.display === "none" ? "table-row" : "none";
        }}
    }}
    (function() {{
        var table = document.getElementById("{table_id}");
        if (!table) return;
        var sortState = {{ col: null, asc: true }};
        function getCellValue(row, colIdx) {{
            var cell = row.cells[colIdx];
            return cell ? (cell.getAttribute("data-sort") || cell.innerText.trim()) : "";
        }}
        function sortTable(th, colIdx, colType) {{
            var tbody = table.querySelector("tbody");
            var allRows = Array.from(tbody.querySelectorAll("tr"));
            // Pair data rows with their detail rows
            var pairs = [];
            for (var i = 0; i < allRows.length; i++) {{
                if (allRows[i].classList.contains("data-row")) {{
                    pairs.push([allRows[i], allRows[i+1]]);
                }}
            }}
            var asc = (sortState.col === colIdx) ? !sortState.asc : true;
            pairs.sort(function(a, b) {{
                var aVal = getCellValue(a[0], colIdx);
                var bVal = getCellValue(b[0], colIdx);
                if (colType === "num") {{
                    aVal = parseFloat(aVal) || 0;
                    bVal = parseFloat(bVal) || 0;
                    return asc ? aVal - bVal : bVal - aVal;
                }} else {{
                    return asc ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
                }}
            }});
            pairs.forEach(function(pair) {{
                tbody.appendChild(pair[0]);
                tbody.appendChild(pair[1]);
            }});
            table.querySelectorAll("thead th[data-col]").forEach(function(h) {{
                h.classList.remove("sort-asc", "sort-desc");
                var arrow = h.querySelector(".sort-arrow");
                if (arrow) arrow.innerHTML = "&#9650;";
            }});
            th.classList.add(asc ? "sort-asc" : "sort-desc");
            var arrow = th.querySelector(".sort-arrow");
            if (arrow) arrow.innerHTML = asc ? "&#9650;" : "&#9660;";
            sortState = {{ col: colIdx, asc: asc }};
        }}
        table.querySelectorAll("thead th[data-col]").forEach(function(th) {{
            th.addEventListener("click", function() {{
                sortTable(th, parseInt(th.getAttribute("data-col")), th.getAttribute("data-type"));
            }});
        }});
    }})();
    </script>
    </body>
    </html>
    """, height=table_height, scrolling=True)


# ── AI functions ─────────────────────────────────────────────────────────────

def get_pairing_suggestion(winery, varietal, region, vintage, your_notes, expert_notes):
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": f"""You are a world-class sommelier. Suggest food pairings for this wine:

Winery: {winery}
Varietal: {varietal}
Region: {region}
Vintage: {vintage}
Tasting Notes: {your_notes or expert_notes}

Give 3-5 specific food pairing suggestions with a brief explanation for each. Be concise."""}]
    )
    return message.content[0].text

def get_recommendations(df):
    if df.empty or df["your_rating"].isna().all():
        return "Add some bottles and ratings to get personalized recommendations."

    top_bottles = df[df["your_rating"] >= 90].sort_values("your_rating", ascending=False).head(5)
    if top_bottles.empty:
        top_bottles = df.sort_values("your_rating", ascending=False).head(5)

    bottle_list = "\n".join([f"- {row['vintage']} {row['winery']} {row['varietal']} from {row['region']} (rated {row['your_rating']})"
                              for _, row in top_bottles.iterrows()])

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": f"""You are a world-class sommelier. Based on these wines a collector has rated highly:

{bottle_list}

Suggest 5 specific wines they might enjoy that aren't already in their list. Include winery, varietal, region, and why they'd enjoy it based on their taste profile. Be specific and concise."""}]
    )
    return message.content[0].text

def lookup_wine_info(winery, varietal, region, vintage, appellation=None):
    vintage_str = "Non-Vintage (NV)" if not vintage else str(int(vintage))
    appellation_str = appellation if appellation else "Not specified"

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": f"""You are a world-class sommelier and wine expert. For this wine:

Winery: {winery}
Varietal: {varietal}
Region: {region}
Appellation: {appellation_str}
Vintage: {vintage_str}

Please provide:
1. DRINK_FROM: The year this wine will start to peak (just the 4-digit year). If Non-Vintage, suggest the current year.
2. DRINK_BY: The year this wine should be consumed by (just the 4-digit year). If Non-Vintage, suggest 3-5 years from now.
3. EXPERT_NOTES: 2-3 sentences of professional tasting notes describing the expected flavor profile, structure, and character of this wine.

Format your response exactly like this:
DRINK_FROM: [year]
DRINK_BY: [year]
EXPERT_NOTES: [notes]"""}]
    )
    return message.content[0].text


# ── App ───────────────────────────────────────────────────────────────────────

init_db()

# ── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## Wine Cellar")
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:0.65rem;letter-spacing:0.2em;text-transform:uppercase;color:rgba(240,234,216,0.25);margin-bottom:0.5rem;">Navigation</p>', unsafe_allow_html=True)
    page = st.radio(
        "",
        ["My Cellar", "Add a Bottle", "Edit a Bottle", "Ready to Drink", "Food Pairings", "Recommendations"],
        label_visibility="collapsed"
    )
    st.markdown('<div class="sidebar-divider" style="margin-top:2rem;"></div>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:0.62rem;letter-spacing:0.1em;color:rgba(240,234,216,0.2);margin-top:1rem;">Powered by Claude</p>', unsafe_allow_html=True)


# ── PAGE: My Cellar ───────────────────────────────────────────────────────────

if page == "My Cellar":
    st.markdown("# My Cellar")
    st.markdown('<div class="page-subtitle">Collection Overview</div>', unsafe_allow_html=True)

    df = get_bottles()
    current_year = datetime.datetime.now().year

    if df.empty:
        st.info("Your cellar is empty. Add your first bottle to begin building your collection.")
    else:
        total_bottles = df["quantity"].sum()
        unique_wines = len(df)
        ready = df[(df["drink_from"] <= current_year) & (df["drink_by"] >= current_year)]
        avg_rating = df["your_rating"].dropna().mean()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Bottles", int(total_bottles))
        col2.metric("Unique Wines", unique_wines)
        col3.metric("Ready to Drink", len(ready))
        col4.metric("Avg Rating", f"{avg_rating:.1f}" if not pd.isna(avg_rating) else "—")

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

        st.caption(f"{len(filtered)} of {unique_wines} wines")
        st.divider()

        render_wine_table(filtered, current_year)


# ── PAGE: Add a Bottle ────────────────────────────────────────────────────────

elif page == "Add a Bottle":
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
                lines = result.strip().split("\n")
                for line in lines:
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
        add_bottle(winery, wine_name, region, appellation, varietal, vintage, quantity, drink_from, drink_by, your_notes, your_rating, expert_notes)
        for key in ["drink_from", "drink_by", "expert_notes"]:
            if key in st.session_state:
                del st.session_state[key]
        st.success(f"{vintage if vintage else 'NV'} {winery} {wine_name} added to your cellar.")


# ── PAGE: Edit a Bottle ───────────────────────────────────────────────────────

elif page == "Edit a Bottle":
    st.markdown("# Edit a Bottle")
    st.markdown('<div class="page-subtitle">Update your records</div>', unsafe_allow_html=True)

    if not require_auth():
        st.stop()

    df = get_bottles()
    if df.empty:
        st.info("No bottles in your cellar yet.")
    else:
        def format_bottle_label(row):
            vintage_str = "NV" if pd.isna(row['vintage']) else str(int(row['vintage']))
            wine_name_str = f" {row['wine_name']}" if row['wine_name'] and not pd.isna(row['wine_name']) else ""
            appellation_str = f" {row['appellation']}" if row['appellation'] and not pd.isna(row['appellation']) else ""
            varietal_str = f" {row['varietal']}" if row['varietal'] and not pd.isna(row['varietal']) else ""
            return f"{vintage_str} {row['winery']}{wine_name_str}{appellation_str}{varietal_str}"

        bottle_options = {format_bottle_label(row): int(row['id']) for _, row in df.iterrows()}
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
            vintage = None if no_vintage else st.number_input("Vintage", min_value=1900, max_value=2100, value=int(bottle["vintage"]) if not pd.isna(bottle["vintage"]) else 2020)
        with col2:
            wine_name = st.text_input("Wine Name", value=str(bottle["wine_name"] or ""))
            appellation = st.text_input("Appellation", value=str(bottle["appellation"] or ""))
            quantity = st.number_input("Bottles in Cellar", min_value=0, value=int(bottle["quantity"]) if not pd.isna(bottle["quantity"]) else 0)

        col1, col2 = st.columns(2)
        with col1:
            drink_from = st.number_input("Drink From", min_value=1900, max_value=2100, value=int(bottle["drink_from"]) if not pd.isna(bottle["drink_from"]) else 2024)
        with col2:
            drink_by = st.number_input("Drink By", min_value=1900, max_value=2100, value=int(bottle["drink_by"]) if not pd.isna(bottle["drink_by"]) else 2030)

        expert_notes = st.text_area("Expert Tasting Notes", value=str(bottle["expert_notes"] or ""), height=100)

        st.markdown('<div class="section-label" style="margin-top:1rem;">Your Notes</div>', unsafe_allow_html=True)
        your_notes = st.text_area("Tasting Notes", value=str(bottle["your_notes"] or ""), height=100)
        not_tried = st.toggle("I haven't tried this wine yet", value=bottle["your_rating"] is None or pd.isna(bottle["your_rating"]))
        your_rating = None if not_tried else st.number_input("Your Rating (0–100)", min_value=0.0, max_value=100.0, value=float(bottle["your_rating"]) if not pd.isna(bottle["your_rating"]) else 90.0, step=0.5)

        st.markdown("")
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("Save Changes"):
                update_bottle(bottle_id, winery, wine_name, region, appellation, varietal, vintage, quantity, drink_from, drink_by, your_notes, your_rating, expert_notes)
                st.success("Bottle updated.")
        with col2:
            if st.button("Delete Bottle"):
                delete_bottle(bottle_id)
                st.warning("Deleted from your cellar.")


# ── PAGE: Ready to Drink ──────────────────────────────────────────────────────

elif page == "Ready to Drink":
    st.markdown("# Ready to Drink")
    st.markdown('<div class="page-subtitle">In their drinking window now</div>', unsafe_allow_html=True)

    current_year = datetime.datetime.now().year
    df = get_bottles()

    if df.empty:
        st.info("No bottles in your cellar yet.")
    else:
        ready = df[(df["drink_from"] <= current_year) & (df["drink_by"] >= current_year)]
        if ready.empty:
            st.info("Nothing is currently in its drinking window.")
        else:
            st.success(f"{len(ready)} bottle{'s' if len(ready) != 1 else ''} ready to drink right now.")
            st.divider()
            render_wine_table(ready, current_year)


# ── PAGE: Food Pairings ───────────────────────────────────────────────────────

elif page == "Food Pairings":
    st.markdown("# Food Pairings")
    st.markdown('<div class="page-subtitle">Sommelier recommendations</div>', unsafe_allow_html=True)

    df = get_bottles()
    if df.empty:
        st.info("No bottles in your cellar yet.")
    else:
        def format_bottle_label(row):
            vintage_str = "NV" if pd.isna(row['vintage']) else str(int(row['vintage']))
            wine_name_str = f" {row['wine_name']}" if row['wine_name'] and not pd.isna(row['wine_name']) else ""
            return f"{vintage_str} {row['winery']}{wine_name_str} — {row['varietal']}"

        bottle_options = {format_bottle_label(row): int(row['id']) for _, row in df.iterrows()}
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


# ── PAGE: Recommendations ─────────────────────────────────────────────────────

elif page == "Recommendations":
    st.markdown("# Recommendations")
    st.markdown('<div class="page-subtitle">Curated for your palate</div>', unsafe_allow_html=True)

    df = get_bottles()
    if df.empty:
        st.info("Add bottles and rate them to unlock personalized recommendations.")
    else:
        st.markdown('<p style="color:rgba(240,234,216,0.5);font-size:0.85rem;margin-bottom:1.5rem;">Based on your highest-rated bottles, our sommelier will suggest wines you\'re likely to love.</p>', unsafe_allow_html=True)
        if st.button("Generate Recommendations"):
            with st.spinner("Analyzing your taste profile..."):
                recommendation = get_recommendations(df)
            st.divider()
            st.markdown(recommendation)