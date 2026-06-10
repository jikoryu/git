"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.api.v1.auth import router as auth_router
from app.api.v1.products import router as products_router
from app.api.v1.watchlist import router as watchlist_router
from app.api.v1.alerts import router as alerts_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup (dev convenience; use Alembic in production)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
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
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(products_router, prefix="/api/v1/products", tags=["Products"])
app.include_router(watchlist_router, prefix="/api/v1/watchlist", tags=["Watchlist"])
app.include_router(alerts_router, prefix="/api/v1/alerts", tags=["Alerts"])


@app.get("/health")
async def health_check():
    return {"status": "ok"}
