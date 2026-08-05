from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.supabase_db import db
from app.models.schemas import CitizenProfile, ChatRequest
from app.services.eligibility_service import EligibilityEngine
from app.services.chatbot_service import AIChatbot

app = FastAPI(title="AI Welfare Eligibility Engine & AI Chatbot API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/evaluate")
async def evaluate_eligibility(profile: CitizenProfile):
    schemes = db.get_schemes()
    result = EligibilityEngine.analyze_all(profile.model_dump(), schemes)
    return result

@app.post("/api/chat")
async def chat_with_assistant(req: ChatRequest):
    res = AIChatbot.generate_response(req.message, language=req.language, profile_data=req.profile_data)
    return res
