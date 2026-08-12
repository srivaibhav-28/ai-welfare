from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.database.supabase_db import db
from app.services.auth_service import require_current_user

app = FastAPI(title="AI Welfare Schemes API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/schemes")
async def get_all_schemes():
    return db.get_schemes()

@app.get("/api/schemes/search")
async def search_schemes(q: str = Query("", description="Natural language search query")):
    """
    Module 10: Natural Language AI Smart Search
    Matches queries like 'Scholarships for Engineering Students', 'Schemes for Farmers', 'Women Entrepreneurship'
    """
    query_raw = q.strip().lower()
    schemes = db.get_schemes()
    if not query_raw:
        return schemes

    keywords = [k for k in query_raw.split() if len(k) > 2]
    matched_results = []

    for s in schemes:
        score = 0
        name = s.get("name", "").lower()
        cat = s.get("category", "").lower()
        desc = s.get("description", "").lower()
        benefits = s.get("benefits", "").lower()
        criteria = s.get("criteria", {})

        # Intent phrase matching
        if "farmer" in query_raw or "agriculture" in query_raw:
            if "farmer" in cat or "kisan" in name or criteria.get("farmer_status"):
                score += 50
        if "student" in query_raw or "scholarship" in query_raw or "education" in query_raw or "engineering" in query_raw:
            if "education" in cat or "scholarship" in name or criteria.get("student_status"):
                score += 50
        if "women" in query_raw or "girl" in query_raw or "widow" in query_raw:
            if "women" in cat or criteria.get("gender") == "Female" or criteria.get("widow_status"):
                score += 50
        if "disabled" in query_raw or "disability" in query_raw or "divyang" in query_raw:
            if "disability" in cat or criteria.get("disability_status"):
                score += 50
        if "pension" in query_raw or "old age" in query_raw or "senior" in query_raw:
            if "pension" in cat or criteria.get("min_age", 0) >= 60:
                score += 50
        if "housing" in query_raw or "house" in query_raw or "awas" in query_raw:
            if "housing" in cat or "awas" in name:
                score += 50

        # General keyword matching
        for kw in keywords:
            if kw in name:
                score += 30
            if kw in cat:
                score += 25
            if kw in desc:
                score += 15
            if kw in benefits:
                score += 10

        if score > 0:
            matched_results.append((score, s))

    matched_results.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in matched_results]

@app.get("/api/schemes/{scheme_id}")
async def get_scheme_details(scheme_id: str):
    scheme = db.get_scheme_by_id(scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")
    return scheme

@app.post("/api/schemes/{scheme_id}/bookmark")
async def toggle_bookmark(scheme_id: str, user: Dict[str, Any] = Depends(require_current_user)):
    prof = user.get("profile", {}) or {}
    saved = prof.get("saved_schemes", [])
    if scheme_id in saved:
        saved.remove(scheme_id)
        action = "removed"
    else:
        saved.append(scheme_id)
        action = "saved"
    prof["saved_schemes"] = saved
    db.update_user_profile(user["id"], prof)
    return {"message": f"Scheme {action} successfully", "saved_schemes": saved, "action": action}
