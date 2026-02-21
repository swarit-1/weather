"""FastAPI entrypoint for weather analysis service."""

from fastapi import FastAPI
from app.api import routes
from app.utils import logging

app = FastAPI(title="Weather Analysis API")

# Include routers
app.include_router(routes.router)

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
