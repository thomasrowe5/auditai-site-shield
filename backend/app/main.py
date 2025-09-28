from __future__ import annotations
import os
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from app.routers import agent_tasks

from app.db import models, session
from app.routers import projects, subcontractors, subcontractor_documents
# include safety_docs if you have it
try:
    from app.routers import safety_docs
    HAS_SAFETY = True
except Exception:
    HAS_SAFETY = False

APP_NAME = "AuditAI SiteShield API"
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")

app = FastAPI(title=APP_NAME, version=APP_VERSION)

# CORS: permissive for local dev; tighten in prod via env if needed
ALLOWED_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

# if you want totally open during dev, uncomment the next line:
# ALLOWED_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOWED_ORIGINS if o.strip()],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount /uploads using an absolute path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

# Routers
app.include_router(projects.router)
app.include_router(subcontractors.router)
app.include_router(subcontractor_documents.router)
if HAS_SAFETY:
    app.include_router(safety_docs.router)
app.include_router(agent_tasks.router)

# Health & utility routes
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

@app.get("/healthz", tags=["Meta"])
def healthz():
    return {"status": "ok", "time": datetime.utcnow().isoformat() + "Z"}

@app.get("/version", tags=["Meta"])
def version():
    return {"name": APP_NAME, "version": APP_VERSION}

# Startup: create tables if missing
@app.on_event("startup")
def on_startup():
    try:
        models.Base.metadata.create_all(bind=session.engine)
    except Exception as e:
        # surface startup issues clearly
        return JSONResponse(status_code=500, content={"error": f"DB init failed: {e}"})

