from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv
import pandas as pd

from database import get_bottles, add_bottle, update_bottle, delete_bottle
from ai import get_pairing_suggestion, get_recommendations, lookup_wine_info

load_dotenv()

app = FastAPI()

# Allow React frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
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

# ── Bottles ───────────────────────────────────────────────────────────────────

@app.get("/bottles")
def list_bottles():
    import math
    df = get_bottles()
    records = df.to_dict(orient="records")
    cleaned = [
        {k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in row.items()}
        for row in records
    ]
    return cleaned

@app.post("/bottles")
def create_bottle(b: Bottle):
    add_bottle(b.winery, b.wine_name, b.region, b.appellation, b.varietal,
               b.vintage, b.quantity, b.drink_from, b.drink_by,
               b.your_notes, b.your_rating, b.expert_notes)
    return {"status": "ok"}

@app.put("/bottles/{bottle_id}")
def edit_bottle(bottle_id: int, b: Bottle):
    update_bottle(bottle_id, b.winery, b.wine_name, b.region, b.appellation,
                  b.varietal, b.vintage, b.quantity, b.drink_from, b.drink_by,
                  b.your_notes, b.your_rating, b.expert_notes)
    return {"status": "ok"}

@app.delete("/bottles/{bottle_id}")
def remove_bottle(bottle_id: int):
    delete_bottle(bottle_id)
    return {"status": "ok"}

# ── AI ────────────────────────────────────────────────────────────────────────

@app.get("/ai/lookup")
def wine_lookup(winery: str, varietal: str, region: str,
                vintage: Optional[int] = None, appellation: Optional[str] = None):
    result = lookup_wine_info(winery, varietal, region, vintage, appellation)
    return {"result": result}

@app.get("/ai/pairing/{bottle_id}")
def food_pairing(bottle_id: int):
    df = get_bottles()
    bottle = df[df["id"] == bottle_id].iloc[0]
    result = get_pairing_suggestion(
        bottle["winery"], bottle["varietal"], bottle["region"],
        bottle["vintage"], bottle["your_notes"], bottle["expert_notes"]
    )
    return {"result": result}

@app.get("/ai/recommendations")
def recommendations():
    df = get_bottles()
    result = get_recommendations(df)
    return {"result": result}