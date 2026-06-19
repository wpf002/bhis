import time

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.routers import auth, churches, surveys, responses, scoring, reports, recommendations
from app.core.errors import register_error_handlers
from app.core.observability import init_sentry, RequestLogMiddleware, START_TIME

init_sentry()

app = FastAPI(
    title="BHIS — Biblical Health Intelligence System",
    description="Scripture-anchored church diagnostic platform",
    version="1.0.0",
)

app.add_middleware(RequestLogMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(churches.router, prefix="/api/v1/churches", tags=["Churches"])
app.include_router(surveys.router, prefix="/api/v1/surveys", tags=["Surveys"])
app.include_router(responses.router, prefix="/api/v1/responses", tags=["Responses"])
app.include_router(scoring.router, prefix="/api/v1/scoring", tags=["Scoring"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(recommendations.router, prefix="/api/v1/recommendations", tags=["Recommendations"])


@app.get("/")
async def root():
    return {"status": "ok", "system": "BHIS"}


@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    db_ok = True
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
    return {
        "status": "healthy" if db_ok else "degraded",
        "db": db_ok,
        "uptime_seconds": int(time.time() - START_TIME),
    }
