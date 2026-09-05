from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0"
)


@app.get("/")
def root():
    return {
        "message": "AgentRaz API is running",
        "environment": settings.environment
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }