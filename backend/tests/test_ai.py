"""Prompt builders and no-API short circuits (nothing here calls Anthropic)."""

import ai

RATED = [
    {"id": 1, "winery": "Ridge", "varietal": "Cab", "region": "SCM",
     "vintage": 2018, "your_rating": 95.0, "wine_name": "Monte Bello"},
    {"id": 2, "winery": "Unrated", "varietal": "Merlot", "region": "Napa",
     "vintage": 2020, "your_rating": None, "wine_name": None},
]


def test_recommendations_prompt_none_without_ratings():
    assert ai._recommendations_prompt([{"your_rating": None}]) is None


def test_recommendations_prompt_includes_rated_bottles():
    prompt = ai._recommendations_prompt(RATED)
    assert "Ridge" in prompt and "rated 95.0" in prompt
    assert "Unrated" not in prompt  # unrated bottles don't shape the taste profile


def test_stream_recommendations_short_circuits_without_ratings():
    chunks = list(ai.stream_recommendations([{"your_rating": None}]))
    assert chunks == ["Add some bottles and ratings to get personalized recommendations."]


def test_stream_meal_short_circuits_with_empty_cellar():
    assert list(ai.stream_wine_for_meal("steak", [])) == ["No bottles in your cellar yet."]


def test_meal_prompt_lists_bottles_with_ids():
    prompt = ai._meal_prompt("steak frites", RATED)
    assert "steak frites" in prompt
    assert "ID 1" in prompt and "Monte Bello" in prompt
    assert "---GAPS---" in prompt


def test_lookup_prompt_handles_non_vintage():
    prompt = ai._lookup_prompt("Krug", "Champagne", None, None, None, None)
    assert "Non-Vintage (NV)" in prompt
    assert "Blend / Not specified" in prompt


def test_parse_value_extracts_number_and_basis():
    out = ai._parse_value("ESTIMATED_VALUE: 85\nBASIS: Based on Wine-Searcher listings.")
    assert out == {"value": 85.0, "basis": "Based on Wine-Searcher listings."}


def test_parse_value_strips_currency_formatting():
    assert ai._parse_value("ESTIMATED_VALUE: $1,250.50")["value"] == 1250.50


def test_parse_value_none_when_unknown_or_zero():
    assert ai._parse_value("ESTIMATED_VALUE: NONE\nBASIS: no data")["value"] is None
    assert ai._parse_value("ESTIMATED_VALUE: 0")["value"] is None
    assert ai._parse_value("nothing useful here")["value"] is None


def test_value_search_tool_picks_dynamic_for_capable_models():
    assert ai._value_search_tool("claude-sonnet-4-6")["type"] == "web_search_20260209"
    assert ai._value_search_tool("claude-opus-4-8")["type"] == "web_search_20260209"
    assert ai._value_search_tool("claude-fable-5")["type"] == "web_search_20260209"
    # Haiku (and anything unrecognized) gets the basic tool.
    assert ai._value_search_tool("claude-haiku-4-5")["type"] == "web_search_20250305"


class _FakeBlock:
    type = "text"
    def __init__(self, text):
        self.text = text


class _FakeMsg:
    stop_reason = "end_turn"
    def __init__(self, text):
        self.content = [_FakeBlock(text)]


class _FakeMessages:
    def __init__(self):
        self.tool_types = []

    def create(self, *, model, max_tokens, tools, messages):
        self.tool_types.append(tools[0]["type"])
        if tools[0]["type"] == "web_search_20260209":
            raise RuntimeError("dynamic filtering not enabled for org")
        return _FakeMsg("ESTIMATED_VALUE: 50\nBASIS: basic web search")


class _FakeClient:
    def __init__(self):
        self.messages = _FakeMessages()


def test_estimate_falls_back_to_basic_when_dynamic_fails(monkeypatch):
    fake = _FakeClient()
    monkeypatch.setattr(ai, "client", fake)
    monkeypatch.setattr(ai, "VALUE_MODEL", "claude-sonnet-4-6")
    out = ai.estimate_market_value("Ridge", "Santa Cruz Mountains")
    assert out["value"] == 50.0
    # Tried dynamic first, then fell back to the basic tool.
    assert fake.messages.tool_types == ["web_search_20260209", "web_search_20250305"]
