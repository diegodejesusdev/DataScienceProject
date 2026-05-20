"""Engine SQLAlchemy — única fuente de verdad para la conexión a MySQL.

Reutiliza el patrón de src/db.py sin importar desde src/ para evitar
dependencias de path frágiles.
"""

from __future__ import annotations

from functools import lru_cache

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from api.config import (
    MYSQL_DATABASE,
    MYSQL_HOST,
    MYSQL_PASSWORD,
    MYSQL_PORT,
    MYSQL_USER,
)


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Devuelve el Engine singleton de SQLAlchemy."""
    url = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    )
    return create_engine(url, pool_pre_ping=True, pool_recycle=3600)


def query(sql: str, params: dict | None = None) -> pd.DataFrame:
    """Ejecuta un SELECT y retorna un DataFrame.

    Args:
        sql: Consulta SQL con parámetros nombrados (:nombre).
        params: Diccionario de parámetros para bind.

    Returns:
        DataFrame con los resultados.
    """
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        return pd.DataFrame(result.mappings().all())
