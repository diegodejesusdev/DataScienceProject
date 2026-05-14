"""Conexión a MySQL — única fuente de verdad para el engine.

Lee credenciales del archivo .env en la raíz del proyecto.
Funciona tanto desde el contenedor Jupyter (host=mysql) como
desde el host nativo (host=localhost).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# Cargar variables de entorno desde la raíz del repo
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def get_engine() -> Engine:
    """Devuelve un Engine de SQLAlchemy conectado a la BD del proyecto.

    Lee las variables MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD,
    MYSQL_DATABASE del entorno (cargadas desde .env).

    Returns:
        Engine conectado a MySQL con pool_pre_ping y pool_recycle activados.

    Raises:
        ValueError: si faltan variables obligatorias en el .env.
    """
    host = os.getenv("MYSQL_HOST", "localhost")
    port = os.getenv("MYSQL_PORT", "3306")
    user = os.getenv("MYSQL_USER")
    password = os.getenv("MYSQL_PASSWORD")
    database = os.getenv("MYSQL_DATABASE")

    missing = [
        name for name, value in [
            ("MYSQL_USER", user),
            ("MYSQL_PASSWORD", password),
            ("MYSQL_DATABASE", database),
        ]
        if not value
    ]
    if missing:
        raise ValueError(
            f"Variables de entorno faltantes: {missing}. "
            "Asegúrate de tener el archivo .env en la raíz del proyecto."
        )

    url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    engine = create_engine(url, pool_pre_ping=True, pool_recycle=3600)

    logger.info("Engine MySQL creado para %s@%s:%s/%s", user, host, port, database)
    return engine


def test_connection() -> bool:
    """Prueba la conexión a la base de datos.

    Returns:
        True si la conexión funciona, False en caso contrario.
    """
    from sqlalchemy import text

    try:
        engine = get_engine()
        with engine.connect() as conn:
            version = conn.execute(text("SELECT VERSION()")).scalar()
            logger.info("Conexión OK. MySQL version: %s", version)
            return True
    except Exception as exc:
        logger.error("Error de conexión: %s", exc)
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    ok = test_connection()
    print("Conexión OK" if ok else "Conexión FALLÓ")
