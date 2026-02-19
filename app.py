import streamlit as st
import sqlite3
import pandas as pd
import anthropic
import datetime
from dotenv import load_dotenv
import os

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

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

/* Sidebar radio nav */
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

[data-testid="stSidebar"] .stRadio [aria-checked="true"] ~ div,
[data-testid="stSidebar"] .stRadio input:checked + div {
    color: var(--gold) !important;
}

/* Radio button circles */
[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] div:first-child {
    border-color: var(--border) !important;
    background: transparent !important;
}

/* ── Main content area ── */
.main .block-container {
    padding: 2.5rem 3rem 4rem !important;
    max-width: 1300px !important;
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

/* Primary action button (first button on page) */
.stButton > button[kind="primary"] {
    background: var(--gold) !important;
    color: var(--bg-primary) !important;
}

/* ── Inputs ── */
.stTextInput input,
.stNumberInput input,
.stTextArea textarea,
.stSelectbox select {
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
[data-baseweb="select"] {
    background-color: var(--bg-card) !important;
    border-color: var(--border) !important;
}

[data-baseweb="select"] > div {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 2px !important;
    color: var(--text-primary) !important;
}

[data-baseweb="select"] > div:hover {
    border-color: var(--gold) !important;
}

/* Dropdown menu */
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

/* ── Checkboxes ── */
.stCheckbox [data-baseweb="checkbox"] {
    background: transparent !important;
}

.stCheckbox [data-baseweb="checkbox"] span {
    border-color: var(--border) !important;
    background: transparent !important;
}

/* ── Divider ── */
hr {
    border-color: var(--border) !important;
    margin: 1.5rem 0 !important;
}

/* ── DataTable ── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 2px !important;
}

[data-testid="stDataFrame"] thead th {
    background-color: var(--bg-secondary) !important;
    color: var(--text-muted) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.68rem !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    border-bottom: 1px solid var(--border) !important;
}

[data-testid="stDataFrame"] tbody tr {
    background-color: var(--bg-card) !important;
    border-bottom: 1px solid var(--border-subtle) !important;
    transition: background-color 0.15s !important;
}

[data-testid="stDataFrame"] tbody tr:hover {
    background-color: var(--bg-card-hover) !important;
}

[data-testid="stDataFrame"] tbody td {
    color: var(--text-primary) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
}

/* ── Alert / info boxes ── */
.stAlert {
    border-radius: 2px !important;
    border-left-width: 2px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
}

[data-testid="stAlert"][data-alert-type="info"] {
    background-color: rgba(201, 168, 76, 0.06) !important;
    border-color: var(--gold) !important;
    color: var(--text-secondary) !important;
}

[data-testid="stAlert"][data-alert-type="success"] {
    background-color: rgba(90, 138, 90, 0.1) !important;
    border-color: var(--success) !important;
    color: var(--text-secondary) !important;
}

[data-testid="stAlert"][data-alert-type="warning"] {
    background-color: rgba(160, 120, 64, 0.1) !important;
    border-color: var(--warning) !important;
}

/* ── Spinner ── */
.stSpinner > div {
    border-top-color: var(--gold) !important;
}

/* ── Caption / small text ── */
.stCaption, caption, small {
    font-family: 'DM Sans', sans-serif !important;
    color: var(--text-muted) !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.05em !important;
}

/* ── Markdown text body ── */
.stMarkdown p {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.9rem !important;
    line-height: 1.7 !important;
    color: var(--text-secondary) !important;
}

/* ── Page subtitle / ornament ── */
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

/* ── Section header ── */
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

/* ── Scrollbar ── */
::-webkit-scrollbar {
    width: 4px;
    height: 4px;
}
::-webkit-scrollbar-track {
    background: var(--bg-secondary);
}
::-webkit-scrollbar-thumb {
    background: var(--border);
    border-radius: 2px;
}
::-webkit-scrollbar-thumb:hover {
    background: var(--gold);
}

/* ── Number input arrows ── */
.stNumberInput [data-baseweb="input"] {
    background: var(--bg-card) !important;
    border-color: var(--border) !important;
}

/* ── Streamlit top header hide ── */
header[data-testid="stHeader"] {
    background: transparent !important;
    border-bottom: none !important;
}

/* ── Footer hide ── */
footer {
    display: none !important;
}

/* ── Main menu hide ── */
#MainMenu {
    display: none !important;
}

/* ── Tooltip ── */
[data-baseweb="tooltip"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
}

/* ── Sidebar nav divider ── */
.sidebar-divider {
    width: 100%;
    height: 1px;
    background: var(--border);
    margin: 1rem 0;
}

/* ── Progress bar (rating column) ── */
.stDataFrame [data-progress] {
    background: var(--gold-dim) !important;
}
.stDataFrame [data-progress] > div {
    background: var(--gold) !important;
}
</style>
""", unsafe_allow_html=True)


# ── Database setup ──────────────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect("cellar.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS bottles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    conn = sqlite3.connect("cellar.db")
    c = conn.cursor()
    c.execute('''
        INSERT INTO bottles (winery, wine_name, region, appellation, varietal, vintage, quantity, drink_from, drink_by, your_notes, your_rating, expert_notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (winery, wine_name, region, appellation, varietal, vintage, quantity, drink_from, drink_by, your_notes, your_rating, expert_notes))
    conn.commit()
    conn.close()

def get_bottles():
    conn = sqlite3.connect("cellar.db")
    df = pd.read_sql_query("SELECT * FROM bottles", conn)
    conn.close()
    return df

def update_bottle(id, winery, wine_name, region, appellation, varietal, vintage, quantity, drink_from, drink_by, your_notes, your_rating, expert_notes):
    conn = sqlite3.connect("cellar.db")
    c = conn.cursor()
    c.execute('''
        UPDATE bottles SET
            winery=?, wine_name=?, region=?, appellation=?, varietal=?, vintage=?,
            quantity=?, drink_from=?, drink_by=?, your_notes=?,
            your_rating=?, expert_notes=?
        WHERE id=?
    ''', (winery, wine_name, region, appellation, varietal, vintage, quantity, drink_from, drink_by, your_notes, your_rating, expert_notes, id))
    conn.commit()
    conn.close()

def delete_bottle(id):
    conn = sqlite3.connect("cellar.db")
    c = conn.cursor()
    c.execute("DELETE FROM bottles WHERE id=?", (id,))
    conn.commit()
    conn.close()


# ── AI functions ─────────────────────────────────────────────────────────────

def get_pairing_suggestion(winery, varietal, region, vintage, your_notes, expert_notes):
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": f"""You are a world-class sommelier. Suggest food pairings for this wine:

Winery: {winery}
Varietal: {varietal}
Region: {region}
Vintage: {vintage}
Tasting Notes: {your_notes or expert_notes}

Give 3-5 specific food pairing suggestions with a brief explanation for each. Be concise."""}
        ]
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
        messages=[
            {"role": "user", "content": f"""You are a world-class sommelier. Based on these wines a collector has rated highly:

{bottle_list}

Suggest 5 specific wines they might enjoy that aren't already in their list. Include winery, varietal, region, and why they'd enjoy it based on their taste profile. Be specific and concise."""}
        ]
    )
    return message.content[0].text

def lookup_wine_info(winery, varietal, region, vintage, appellation=None):
    vintage_str = "Non-Vintage (NV)" if not vintage else str(int(vintage))
    appellation_str = appellation if appellation else "Not specified"

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": f"""You are a world-class sommelier and wine expert. For this wine:

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
EXPERT_NOTES: [notes]"""}
        ]
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

    if df.empty:
        st.info("Your cellar is empty. Add your first bottle to begin building your collection.")
    else:
        current_year = datetime.datetime.now().year
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

        display = filtered.drop(columns=["id"]).rename(columns={
            "winery": "Winery",
            "wine_name": "Wine Name",
            "region": "Region",
            "appellation": "Appellation",
            "varietal": "Varietal",
            "vintage": "Vintage",
            "quantity": "Qty",
            "drink_from": "Drink From",
            "drink_by": "Drink By",
            "your_notes": "Your Notes",
            "your_rating": "Rating",
            "expert_notes": "Expert Notes"
        })

        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Rating": st.column_config.ProgressColumn(
                    "Rating",
                    min_value=0,
                    max_value=100,
                    format="%.0f"
                ),
                "Vintage": st.column_config.NumberColumn("Vintage", format="%d"),
                "Drink From": st.column_config.NumberColumn("Drink From", format="%d"),
                "Drink By": st.column_config.NumberColumn("Drink By", format="%d"),
            }
        )


# ── PAGE: Add a Bottle ────────────────────────────────────────────────────────

elif page == "Add a Bottle":
    st.markdown("# Add a Bottle")
    st.markdown('<div class="page-subtitle">Catalog a new wine</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        winery = st.text_input("Winery")
        region = st.text_input("Region", placeholder="e.g. Burgundy, Napa Valley")
        varietal = st.text_input("Varietal", placeholder="e.g. Pinot Noir, Cabernet Sauvignon")
        no_vintage = st.checkbox("Non-Vintage (NV)")
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
    not_tried = st.checkbox("I haven't tried this wine yet")
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

        bottle_options = {format_bottle_label(row): row['id'] for _, row in df.iterrows()}
        selected = st.selectbox("Select a bottle", list(bottle_options.keys()))
        bottle_id = bottle_options[selected]
        bottle = df[df["id"] == bottle_id].iloc[0]

        st.markdown('<div class="section-label" style="margin-top:1.5rem;">Wine Details</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            winery = st.text_input("Winery", value=bottle["winery"])
            region = st.text_input("Region", value=bottle["region"])
            varietal = st.text_input("Varietal", value=bottle["varietal"])
            no_vintage = st.checkbox("Non-Vintage (NV)", value=bottle["vintage"] is None or pd.isna(bottle["vintage"]))
            vintage = None if no_vintage else st.number_input("Vintage", min_value=1900, max_value=2100, value=int(bottle["vintage"]) if not pd.isna(bottle["vintage"]) else 2020)
        with col2:
            wine_name = st.text_input("Wine Name", value=str(bottle["wine_name"] or ""))
            appellation = st.text_input("Appellation", value=str(bottle["appellation"] or ""))
            quantity = st.number_input("Bottles in Cellar", min_value=0, value=int(bottle["quantity"]))

        col1, col2 = st.columns(2)
        with col1:
            drink_from = st.number_input("Drink From", min_value=1900, max_value=2100, value=int(bottle["drink_from"]))
        with col2:
            drink_by = st.number_input("Drink By", min_value=1900, max_value=2100, value=int(bottle["drink_by"]))

        expert_notes = st.text_area("Expert Tasting Notes", value=str(bottle["expert_notes"] or ""), height=100)

        st.markdown('<div class="section-label" style="margin-top:1rem;">Your Notes</div>', unsafe_allow_html=True)
        your_notes = st.text_area("Tasting Notes", value=str(bottle["your_notes"] or ""), height=100)
        not_tried = st.checkbox("I haven't tried this wine yet", value=bottle["your_rating"] is None or pd.isna(bottle["your_rating"]))
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
                st.warning(f"Deleted from your cellar.")


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

            display = ready.drop(columns=["id"]).rename(columns={
                "winery": "Winery",
                "wine_name": "Wine Name",
                "region": "Region",
                "appellation": "Appellation",
                "varietal": "Varietal",
                "vintage": "Vintage",
                "quantity": "Qty",
                "drink_from": "Drink From",
                "drink_by": "Drink By",
                "your_notes": "Your Notes",
                "your_rating": "Rating",
                "expert_notes": "Expert Notes"
            })

            st.dataframe(
                display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Rating": st.column_config.ProgressColumn(
                        "Rating",
                        min_value=0,
                        max_value=100,
                        format="%.0f"
                    ),
                    "Vintage": st.column_config.NumberColumn("Vintage", format="%d"),
                    "Drink From": st.column_config.NumberColumn("Drink From", format="%d"),
                    "Drink By": st.column_config.NumberColumn("Drink By", format="%d"),
                }
            )


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

        bottle_options = {format_bottle_label(row): row['id'] for _, row in df.iterrows()}
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