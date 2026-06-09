from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import settings
from backend.core.database import database
from backend.routes import (
    dashboard_routes,
    forecast_routes,
    health,
    orders,
    risk_predict_routes,
    supplier_selection_routes,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Menyambungkan database saat startup
    try:
        await database.connect()
    except Exception as e:
        print(f"Database connection skipped or failed: {e}")
        
    from backend.core.model_registry import model_registry
    model_registry.load_all()
    yield
    # Memutuskan database saat shutdown
    await database.disconnect()
    model_registry.clear()


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Backend API for Supply Chain Analytics: Late Delivery Risk, "
        "Demand Forecasting, Supplier Selection, and PostgreSQL dashboard data."
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# Mengaktifkan CORS agar domain frontend Vercel bisa mengambil data dari HF
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.allowed_origins == [] else settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================================
# SOLUSI UTAMA: Rute Root Dasar (/) khusus untuk bypass 404 Hugging Face
# =====================================================================
@app.get("/")
async def root_hf_check():
    return {
        "status": "online",
        "message": f"Backend API for {settings.APP_NAME} is running perfectly!",
        "documentation": "/docs"
    }


def include_api(prefix: str) -> None:
    app.include_router(health.router, prefix=prefix, tags=["Health"])
    app.include_router(orders.router, prefix=f"{prefix}/orders", tags=["Orders"])
    app.include_router(risk_predict_routes.router, prefix=f"{prefix}/risk", tags=["Late Delivery Risk"])
    app.include_router(forecast_routes.router, prefix=f"{prefix}/forecast", tags=["Demand Forecast"])
    app.include_router(
        supplier_selection_routes.router,
        prefix=f"{prefix}/supplier-selection",
        tags=["Supplier Selection"],
    )
    app.include_router(dashboard_routes.router, prefix=f"{prefix}/dashboard", tags=["Dashboard"])


# Memasang rute ber-prefix (contoh: /api/v1)
include_api(settings.API_V1_PREFIX)
include_api(settings.API_PREFIX)