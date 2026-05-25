from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.routers import risk, forecast, supplier, health, orders
from backend.core.config import settings
from backend.core.database import database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await database.connect()
    from backend.core.model_registry import model_registry
    model_registry.load_all()
    yield
    # Shutdown
    await database.disconnect()
    model_registry.clear()


app = FastAPI(
    title="Neo-Horcrox Supply Chain API",
    description=(
        "Backend API for Supply Chain Analytics — "
        "Late Delivery Risk prediction, Demand Forecasting, dan Supplier Selection. "
        "Database: PostgreSQL."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router,   prefix="/api/v1",           tags=["Health"])
app.include_router(orders.router,   prefix="/api/v1/orders",    tags=["Orders"])
app.include_router(risk.router,     prefix="/api/v1/risk",      tags=["Late Delivery Risk"])
app.include_router(forecast.router, prefix="/api/v1/forecast",  tags=["Demand Forecast"])
app.include_router(supplier.router, prefix="/api/v1/supplier",  tags=["Supplier Selection"])