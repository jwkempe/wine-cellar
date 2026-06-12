"""API surface tests with the database layer mocked out."""

import main
from tests.conftest import TEST_USER

SAMPLE_ROW = {
    "id": 1,
    "winery": "Ridge",
    "wine_name": "Monte Bello",
    "region": "Santa Cruz Mountains",
    "appellation": None,
    "varietal": "Cabernet Sauvignon",
    "vintage": 2018,
    "quantity": 3,
    "drink_from": 2026,
    "drink_by": 2040,
    "your_notes": None,
    "your_rating": 95.0,
    "expert_notes": None,
    "user_id": TEST_USER,
    "purchase_price": 120.0,
}


def test_unauthenticated_request_rejected(anon_client):
    assert anon_client.get("/bottles").status_code in (401, 403)


def test_list_bottles_filters_user_id(client, monkeypatch):
    monkeypatch.setattr(main, "get_bottles", lambda user_id: [dict(SAMPLE_ROW)])
    res = client.get("/bottles")
    assert res.status_code == 200
    [bottle] = res.json()
    assert bottle["winery"] == "Ridge"
    assert "user_id" not in bottle  # response model must not leak ownership ids


def test_create_bottle_passes_user(client, monkeypatch):
    calls = []
    monkeypatch.setattr(main, "add_bottle", lambda *a, **k: calls.append(a))
    res = client.post("/bottles", json={"winery": "Ridge", "region": "SCM", "varietal": "Cab"})
    assert res.status_code == 200
    assert calls and TEST_USER in calls[0]


def test_create_bottle_rejects_blank_winery(client):
    res = client.post("/bottles", json={"winery": "", "region": "SCM", "varietal": "Cab"})
    assert res.status_code == 422


def test_create_bottle_rejects_out_of_range_values(client):
    base = {"winery": "Ridge", "region": "SCM", "varietal": "Cab"}
    assert client.post("/bottles", json={**base, "quantity": -1}).status_code == 422
    assert client.post("/bottles", json={**base, "your_rating": 101}).status_code == 422
    assert client.post("/bottles", json={**base, "vintage": 20180}).status_code == 422


def test_drink_404_when_bottle_missing(client, monkeypatch):
    monkeypatch.setattr(main, "get_bottle", lambda *a: None)
    res = client.post("/bottles/1/drink", json={"quantity": 1, "consumed_on": "2026-06-09"})
    assert res.status_code == 404


def test_drink_400_when_insufficient_stock(client, monkeypatch):
    monkeypatch.setattr(main, "get_bottle", lambda *a: dict(SAMPLE_ROW))
    monkeypatch.setattr(main, "decrement_bottle", lambda *a: None)
    res = client.post("/bottles/1/drink", json={"quantity": 5, "consumed_on": "2026-06-09"})
    assert res.status_code == 400


def test_drink_logs_and_keeps_bottle_when_stock_remains(client, monkeypatch):
    logged, deleted = [], []
    monkeypatch.setattr(main, "get_bottle", lambda *a: dict(SAMPLE_ROW))
    monkeypatch.setattr(main, "decrement_bottle", lambda *a: 2)
    monkeypatch.setattr(main, "delete_bottle", lambda *a: deleted.append(a))
    monkeypatch.setattr(main, "log_consumption", lambda *a: logged.append(a))
    res = client.post("/bottles/1/drink", json={"quantity": 1, "consumed_on": "2026-06-09"})
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "remaining": 2}
    assert logged and not deleted


def test_drink_deletes_bottle_at_zero(client, monkeypatch):
    deleted = []
    monkeypatch.setattr(main, "get_bottle", lambda *a: dict(SAMPLE_ROW))
    monkeypatch.setattr(main, "decrement_bottle", lambda *a: 0)
    monkeypatch.setattr(main, "delete_bottle", lambda *a: deleted.append(a))
    monkeypatch.setattr(main, "log_consumption", lambda *a: None)
    res = client.post("/bottles/1/drink", json={"quantity": 3, "consumed_on": "2026-06-09"})
    assert res.status_code == 200
    assert deleted


def test_drink_rejects_zero_quantity(client):
    res = client.post("/bottles/1/drink", json={"quantity": 0, "consumed_on": "2026-06-09"})
    assert res.status_code == 422


def test_drink_passes_rating_to_log(client, monkeypatch):
    logged = []
    monkeypatch.setattr(main, "get_bottle", lambda *a: dict(SAMPLE_ROW))
    monkeypatch.setattr(main, "decrement_bottle", lambda *a: 2)
    monkeypatch.setattr(main, "log_consumption", lambda *a: logged.append(a))
    res = client.post("/bottles/1/drink",
                      json={"quantity": 1, "consumed_on": "2026-06-09", "rating": 93})
    assert res.status_code == 200
    assert logged[0][-1] == 93  # rating is the last positional arg


def test_edit_log_entry_updates(client, monkeypatch):
    captured = {}
    def fake_update(entry_id, user_id, consumed_on, quantity, notes, rating):
        captured.update(id=entry_id, user=user_id, rating=rating, notes=notes)
        return True
    monkeypatch.setattr(main, "update_log_entry", fake_update)
    res = client.put("/log/7", json={"quantity": 1, "consumed_on": "2026-06-09",
                                      "notes": "loved it", "rating": 95})
    assert res.status_code == 200
    assert captured == {"id": 7, "user": TEST_USER, "rating": 95.0, "notes": "loved it"}


def test_edit_log_entry_404_when_not_owned(client, monkeypatch):
    monkeypatch.setattr(main, "update_log_entry", lambda *a: False)
    res = client.put("/log/7", json={"quantity": 1, "consumed_on": "2026-06-09"})
    assert res.status_code == 404


def test_edit_log_entry_rejects_bad_rating(client):
    res = client.put("/log/7", json={"quantity": 1, "consumed_on": "2026-06-09", "rating": 150})
    assert res.status_code == 422


def test_delete_log_entry(client, monkeypatch):
    monkeypatch.setattr(main, "delete_log_entry", lambda eid, uid: True)
    assert client.delete("/log/7").status_code == 200
    monkeypatch.setattr(main, "delete_log_entry", lambda eid, uid: False)
    assert client.delete("/log/7").status_code == 404


def test_ai_rate_limit_trips(client, monkeypatch):
    main._ai_calls.clear()
    monkeypatch.setattr(main, "get_bottle", lambda *a: None)  # 404s, but each call counts
    for _ in range(main.AI_RATE_LIMIT_PER_MINUTE):
        assert client.get("/ai/pairing/1").status_code == 404
    assert client.get("/ai/pairing/1").status_code == 429
    main._ai_calls.clear()


def test_wine_lookup_502_on_failure(client, monkeypatch):
    main._ai_calls.clear()
    def boom(*a, **k):
        raise RuntimeError("anthropic call failed")
    monkeypatch.setattr(main, "lookup_wine_info", boom)
    res = client.get("/ai/lookup", params={"winery": "Ridge", "region": "SCM"})
    assert res.status_code == 502
    main._ai_calls.clear()


def test_value_lookup_returns_estimate(client, monkeypatch):
    main._ai_calls.clear()
    monkeypatch.setattr(
        main, "estimate_market_value",
        lambda *a, **k: {"value": 90.0, "basis": "auction comps"},
    )
    res = client.get("/ai/value-lookup", params={"winery": "Ridge", "region": "SCM"})
    assert res.status_code == 200
    assert res.json() == {"value": 90.0, "basis": "auction comps"}
    main._ai_calls.clear()


def test_value_lookup_502_on_failure(client, monkeypatch):
    main._ai_calls.clear()
    def boom(*a, **k):
        raise RuntimeError("web search unavailable")
    monkeypatch.setattr(main, "estimate_market_value", boom)
    res = client.get("/ai/value-lookup", params={"winery": "Ridge", "region": "SCM"})
    assert res.status_code == 502
    main._ai_calls.clear()


def test_estimate_cellar_only_prices_unvalued_and_persists(client, monkeypatch):
    main._ai_calls.clear()
    bottles = [
        {**SAMPLE_ROW, "id": 1, "market_value": None},
        {**SAMPLE_ROW, "id": 2, "market_value": 75.0},  # already valued — skipped
    ]
    saved = []
    monkeypatch.setattr(main, "get_bottles", lambda user_id: [dict(b) for b in bottles])
    monkeypatch.setattr(main, "estimate_market_value", lambda *a, **k: {"value": 120.0, "basis": "x"})
    monkeypatch.setattr(main, "set_market_value", lambda bid, uid, val: saved.append((bid, val)))

    res = client.post("/ai/estimate-cellar")
    assert res.status_code == 200
    assert "id" in res.text and "valued" in res.text  # streamed events + done summary
    assert saved == [(1, 120.0)]  # only the unvalued bottle was priced and saved
    main._ai_calls.clear()


def test_sse_framing_and_error_event():
    frames = list(main._sse_events(iter(["Hello", " world\n", ""])))
    assert frames == ['data: "Hello"\n\n', 'data: " world\\n"\n\n']

    def boom():
        yield "partial"
        raise RuntimeError("api fell over")

    frames = list(main._sse_events(boom()))
    assert frames[0] == 'data: "partial"\n\n'
    assert frames[1].startswith("event: error\n")
