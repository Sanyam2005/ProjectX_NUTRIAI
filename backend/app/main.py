from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import init_db
from app.routers import (
    achievements,
    analytics,
    analyze,
    auth,
    calendar,
    challenges,
    dashboard,
    foods,
    goals,
    meals,
    recommendations,
    reminders,
    tracking,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    Path("uploads").mkdir(exist_ok=True)
    yield


settings = get_settings()

app = FastAPI(
    title="NutriAI API",
    version="0.1.0",
    description="AI-powered calorie tracking, optimized for Indian meals.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Path("uploads").mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth.router)
app.include_router(analyze.router)
app.include_router(meals.router)
app.include_router(dashboard.router)
app.include_router(analytics.router)
app.include_router(goals.router)
app.include_router(tracking.router)
app.include_router(recommendations.router)
app.include_router(calendar.router)
app.include_router(achievements.router)
app.include_router(reminders.router)
app.include_router(challenges.router)
app.include_router(foods.router)


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env, "ai_provider": settings.ai_provider}
