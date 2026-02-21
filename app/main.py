"""FastAPI entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as analyze_router
from app.config import DEBUG, ENV

app = FastAPI(
    title="Weather Analysis API",
    description="Weather-driven scenario analysis and playbook generation",
    version="0.1.0",
    debug=DEBUG,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router, prefix="/api", tags=["analyze"])


@app.get("/health")
def health():
    return {"status": "ok", "env": ENV}
