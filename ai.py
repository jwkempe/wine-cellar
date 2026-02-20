import anthropic
import os

from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


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

    bottle_list = "\n".join([
        f"- {row['vintage']} {row['winery']} {row['varietal']} from {row['region']} (rated {row['your_rating']})"
        for _, row in top_bottles.iterrows()
    ])

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