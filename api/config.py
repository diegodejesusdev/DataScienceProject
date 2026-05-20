"""Configuración global de la API — lee variables desde .env."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT: str = os.getenv("MYSQL_PORT", "3307")
MYSQL_USER: str = os.getenv("MYSQL_USER", "")
MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "")

MODELOS_VALIDOS: set[str] = {"lightgbm", "xgboost", "baseline_ma4", "prophet"}
CENTROS_VALIDOS: set[str] = {"001", "002", "003"}
SPLITS_VALIDOS: set[str] = {"valid", "test_2026"}
SEGMENTOS_VALIDOS: set[str] = {"global", "abc_A", "abc_B", "abc_C", "top50_clase_A"}

FECHA_FIN_TRAIN = "2025-09-30"
FECHA_FIN_VALID = "2025-12-31"
FECHA_FIN_TEST = "2026-03-31"

NOMBRES_MODELO: dict[str, str] = {
    "baseline_ma4": "Baseline (MA-4)",
    "lightgbm": "LightGBM",
    "xgboost": "XGBoost",
    "prophet": "Prophet",
}
