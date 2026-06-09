import math
import os

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from database import get_conn, get_bottles, add_bottle, update_bottle, delete_bottle, init_db, log_consumption, get_consumption_log
from ai import get_pairing_suggestion, get_recommendations, lookup_wine_info, get_wine_for_meal
from auth import get_current_user

init_db()

load_dotenv()

app = FastAPI()

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
    df = get_bottles(user_id)
    records = df.to_dict(orient="records")
    return [
        {k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in row.items()}
        for row in records
    ]

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
    df = get_bottles(user_id)
    matches = df[df["id"] == bottle_id]
    if matches.empty:
        raise HTTPException(status_code=404, detail="Bottle not found")
    bottle = matches.iloc[0]
    if entry.quantity > int(bottle["quantity"]):
        raise HTTPException(status_code=400, detail="Not enough bottles in stock")
    new_qty = int(bottle["quantity"]) - entry.quantity
    if new_qty == 0:
        delete_bottle(bottle_id, user_id)
    else:
        update_bottle(
            bottle_id,
            bottle["winery"], bottle["wine_name"], bottle["region"], bottle["appellation"],
            bottle["varietal"], bottle["vintage"], new_qty,
            bottle["drink_from"], bottle["drink_by"],
            bottle["your_notes"], bottle["your_rating"], bottle["expert_notes"],
            user_id, bottle["purchase_price"] if not math.isnan(bottle["purchase_price"] or float('nan')) else None,
        )
    log_consumption(
        bottle_id, bottle["winery"], bottle["wine_name"], bottle["vintage"],
        bottle["varietal"], bottle["region"],
        entry.quantity, entry.consumed_on, entry.notes, user_id,
    )
    return {"status": "ok", "remaining": new_qty}

@app.get("/log")
def consumption_log(user_id: str = Depends(get_current_user)):
    df = get_consumption_log(user_id)
    records = df.to_dict(orient="records")
    return [
        {k: (None if isinstance(v, float) and math.isnan(v) else
             v.isoformat() if hasattr(v, 'isoformat') else v)
         for k, v in row.items()}
        for row in records
    ]

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
    df = get_bottles(user_id)
    matches = df[df["id"] == bottle_id]
    if matches.empty:
        raise HTTPException(status_code=404, detail="Bottle not found")
    bottle = matches.iloc[0]
    result = get_pairing_suggestion(
        bottle["winery"], bottle["varietal"], bottle["region"],
        bottle["vintage"], bottle["your_notes"], bottle["expert_notes"]
    )
    return {"result": result}

@app.get("/ai/meal-pairing")
def meal_pairing(meal: str, user_id: str = Depends(get_current_user)):
    df = get_bottles(user_id)
    result = get_wine_for_meal(meal, df)
    return result

@app.get("/ai/recommendations")
def recommendations(user_id: str = Depends(get_current_user)):
    df = get_bottles(user_id)
    result = get_recommendations(df)
    return {"result": result}
