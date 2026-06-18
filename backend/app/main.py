from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, churches, surveys, responses, scoring, reports, recommendations

app = FastAPI(
    title="BHIS — Biblical Health Intelligence System",
    description="Scripture-anchored church diagnostic platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
async def health():
    return {"status": "healthy"}
