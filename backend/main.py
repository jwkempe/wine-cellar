import os
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from database import (
    get_bottles, get_bottle, add_bottle, update_bottle, delete_bottle,
    init_db, log_consumption, get_consumption_log,
)
from ai import (
    lookup_wine_info, stream_pairing, stream_recommendations, stream_wine_for_meal,
)
from auth import get_current_user

load_dotenv()

# Headers that keep streamed responses from being buffered by proxies.
_STREAM_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}


def _text_stream(chunks) -> StreamingResponse:
    return StreamingResponse(chunks, media_type="text/plain; charset=utf-8", headers=_STREAM_HEADERS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex="https://.*\\.vercel\\.app",
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Data models ───────────────────────────────────────────────────────────────

class Bottle(BaseModel):
    winery: str
    wine_name: Optional[str] = None
    region: str
    appellation: Optional[str] = None
    varietal: str
    vintage: Optional[int] = None
    quantity: int = 1
    drink_from: Optional[int] = None
    drink_by: Optional[int] = None
    your_notes: Optional[str] = None
    your_rating: Optional[float] = None
    expert_notes: Optional[str] = None
    purchase_price: Optional[float] = None


class DrinkEntry(BaseModel):
    quantity: int = 1
    consumed_on: str  # ISO date string YYYY-MM-DD
    notes: Optional[str] = None

# ── Bottles ───────────────────────────────────────────────────────────────────

@app.get("/bottles")
def list_bottles(user_id: str = Depends(get_current_user)):
    return get_bottles(user_id)

@app.post("/bottles")
def create_bottle(b: Bottle, user_id: str = Depends(get_current_user)):
    add_bottle(b.winery, b.wine_name, b.region, b.appellation, b.varietal,
               b.vintage, b.quantity, b.drink_from, b.drink_by,
               b.your_notes, b.your_rating, b.expert_notes, user_id, b.purchase_price)
    return {"status": "ok"}

@app.put("/bottles/{bottle_id}")
def edit_bottle(bottle_id: int, b: Bottle, user_id: str = Depends(get_current_user)):
    update_bottle(bottle_id, b.winery, b.wine_name, b.region, b.appellation,
                  b.varietal, b.vintage, b.quantity, b.drink_from, b.drink_by,
                  b.your_notes, b.your_rating, b.expert_notes, user_id, b.purchase_price)
    return {"status": "ok"}

@app.delete("/bottles/{bottle_id}")
def remove_bottle(bottle_id: int, user_id: str = Depends(get_current_user)):
    delete_bottle(bottle_id, user_id)
    return {"status": "ok"}

@app.post("/bottles/{bottle_id}/drink")
def drink_bottle(bottle_id: int, entry: DrinkEntry, user_id: str = Depends(get_current_user)):
    bottle = get_bottle(bottle_id, user_id)
    if bottle is None:
        raise HTTPException(status_code=404, detail="Bottle not found")
    if entry.quantity > bottle["quantity"]:
        raise HTTPException(status_code=400, detail="Not enough bottles in stock")
    new_qty = bottle["quantity"] - entry.quantity
    if new_qty == 0:
        delete_bottle(bottle_id, user_id)
    else:
        update_bottle(
            bottle_id,
            bottle["winery"], bottle["wine_name"], bottle["region"], bottle["appellation"],
            bottle["varietal"], bottle["vintage"], new_qty,
            bottle["drink_from"], bottle["drink_by"],
            bottle["your_notes"], bottle["your_rating"], bottle["expert_notes"],
            user_id, bottle["purchase_price"],
        )
    log_consumption(
        bottle_id, bottle["winery"], bottle["wine_name"], bottle["vintage"],
        bottle["varietal"], bottle["region"],
        entry.quantity, entry.consumed_on, entry.notes, user_id,
    )
    return {"status": "ok", "remaining": new_qty}

@app.get("/log")
def consumption_log(user_id: str = Depends(get_current_user)):
    return get_consumption_log(user_id)

# ── AI ────────────────────────────────────────────────────────────────────────

@app.get("/ai/lookup")
def wine_lookup(winery: str, region: str, wine_name: Optional[str] = None,
                varietal: Optional[str] = None, vintage: Optional[int] = None,
                appellation: Optional[str] = None,
                user_id: str = Depends(get_current_user)):
    result = lookup_wine_info(winery, region, wine_name, varietal, vintage, appellation)
    return {"result": result}

@app.get("/ai/pairing/{bottle_id}")
def food_pairing(bottle_id: int, user_id: str = Depends(get_current_user)):
    bottle = get_bottle(bottle_id, user_id)
    if bottle is None:
        raise HTTPException(status_code=404, detail="Bottle not found")
    return _text_stream(stream_pairing(
        bottle["winery"], bottle["varietal"], bottle["region"],
        bottle["vintage"], bottle["your_notes"], bottle["expert_notes"],
    ))

@app.get("/ai/meal-pairing")
def meal_pairing(meal: str, user_id: str = Depends(get_current_user)):
    return _text_stream(stream_wine_for_meal(meal, get_bottles(user_id)))

@app.get("/ai/recommendations")
def recommendations(user_id: str = Depends(get_current_user)):
    return _text_stream(stream_recommendations(get_bottles(user_id)))
