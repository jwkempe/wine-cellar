import json
import logging
import os
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import date
from typing import Iterator, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ai import (
    estimate_market_value, lookup_wine_info, stream_pairing,
    stream_recommendations, stream_wine_for_meal,
)
from auth import get_current_user
from database import (
    add_bottle, decrement_bottle, delete_bottle, get_bottle, get_bottles,
    get_consumption_log, init_db, log_consumption, set_market_value, update_bottle,
)

load_dotenv()

logger = logging.getLogger(__name__)

REQUIRED_ENV = ("DATABASE_URL", "ANTHROPIC_API_KEY", "CLERK_JWKS_URL")

# Comma-separated exact origins, plus a regex for Vercel deployments. The
# regex default is scoped to this project's deployments rather than all of
# *.vercel.app, so arbitrary Vercel-hosted sites can't make browser requests.
ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if o.strip()
]
ALLOWED_ORIGIN_REGEX = os.getenv(
    "ALLOWED_ORIGIN_REGEX", r"https://wine-cellar.*\.vercel\.app"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    missing = [k for k in REQUIRED_ENV if not os.getenv(k)]
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}"
        )
    init_db()
    yield


app = FastAPI(title="Wine Cellar API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=ALLOWED_ORIGIN_REGEX,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── AI rate limiting ──────────────────────────────────────────────────────────
# Every AI call costs real money, so cap per-user calls with a small in-memory
# sliding window. Per-process state is fine for a single-worker deployment; a
# multi-worker or multi-instance setup would need a shared store (e.g. Redis).

AI_RATE_LIMIT_PER_MINUTE = int(os.getenv("AI_RATE_LIMIT_PER_MINUTE", "20"))
_ai_calls: dict[str, deque[float]] = defaultdict(deque)

# Cap how many bottles a single bulk-valuation run will price, so one click
# can't fan out into hundreds of paid web searches. Users can re-run to
# continue through a large backlog.
BULK_VALUE_LIMIT = int(os.getenv("BULK_VALUE_LIMIT", "60"))


def rate_limited_user(user_id: str = Depends(get_current_user)) -> str:
    now = time.monotonic()
    calls = _ai_calls[user_id]
    while calls and now - calls[0] > 60:
        calls.popleft()
    if len(calls) >= AI_RATE_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=429,
            detail="Too many sommelier requests — please wait a minute and try again.",
        )
    calls.append(now)
    return user_id


# ── Data models ───────────────────────────────────────────────────────────────

class BottleIn(BaseModel):
    """Input schema: bounds keep garbage out of the database and AI prompts."""
    winery: str = Field(min_length=1, max_length=200)
    wine_name: Optional[str] = Field(default=None, max_length=200)
    region: str = Field(max_length=200)
    appellation: Optional[str] = Field(default=None, max_length=200)
    varietal: str = Field(max_length=200)
    vintage: Optional[int] = Field(default=None, ge=1800, le=2100)
    quantity: int = Field(default=1, ge=0, le=10000)
    drink_from: Optional[int] = Field(default=None, ge=1800, le=2200)
    drink_by: Optional[int] = Field(default=None, ge=1800, le=2200)
    your_notes: Optional[str] = Field(default=None, max_length=5000)
    your_rating: Optional[float] = Field(default=None, ge=0, le=100)
    expert_notes: Optional[str] = Field(default=None, max_length=5000)
    purchase_price: Optional[float] = Field(default=None, ge=0)
    market_value: Optional[float] = Field(default=None, ge=0)


class BottleOut(BaseModel):
    """Output schema: deliberately lenient (legacy rows may have empty/NULL
    fields) and excludes user_id from responses."""
    id: int
    winery: Optional[str] = None
    wine_name: Optional[str] = None
    region: Optional[str] = None
    appellation: Optional[str] = None
    varietal: Optional[str] = None
    vintage: Optional[int] = None
    quantity: Optional[int] = None
    drink_from: Optional[int] = None
    drink_by: Optional[int] = None
    your_notes: Optional[str] = None
    your_rating: Optional[float] = None
    expert_notes: Optional[str] = None
    purchase_price: Optional[float] = None
    market_value: Optional[float] = None
    market_value_updated: Optional[date] = None


class ValueEstimate(BaseModel):
    value: Optional[float] = None
    basis: str = ""


class DrinkEntry(BaseModel):
    quantity: int = Field(default=1, ge=1, le=10000)
    consumed_on: date
    notes: Optional[str] = Field(default=None, max_length=1000)


class DrinkResult(BaseModel):
    status: str
    remaining: int


class LogEntryOut(BaseModel):
    id: int
    bottle_id: Optional[int] = None
    winery: Optional[str] = None
    wine_name: Optional[str] = None
    vintage: Optional[int] = None
    varietal: Optional[str] = None
    region: Optional[str] = None
    quantity: Optional[int] = None
    consumed_on: Optional[date] = None
    notes: Optional[str] = None


class StatusOut(BaseModel):
    status: str


# ── Bottles ───────────────────────────────────────────────────────────────────

@app.get("/bottles", response_model=list[BottleOut])
def list_bottles(user_id: str = Depends(get_current_user)):
    return get_bottles(user_id)

@app.post("/bottles", response_model=StatusOut)
def create_bottle(b: BottleIn, user_id: str = Depends(get_current_user)):
    add_bottle(b.winery, b.wine_name, b.region, b.appellation, b.varietal,
               b.vintage, b.quantity, b.drink_from, b.drink_by,
               b.your_notes, b.your_rating, b.expert_notes, user_id,
               b.purchase_price, b.market_value)
    return {"status": "ok"}

@app.put("/bottles/{bottle_id}", response_model=StatusOut)
def edit_bottle(bottle_id: int, b: BottleIn, user_id: str = Depends(get_current_user)):
    update_bottle(bottle_id, b.winery, b.wine_name, b.region, b.appellation,
                  b.varietal, b.vintage, b.quantity, b.drink_from, b.drink_by,
                  b.your_notes, b.your_rating, b.expert_notes, user_id,
                  b.purchase_price, b.market_value)
    return {"status": "ok"}

@app.delete("/bottles/{bottle_id}", response_model=StatusOut)
def remove_bottle(bottle_id: int, user_id: str = Depends(get_current_user)):
    delete_bottle(bottle_id, user_id)
    return {"status": "ok"}

@app.post("/bottles/{bottle_id}/drink", response_model=DrinkResult)
def drink_bottle(bottle_id: int, entry: DrinkEntry, user_id: str = Depends(get_current_user)):
    bottle = get_bottle(bottle_id, user_id)
    if bottle is None:
        raise HTTPException(status_code=404, detail="Bottle not found")
    new_qty = decrement_bottle(bottle_id, user_id, entry.quantity)
    if new_qty is None:
        raise HTTPException(status_code=400, detail="Not enough bottles in stock")
    if new_qty == 0:
        delete_bottle(bottle_id, user_id)
    log_consumption(
        bottle_id, bottle["winery"], bottle["wine_name"], bottle["vintage"],
        bottle["varietal"], bottle["region"],
        entry.quantity, entry.consumed_on, entry.notes, user_id,
    )
    return {"status": "ok", "remaining": new_qty}

@app.get("/log", response_model=list[LogEntryOut])
def consumption_log(user_id: str = Depends(get_current_user)):
    return get_consumption_log(user_id)

# ── AI ────────────────────────────────────────────────────────────────────────

# Server-Sent Events keep the response from being buffered before it reaches
# JS: browsers never MIME-sniff or hold back text/event-stream, and
# no-transform stops proxies (Railway's edge) from gzip-buffering the body.
_SSE_HEADERS = {
    "Cache-Control": "no-cache, no-transform",
    "X-Accel-Buffering": "no",
    "X-Content-Type-Options": "nosniff",
}


def _sse_events(chunks) -> Iterator[str]:
    """Frame text deltas as SSE events.

    Each delta is JSON-encoded into one `data:` event so embedded newlines
    survive the SSE framing. A failure mid-stream becomes an `error` event so
    the client can show a message instead of silently truncating the text.
    """
    try:
        for chunk in chunks:
            if chunk:
                yield f"data: {json.dumps(chunk)}\n\n"
    except Exception:
        logger.exception("AI stream failed mid-response")
        message = "The sommelier was interrupted — please try again."
        yield f"event: error\ndata: {json.dumps(message)}\n\n"


def _sse_stream(chunks) -> StreamingResponse:
    return StreamingResponse(
        _sse_events(chunks), media_type="text/event-stream", headers=_SSE_HEADERS
    )


@app.get("/ai/lookup")
def wine_lookup(winery: str = Query(min_length=1, max_length=200),
                region: str = Query(max_length=200),
                wine_name: Optional[str] = Query(default=None, max_length=200),
                varietal: Optional[str] = Query(default=None, max_length=200),
                vintage: Optional[int] = Query(default=None, ge=1800, le=2100),
                appellation: Optional[str] = Query(default=None, max_length=200),
                user_id: str = Depends(rate_limited_user)):
    result = lookup_wine_info(winery, region, wine_name, varietal, vintage, appellation)
    return {"result": result}

@app.get("/ai/pairing/{bottle_id}")
def food_pairing(bottle_id: int, user_id: str = Depends(rate_limited_user)):
    bottle = get_bottle(bottle_id, user_id)
    if bottle is None:
        raise HTTPException(status_code=404, detail="Bottle not found")
    return _sse_stream(stream_pairing(
        bottle["winery"], bottle["varietal"], bottle["region"],
        bottle["vintage"], bottle["your_notes"], bottle["expert_notes"],
    ))

@app.get("/ai/meal-pairing")
def meal_pairing(meal: str = Query(min_length=1, max_length=2000),
                 user_id: str = Depends(rate_limited_user)):
    return _sse_stream(stream_wine_for_meal(meal, get_bottles(user_id)))

@app.get("/ai/recommendations")
def recommendations(user_id: str = Depends(rate_limited_user)):
    return _sse_stream(stream_recommendations(get_bottles(user_id)))


@app.get("/ai/value-lookup", response_model=ValueEstimate)
def value_lookup(winery: str = Query(min_length=1, max_length=200),
                 region: str = Query(max_length=200),
                 wine_name: Optional[str] = Query(default=None, max_length=200),
                 varietal: Optional[str] = Query(default=None, max_length=200),
                 vintage: Optional[int] = Query(default=None, ge=1800, le=2100),
                 appellation: Optional[str] = Query(default=None, max_length=200),
                 user_id: str = Depends(rate_limited_user)):
    try:
        return estimate_market_value(winery, region, wine_name, varietal, vintage, appellation)
    except Exception:
        logger.exception("value lookup failed")
        raise HTTPException(status_code=502, detail="Could not estimate a value right now.")


@app.post("/ai/estimate-cellar")
def estimate_cellar(user_id: str = Depends(rate_limited_user)):
    """Estimate values for bottles that don't have one yet, streaming progress.

    Each bottle priced emits an SSE `data:` event {id, value}; persistence
    happens server-side as we go, so a closed tab still keeps prior results.
    """
    unvalued = [b for b in get_bottles(user_id) if b.get("market_value") is None]
    batch = unvalued[:BULK_VALUE_LIMIT]

    def events():
        valued = 0
        for b in batch:
            try:
                est = estimate_market_value(
                    b["winery"], b["region"], b["wine_name"],
                    b["varietal"], b["vintage"], b["appellation"],
                )
                value = est.get("value")
                if value is not None:
                    set_market_value(b["id"], user_id, value)
                    valued += 1
                yield f"data: {json.dumps({'id': b['id'], 'value': value})}\n\n"
            except Exception:
                logger.exception("valuation failed for bottle %s", b["id"])
                yield f"data: {json.dumps({'id': b['id'], 'value': None, 'error': True})}\n\n"
        summary = {"valued": valued, "remaining": len(unvalued) - len(batch)}
        yield f"event: done\ndata: {json.dumps(summary)}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream", headers=_SSE_HEADERS)
