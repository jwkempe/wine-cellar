import os
from typing import Any

import anthropic

from dotenv import load_dotenv
load_dotenv()

MODEL = "claude-opus-4-8"

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def _complete(prompt: str, max_tokens: int = 1024) -> str:
    """Send a single-turn prompt to Claude and return the text response."""
    message = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def get_pairing_suggestion(winery, varietal, region, vintage, your_notes, expert_notes):
    return _complete(f"""You are a world-class sommelier. Suggest food pairings for this wine:

Winery: {winery}
Varietal: {varietal}
Region: {region}
Vintage: {vintage}
Tasting Notes: {your_notes or expert_notes}

Give 3-5 specific food pairing suggestions with a brief explanation for each. Be concise.""")


def get_recommendations(bottles: list[dict[str, Any]]) -> str:
    rated = [b for b in bottles if b.get("your_rating") is not None]
    if not rated:
        return "Add some bottles and ratings to get personalized recommendations."

    top = sorted(rated, key=lambda b: b["your_rating"], reverse=True)
    highly_rated = [b for b in top if b["your_rating"] >= 90][:5] or top[:5]

    bottle_list = "\n".join(
        f"- {b.get('vintage')} {b['winery']} {b['varietal']} from {b['region']} "
        f"(rated {b['your_rating']})"
        for b in highly_rated
    )

    return _complete(f"""You are a world-class sommelier. Based on these wines a collector has rated highly:

{bottle_list}

Suggest 5 specific wines they might enjoy that aren't already in their list. Include winery, varietal, region, and why they'd enjoy it based on their taste profile. Be specific and concise.""")


def get_wine_for_meal(meal: str, bottles: list[dict[str, Any]]) -> dict:
    if not bottles:
        return {"pairings": "No bottles in your cellar yet.", "gaps": None}

    def describe(b: dict[str, Any]) -> str:
        vintage = "" if b.get("vintage") is None else str(b["vintage"])
        name = f" {b['wine_name']}" if b.get("wine_name") else ""
        return f"- ID {b['id']}: {vintage} {b['winery']}{name} — {b['varietal']}, {b['region']}"

    bottle_list = "\n".join(describe(b) for b in bottles)

    text = _complete(f"""You are a world-class sommelier. A collector is having this meal:

{meal}

Here are the bottles currently in their cellar:
{bottle_list}

Respond in exactly two sections separated by "---GAPS---":

SECTION 1 (before ---GAPS---): Recommend the 3 best bottles from the list for the meal. For each, explain briefly why it pairs well. If fewer than 3 are a good match, say so honestly. If nothing is a great fit, say so clearly.

SECTION 2 (after ---GAPS---): Identify 1-3 wine styles or specific bottles NOT in the cellar that would be ideal for this meal. Be specific (e.g. "white Burgundy" or "Sancerre" rather than just "white wine"). If the cellar already has excellent options, say so and keep this section brief. Be concise throughout.""", max_tokens=1536)

    if "---GAPS---" in text:
        pairings, gaps = text.split("---GAPS---", 1)
        return {"pairings": pairings.strip(), "gaps": gaps.strip()}
    return {"pairings": text.strip(), "gaps": None}


def lookup_wine_info(winery, region, wine_name=None, varietal=None, vintage=None, appellation=None):
    vintage_str = "Non-Vintage (NV)" if not vintage else str(int(vintage))
    appellation_str = appellation if appellation else "Not specified"
    varietal_str = varietal if varietal else "Blend / Not specified"
    wine_name_str = wine_name if wine_name else "Not specified"

    return _complete(f"""You are a world-class sommelier and wine expert. For this wine:

Winery: {winery}
Wine Name: {wine_name_str}
Varietal: {varietal_str}
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
EXPERT_NOTES: [notes]""")
