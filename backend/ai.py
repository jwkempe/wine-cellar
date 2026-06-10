import logging
import os
from typing import Any, Iterator

import anthropic

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

# Overridable so a model bump is a config change, not a deploy.
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-4-8")

# Pulling a price out of search results is a cheap extraction task, so it runs
# on a small fast model by default.
VALUE_MODEL = os.getenv("ANTHROPIC_VALUE_MODEL", "claude-haiku-4-5")

# Basic web search works on every model. web_search_20260209 adds dynamic
# filtering (Claude filters results with code before they reach context — more
# accurate, fewer tokens) but only on Opus 4.6+/Sonnet 4.6/Fable. We pick the
# best tool the value model supports and fall back to basic if it errors.
_WEB_SEARCH_BASIC = {"type": "web_search_20250305", "name": "web_search", "max_uses": 3}
_WEB_SEARCH_DYNAMIC = {"type": "web_search_20260209", "name": "web_search"}
_DYNAMIC_FILTER_MODELS = ("opus-4-6", "opus-4-7", "opus-4-8", "sonnet-4-6", "fable-5")


def _value_search_tool(model: str) -> dict:
    if any(tag in model for tag in _DYNAMIC_FILTER_MODELS):
        return _WEB_SEARCH_DYNAMIC
    return _WEB_SEARCH_BASIC

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def _complete(prompt: str, max_tokens: int = 1024) -> str:
    """Send a single-turn prompt to Claude and return the full text response."""
    message = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def _stream(prompt: str, max_tokens: int = 1024) -> Iterator[str]:
    """Stream a single-turn prompt to Claude, yielding text deltas as they arrive."""
    with client.messages.stream(
        model=MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        yield from stream.text_stream


# ── Prompt builders ─────────────────────────────────────────────────────────

def _pairing_prompt(winery, varietal, region, vintage, your_notes, expert_notes) -> str:
    return f"""You are a world-class sommelier. Suggest food pairings for this wine:

Winery: {winery}
Varietal: {varietal}
Region: {region}
Vintage: {vintage}
Tasting Notes: {your_notes or expert_notes}

Give 3-5 specific food pairing suggestions with a brief explanation for each. Be concise."""


def _recommendations_prompt(bottles: list[dict[str, Any]]) -> str | None:
    """Build the recommendations prompt, or None if there's nothing to base it on."""
    rated = [b for b in bottles if b.get("your_rating") is not None]
    if not rated:
        return None

    top = sorted(rated, key=lambda b: b["your_rating"], reverse=True)
    highly_rated = [b for b in top if b["your_rating"] >= 90][:5] or top[:5]

    bottle_list = "\n".join(
        f"- {b.get('vintage')} {b['winery']} {b['varietal']} from {b['region']} "
        f"(rated {b['your_rating']})"
        for b in highly_rated
    )

    return f"""You are a world-class sommelier. Based on these wines a collector has rated highly:

{bottle_list}

Suggest 5 specific wines they might enjoy that aren't already in their list. Include winery, varietal, region, and why they'd enjoy it based on their taste profile. Be specific and concise."""


def _meal_prompt(meal: str, bottles: list[dict[str, Any]]) -> str:
    def describe(b: dict[str, Any]) -> str:
        vintage = "" if b.get("vintage") is None else str(b["vintage"])
        name = f" {b['wine_name']}" if b.get("wine_name") else ""
        return f"- ID {b['id']}: {vintage} {b['winery']}{name} — {b['varietal']}, {b['region']}"

    bottle_list = "\n".join(describe(b) for b in bottles)

    return f"""You are a world-class sommelier. A collector is having this meal:

{meal}

Here are the bottles currently in their cellar:
{bottle_list}

Respond in exactly two sections separated by "---GAPS---":

SECTION 1 (before ---GAPS---): Recommend the 3 best bottles from the list for the meal. For each, explain briefly why it pairs well. If fewer than 3 are a good match, say so honestly. If nothing is a great fit, say so clearly.

SECTION 2 (after ---GAPS---): Identify 1-3 wine styles or specific bottles NOT in the cellar that would be ideal for this meal. Be specific (e.g. "white Burgundy" or "Sancerre" rather than just "white wine"). If the cellar already has excellent options, say so and keep this section brief. Be concise throughout."""


def _lookup_prompt(winery, region, wine_name, varietal, vintage, appellation) -> str:
    vintage_str = "Non-Vintage (NV)" if not vintage else str(int(vintage))
    appellation_str = appellation if appellation else "Not specified"
    varietal_str = varietal if varietal else "Blend / Not specified"
    wine_name_str = wine_name if wine_name else "Not specified"

    return f"""You are a world-class sommelier and wine expert. For this wine:

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
EXPERT_NOTES: [notes]"""


# ── Streaming sommelier responses (free-text features) ───────────────────────

def stream_pairing(winery, varietal, region, vintage, your_notes, expert_notes) -> Iterator[str]:
    yield from _stream(_pairing_prompt(winery, varietal, region, vintage, your_notes, expert_notes))


def stream_recommendations(bottles: list[dict[str, Any]]) -> Iterator[str]:
    prompt = _recommendations_prompt(bottles)
    if prompt is None:
        yield "Add some bottles and ratings to get personalized recommendations."
        return
    yield from _stream(prompt)


def stream_wine_for_meal(meal: str, bottles: list[dict[str, Any]]) -> Iterator[str]:
    if not bottles:
        yield "No bottles in your cellar yet."
        return
    yield from _stream(_meal_prompt(meal, bottles), max_tokens=1536)


# ── Non-streaming lookup (structured response parsed into form fields) ────────

def lookup_wine_info(winery, region, wine_name=None, varietal=None, vintage=None, appellation=None) -> str:
    return _complete(_lookup_prompt(winery, region, wine_name, varietal, vintage, appellation))


# ── Market value estimation (web-search grounded) ────────────────────────────

def _value_prompt(winery, region, wine_name, varietal, vintage, appellation) -> str:
    vintage_str = "Non-Vintage (NV)" if not vintage else str(int(vintage))
    name = f" {wine_name}" if wine_name else ""
    extra = f", {appellation}" if appellation else ""
    return f"""You are a wine market analyst. Search the web for the current fair market value of this specific wine and give a single best estimate of its price per 750ml bottle in US dollars.

Wine: {vintage_str} {winery}{name} — {varietal or 'unknown varietal'}, {region}{extra}

Base the estimate on current retail and auction listings (e.g. Wine-Searcher, wine retailers, recent auction results). If the exact vintage isn't listed, use the nearest comparable vintage. If you genuinely cannot find enough information to estimate, answer NONE.

Respond in exactly this format and nothing else:
ESTIMATED_VALUE: <number only, no symbols or commas, e.g. 85 — or NONE>
BASIS: <one short sentence on what the figure is based on>"""


def _parse_value(text: str) -> dict:
    value: float | None = None
    basis = ""
    for line in text.splitlines():
        s = line.strip()
        upper = s.upper()
        if upper.startswith("ESTIMATED_VALUE:"):
            raw = s.split(":", 1)[1].strip().replace("$", "").replace(",", "")
            try:
                parsed = round(float(raw), 2)
                value = parsed if parsed > 0 else None
            except ValueError:
                value = None
        elif upper.startswith("BASIS:"):
            basis = s.split(":", 1)[1].strip()
    return {"value": value, "basis": basis}


def _run_valuation(prompt: str, tool: dict) -> dict:
    messages: list[dict[str, Any]] = [{"role": "user", "content": prompt}]
    resp = None
    # Server-side web search may need several turns; pause_turn means "resume".
    for _ in range(4):
        resp = client.messages.create(
            model=VALUE_MODEL,
            max_tokens=2048,
            tools=[tool],
            messages=messages,
        )
        if resp.stop_reason != "pause_turn":
            break
        messages.append({"role": "assistant", "content": resp.content})

    text = "".join(
        b.text for b in resp.content if getattr(b, "type", None) == "text"
    ) if resp else ""
    return _parse_value(text)


def estimate_market_value(winery, region, wine_name=None, varietal=None,
                          vintage=None, appellation=None) -> dict:
    """Estimate a bottle's current market value, grounded in web search.

    Uses the dynamic-filtering web search tool when VALUE_MODEL supports it,
    falling back to the basic tool if that call fails (e.g. dynamic filtering
    isn't enabled for the org). Returns {"value": float|None, "basis": str};
    value is None when Claude can't find enough data.
    """
    prompt = _value_prompt(winery, region, wine_name, varietal, vintage, appellation)
    tool = _value_search_tool(VALUE_MODEL)
    try:
        return _run_valuation(prompt, tool)
    except Exception:
        if tool["type"] == _WEB_SEARCH_BASIC["type"]:
            raise  # already the basic tool — nothing simpler to fall back to
        logger.warning(
            "Dynamic-filter web search failed; retrying with basic search", exc_info=True
        )
        return _run_valuation(prompt, _WEB_SEARCH_BASIC)
