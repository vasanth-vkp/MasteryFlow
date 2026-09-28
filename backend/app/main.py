"""
MasteryFlow - Main FastAPI Application
======================================
Explainable Adaptive Learning & Intervention Engine
YUVA Megathon 2026 EduGenAI Submission
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .database import engine, Base
from .api import router
from .diagnostic_service import seed_diagnostic_questions_if_needed
from .database import SessionLocal

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MasteryFlow API",
    description="Explainable Adaptive Learning & Intervention Engine with Bayesian Knowledge Tracing & DAG Prerequisites",
    version="1.0.0",
)

# Enable CORS for local Vite development and cross-origin access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(router)

@app.on_event("startup")
def on_startup():
    db = SessionLocal()
    try:
        seed_diagnostic_questions_if_needed(db)
    finally:
        db.close()

@app.get("/health")
def health():
    return {"status": "ok"}

# Mount frontend dist static files if built
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        if full_path.startswith("api"):
            return {"detail": "Not Found"}
        index_file = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"system": "MasteryFlow API", "docs": "/docs"}
else:
    @app.get("/")
    def root():
        return {
            "system": "MasteryFlow API",
            "tagline": "Explainable Adaptive Learning & Intervention Engine",
            "docs": "/docs",
            "status": "healthy"
        }
