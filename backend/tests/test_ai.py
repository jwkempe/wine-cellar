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
