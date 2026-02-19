import streamlit as st
import sqlite3
import pandas as pd
import anthropic
import datetime
from dotenv import load_dotenv
import os

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ── Database setup ──────────────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect("cellar.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS bottles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            winery TEXT,
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

def add_bottle(winery, region, appellation, varietal, vintage, quantity, drink_from, drink_by, your_notes, your_rating, expert_notes):
    conn = sqlite3.connect("cellar.db")
    c = conn.cursor()
    c.execute('''
        INSERT INTO bottles (winery, region, appellation, varietal, vintage, quantity, drink_from, drink_by, your_notes, your_rating, expert_notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (winery, region, appellation, varietal, vintage, quantity, drink_from, drink_by, your_notes, your_rating, expert_notes))
    conn.commit()
    conn.close()

def get_bottles():
    conn = sqlite3.connect("cellar.db")
    df = pd.read_sql_query("SELECT * FROM bottles", conn)
    conn.close()
    return df

def update_bottle(id, winery, region, appellation, varietal, vintage, quantity, drink_from, drink_by, your_notes, your_rating, expert_notes):
    conn = sqlite3.connect("cellar.db")
    c = conn.cursor()
    c.execute('''
        UPDATE bottles SET
            winery=?, region=?, appellation=?, varietal=?, vintage=?,
            quantity=?, drink_from=?, drink_by=?, your_notes=?,
            your_rating=?, expert_notes=?
        WHERE id=?
    ''', (winery, region, appellation, varietal, vintage, quantity, drink_from, drink_by, your_notes, your_rating, expert_notes, id))
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

def lookup_wine_info(winery, varietal, region, vintage):
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": f"""You are a world-class sommelier and wine expert. For this wine:

Winery: {winery}
Varietal: {varietal}
Region: {region}
Vintage: {vintage}

Please provide:
1. DRINK_FROM: The year this wine will start to peak (just the 4-digit year)
2. DRINK_BY: The year this wine should be consumed by (just the 4-digit year)
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

st.sidebar.title("🍷 Wine Cellar")
page = st.sidebar.radio("Navigate", ["My Cellar", "Add a Bottle", "Edit a Bottle", "Ready to Drink", "Food Pairings", "Recommendations"])

# --- PAGE: My Cellar ---
if page == "My Cellar":
    st.title("My Cellar")
    df = get_bottles()

    if df.empty:
        st.info("Your cellar is empty. Add some bottles to get started!")
    else:
        # ── Summary metrics ──────────────────────────────────────
        current_year = datetime.datetime.now().year
        total_bottles = df["quantity"].sum()
        unique_wines = len(df)
        ready = df[(df["drink_from"] <= current_year) & (df["drink_by"] >= current_year)]
        avg_rating = df["your_rating"].mean()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Bottles", int(total_bottles))
        col2.metric("Unique Wines", unique_wines)
        col3.metric("Ready to Drink", len(ready))
        col4.metric("Avg Rating", f"{avg_rating:.1f}")

        st.divider()

        # ── Filters ──────────────────────────────────────────────
        col1, col2 = st.columns(2)
        with col1:
            varietal_options = ["All"] + sorted(df["varietal"].dropna().unique().tolist())
            selected_varietal = st.selectbox("Filter by Varietal", varietal_options)
        with col2:
            region_options = ["All"] + sorted(df["region"].dropna().unique().tolist())
            selected_region = st.selectbox("Filter by Region", region_options)

        filtered = df.copy()
        if selected_varietal != "All":
            filtered = filtered[filtered["varietal"] == selected_varietal]
        if selected_region != "All":
            filtered = filtered[filtered["region"] == selected_region]

        st.caption(f"Showing {len(filtered)} of {unique_wines} wines")

        st.divider()

        # ── Clean table ──────────────────────────────────────────
        display = filtered.drop(columns=["id"]).rename(columns={
            "winery": "Winery",
            "region": "Region",
            "appellation": "Appellation",
            "varietal": "Varietal",
            "vintage": "Vintage",
            "quantity": "Qty",
            "drink_from": "Drink From",
            "drink_by": "Drink By",
            "your_notes": "Your Notes",
            "your_rating": "Your Rating",
            "expert_notes": "Expert Notes"
        })

        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Your Rating": st.column_config.ProgressColumn(
                    "Your Rating",
                    min_value=0,
                    max_value=100,
                    format="%.1f"
                ),
                "Vintage": st.column_config.NumberColumn("Vintage", format="%d"),
                "Drink From": st.column_config.NumberColumn("Drink From", format="%d"),
                "Drink By": st.column_config.NumberColumn("Drink By", format="%d"),
            }
        )

# --- PAGE: Add a Bottle ---
elif page == "Add a Bottle":
    st.title("Add a Bottle")

    winery = st.text_input("Winery")
    region = st.text_input("Region (e.g. Burgundy, Napa Valley)")
    appellation = st.text_input("Appellation (e.g. Pommard, Stags Leap District)")
    varietal = st.text_input("Varietal (e.g. Pinot Noir, Cabernet Sauvignon)")
    vintage = st.number_input("Vintage", min_value=1900, max_value=2100, value=2020)
    quantity = st.number_input("Bottles in Cellar", min_value=1, value=1)

    # AI Lookup
    if st.button("🔍 Lookup Drink Window & Tasting Notes"):
        if winery and varietal and region and vintage:
            with st.spinner("Looking up wine info..."):
                result = lookup_wine_info(winery, varietal, region, int(vintage))
                lines = result.strip().split("\n")
                for line in lines:
                    if line.startswith("DRINK_FROM:"):
                        st.session_state["drink_from"] = int(line.replace("DRINK_FROM:", "").strip())
                    elif line.startswith("DRINK_BY:"):
                        st.session_state["drink_by"] = int(line.replace("DRINK_BY:", "").strip())
                    elif line.startswith("EXPERT_NOTES:"):
                        st.session_state["expert_notes"] = line.replace("EXPERT_NOTES:", "").strip()
            st.success("Got it! Review the info below and adjust if needed.")
        else:
            st.warning("Please fill in Winery, Varietal, Region, and Vintage first.")

    drink_from = st.number_input("Drink From (year)", min_value=1900, max_value=2100, value=st.session_state.get("drink_from", 2024))
    drink_by = st.number_input("Drink By (year)", min_value=1900, max_value=2100, value=st.session_state.get("drink_by", 2030))
    your_notes = st.text_area("Your Tasting Notes")
    not_tried = st.checkbox("I haven't tried this wine yet")
    your_rating = None if not_tried else st.number_input("Your Rating (0-100)", min_value=0.0, max_value=100.0, value=90.0, step=0.5)
    expert_notes = st.text_area("Expert Tasting Notes", value=st.session_state.get("expert_notes", ""))

    if st.button("Add to Cellar"):
        add_bottle(winery, region, appellation, varietal, vintage, quantity, drink_from, drink_by, your_notes, your_rating, expert_notes)
        # Clear session state after adding
        for key in ["drink_from", "drink_by", "expert_notes"]:
            if key in st.session_state:
                del st.session_state[key]
        st.success(f"Added {vintage} {winery} to your cellar!")

# --- PAGE: Edit a Bottle ---
elif page == "Edit a Bottle":
    st.title("Edit a Bottle")
    df = get_bottles()
    if df.empty:
        st.info("No bottles in your cellar yet.")
    else:
        bottle_options = {f"{row['vintage']} {row['winery']} (ID: {row['id']})": row['id'] for _, row in df.iterrows()}
        selected = st.selectbox("Select a bottle to edit", list(bottle_options.keys()))
        bottle_id = bottle_options[selected]
        bottle = df[df["id"] == bottle_id].iloc[0]

        winery = st.text_input("Winery", value=bottle["winery"])
        region = st.text_input("Region", value=bottle["region"])
        appellation = st.text_input("Appellation", value=bottle["appellation"])
        varietal = st.text_input("Varietal", value=bottle["varietal"])
        vintage = st.number_input("Vintage", min_value=1900, max_value=2100, value=int(bottle["vintage"]))
        quantity = st.number_input("Bottles in Cellar", min_value=0, value=int(bottle["quantity"]))
        drink_from = st.number_input("Drink From (year)", min_value=1900, max_value=2100, value=int(bottle["drink_from"]))
        drink_by = st.number_input("Drink By (year)", min_value=1900, max_value=2100, value=int(bottle["drink_by"]))
        your_notes = st.text_area("Your Tasting Notes", value=str(bottle["your_notes"] or ""))
        not_tried = st.checkbox("I haven't tried this wine yet", value=bottle["your_rating"] is None or pd.isna(bottle["your_rating"]))
        your_rating = None if not_tried else st.number_input("Your Rating (0-100)", min_value=0.0, max_value=100.0, value=float(bottle["your_rating"]) if not pd.isna(bottle["your_rating"]) else 90.0, step=0.5)
        expert_notes = st.text_area("Expert Tasting Notes", value=str(bottle["expert_notes"] or ""))

        if st.button("Save Changes"):
            update_bottle(bottle_id, winery, region, appellation, varietal, vintage, quantity, drink_from, drink_by, your_notes, your_rating, expert_notes)
            st.success("Bottle updated!")

        if st.button("🗑️ Delete Bottle"):
            delete_bottle(bottle_id)
            st.warning(f"Deleted {bottle['vintage']} {bottle['winery']} from your cellar.")

# --- PAGE: Ready to Drink ---
elif page == "Ready to Drink":
    st.title("Ready to Drink")
    current_year = datetime.datetime.now().year
    df = get_bottles()
    if df.empty:
        st.info("No bottles in your cellar yet.")
    else:
        ready = df[(df["drink_from"] <= current_year) & (df["drink_by"] >= current_year)]
        if ready.empty:
            st.info("Nothing in its drinking window right now.")
        else:
            st.success(f"{len(ready)} bottle(s) ready to drink!")
            st.dataframe(ready)

# --- PAGE: Food Pairings ---
elif page == "Food Pairings":
    st.title("🍽️ Food Pairings")
    df = get_bottles()
    if df.empty:
        st.info("No bottles in your cellar yet.")
    else:
        bottle_options = {f"{row['vintage']} {row['winery']} (ID: {row['id']})": row['id'] for _, row in df.iterrows()}
        selected = st.selectbox("Select a bottle", list(bottle_options.keys()))
        bottle_id = bottle_options[selected]
        bottle = df[df["id"] == bottle_id].iloc[0]

        if st.button("Get Pairing Suggestions"):
            with st.spinner("Consulting the sommelier..."):
                suggestion = get_pairing_suggestion(
                    bottle["winery"], bottle["varietal"], bottle["region"],
                    bottle["vintage"], bottle["your_notes"], bottle["expert_notes"]
                )
            st.markdown(suggestion)

# --- PAGE: Recommendations ---
elif page == "Recommendations":
    st.title("🌟 Wine Recommendations")
    df = get_bottles()
    if st.button("Get Recommendations Based on My Cellar"):
        with st.spinner("Analyzing your taste profile..."):
            recommendation = get_recommendations(df)
        st.markdown(recommendation)