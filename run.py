import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from api.auth import app as auth_app
from api.users import app as users_app
from api.schemes import app as schemes_app
from api.eligibility import app as eligibility_app
from api.applications import app as applications_app
from api.documents import app as documents_app
from api.admin import app as admin_app
from api.admin_auth import app as admin_auth_app
from api.reports import app as reports_app

app = FastAPI(
    title="AI Government Welfare Eligibility Assistant",
    description="Unified API Server",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
UPLOADS_DIR = os.path.join(STATIC_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(admin_auth_app.router)
app.include_router(auth_app.router)
app.include_router(users_app.router)
app.include_router(schemes_app.router)
app.include_router(eligibility_app.router)
app.include_router(applications_app.router)
app.include_router(documents_app.router)
app.include_router(admin_app.router)
app.include_router(reports_app.router)

from fastapi.responses import HTMLResponse, Response

@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)

@app.get("/", response_class=HTMLResponse)
async def serve_homepage():
    index_path = os.path.join(BASE_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            headers = {
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
            return HTMLResponse(content=f.read(), headers=headers)
    return "<h1>AI Government Welfare Eligibility Assistant Server Running</h1>"

if __name__ == "__main__":
    print("Starting AI Government Welfare Eligibility Assistant on http://127.0.0.1:8000")
    uvicorn.run("run:app", host="127.0.0.1", port=8000, reload=False)
