"""FastAPI backend application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .core.database import mongodb
from .core.model_registry import model_registry
from .routes import dashboard_routes, forecast_routes, health, orders, risk_predict_routes, supplier_selection_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=settings.LOG_LEVEL)
    model_registry.load_all()
    await mongodb.connect()
    yield
    await mongodb.disconnect()
    model_registry.clear()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Supply Chain Analytics API for late delivery risk, demand forecasting, "
            "supplier selection ranking, dashboard metrics, and MongoDB-backed orders."
        ),
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _include_routes(app, settings.API_PREFIX, include_in_schema=True)
    _include_routes(app, settings.API_V1_PREFIX, include_in_schema=False)

    @app.get("/", include_in_schema=False)
    def index() -> dict:
        return {
            "service": settings.APP_NAME,
            "status": "ok",
            "docs": "/docs",
            "health": f"{settings.API_PREFIX}/health",
        }


    return app


def _include_routes(app: FastAPI, prefix: str, include_in_schema: bool) -> None:
    app.include_router(health.router, prefix=prefix, include_in_schema=include_in_schema)
    app.include_router(risk_predict_routes.router, prefix=prefix, include_in_schema=include_in_schema)
    app.include_router(forecast_routes.router, prefix=prefix, include_in_schema=include_in_schema)
    app.include_router(supplier_selection_routes.router, prefix=prefix, include_in_schema=include_in_schema)
    app.include_router(dashboard_routes.router, prefix=prefix, include_in_schema=include_in_schema)
    app.include_router(orders.router, prefix=prefix, include_in_schema=include_in_schema)


app = create_app()


if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "app.backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )

