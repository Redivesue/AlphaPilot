"""FastAPI application for AlphaPilot Web Platform."""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure project root in path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.deps import get_state
from api.routers import (
    agent,
    backtest,
    dashboard,
    data,
    factors,
    logs,
    reports,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize app state on startup, cleanup on shutdown."""
    state = get_state()
    state.initialize()
    yield
    # Shutdown: nothing to clean up for now


app = FastAPI(
    title="AlphaPilot API",
    description="AI Quant Research Platform - AlphaPilot Web Backend",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(factors.router, prefix="/api/factors", tags=["factors"])
app.include_router(agent.router, prefix="/api/agent", tags=["agent"])
app.include_router(data.router, prefix="/api/data", tags=["data"])
app.include_router(backtest.router, prefix="/api/backtest", tags=["backtest"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(logs.router, prefix="/api/logs", tags=["logs"])

# Serve React static files in production (when frontend/dist exists)
_frontend_dist = _PROJECT_ROOT / "frontend" / "dist"
if _frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(_frontend_dist / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("assets/"):
            from fastapi import HTTPException
            raise HTTPException(404)
        file_path = _frontend_dist / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(_frontend_dist / "index.html")


@app.get("/api/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "AlphaPilot API"}
