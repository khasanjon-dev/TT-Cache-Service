"""FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(title="TT Cache Service", version="0.1.0")


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Report that the API process is running."""
    return {"status": "ok"}
