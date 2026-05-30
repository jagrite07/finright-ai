# ============================================================
# FinRight AI — main.py
# 
# START SERVER:
#   python main.py
#   OR: uvicorn main:app --reload
#
# URLS:
#   http://localhost:8000/          → FinRight AI app
#   http://localhost:8000/docs      → API documentation
#   http://localhost:8000/health    → Server status
#   http://localhost:8000/api/v1/   → All API endpoints
# ============================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from app.config import settings
from app.routes import (
    auth, dashboard, transactions, goals, budgets,
    net_worth, reports, shopping, activity_log,
    income_sources, taxonomy, accounts, profile, data_export,
)
import logging
import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# ── Create app ────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="FinRight AI — Personal Finance OS",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS (allows frontend to call the API) ────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register all routes ───────────────────────────────────
PREFIX = "/api/v1"
app.include_router(auth.router,           prefix=PREFIX)
app.include_router(dashboard.router,      prefix=PREFIX)
app.include_router(transactions.router,   prefix=PREFIX)
app.include_router(goals.router,          prefix=PREFIX)
app.include_router(budgets.router,        prefix=PREFIX)
app.include_router(net_worth.router,      prefix=PREFIX)
app.include_router(reports.router,        prefix=PREFIX)
app.include_router(shopping.router,       prefix=PREFIX)
app.include_router(activity_log.router,   prefix=PREFIX)
app.include_router(income_sources.router, prefix=PREFIX)
app.include_router(taxonomy.router,       prefix=PREFIX)
app.include_router(accounts.router,       prefix=PREFIX)
app.include_router(profile.router,        prefix=PREFIX)
app.include_router(data_export.router,    prefix=PREFIX)

# ── Serve HTML frontend ───────────────────────────────────
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/", include_in_schema=False)
async def serve_frontend():
    return FileResponse("frontend/index.html")

# ── Health check ──────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "healthy ✅",
        "app": settings.app_name,
        "version": settings.app_version,
        "frontend": "/",
        "api_docs": "/docs",
    }

# ── Global error handler ──────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Something went wrong."}
    )

# ── Start server ──────────────────────────────────────────
if __name__ == "__main__":
    logger.info(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"🌐 App:      http://localhost:{settings.api_port}/")
    logger.info(f"📋 API Docs: http://localhost:{settings.api_port}/docs")
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_development,
        log_level="info",
    )
