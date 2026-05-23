"""FastAPI app principal — ConstruNorte API."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routers import clasificacion, descriptivo, insights, metricas, pronosticos

app = FastAPI(
    title="ConstruNorte API",
    description=(
        "API REST del sistema de pronóstico de demanda de inventarios — "
        "Diplomado Ingeniería y Ciencia de Datos, Unicomfacauca 2026."
    ),
    version="1.0.0",
    contact={"name": "Diego Andrés De Jesús Montenegro y Luis David Andrade Díaz"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(pronosticos.router, prefix="/api/pronosticos", tags=["Pronósticos"])
app.include_router(clasificacion.router, prefix="/api/clasificacion", tags=["Clasificación"])
app.include_router(metricas.router, prefix="/api/metricas", tags=["Métricas"])
app.include_router(insights.router, prefix="/api/insights", tags=["Insights"])
app.include_router(descriptivo.router, prefix="/api/descriptivo", tags=["Descriptivo"])

# Servir frontend estático — debe ir DESPUÉS de los routers
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
