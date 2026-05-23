"""ETF Compass — FastAPI application."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from backend.app.routers import admin, auth, backtest, dashboard, ohlc, positions, trades, wiki

app = FastAPI(title="ETF Compass", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(positions.router)
app.include_router(trades.router)
app.include_router(backtest.router)
app.include_router(ohlc.router)
app.include_router(admin.router)

# Wiki viewer (HTML pages)
app.include_router(wiki.router, prefix="/wiki")


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# Production: serve frontend static files
FRONTEND_DIST = Path("frontend/dist")
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{path:path}")
    async def spa_fallback(path: str):
        """Serve frontend SPA for all non-API, non-wiki routes."""
        file_path = FRONTEND_DIST / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")

    @app.get("/")
    async def root() -> FileResponse:
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    @app.get("/")
    async def root() -> RedirectResponse:
        return RedirectResponse(url="/wiki/")
