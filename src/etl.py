"""Pipeline ETL — Proyecto ConstruNorte.

Estrategia de ETL:
- Apache Hop hace la INGESTA INICIAL del CSV crudo a la tabla `ventas_staging`
  (con las 17 columnas útiles, ya sin datos personales).
- Python toma `ventas_staging`, tipifica, limpia y construye:
    - ventas_crudas (datos transaccionales limpios)
    - dim_producto (dimensión de productos)
    - ventas_semanales (tabla de hechos modelable, granularidad semanal)

Como respaldo, este módulo también puede leer el CSV directo (sin pasar por Hop)
mediante `run_etl_desde_csv()`, útil para desarrollo o si Hop no está disponible.

Ver `.claude/skills/etl-pipeline/SKILL.md` para el detalle de cada paso.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.db import get_engine

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_DEFAULT = BASE_DIR / "data" / "raw" / "ventas_construnorte.csv"

# Columnas útiles del CSV (Hop debe seleccionar estas 17, descartando las personales)
COLUMNAS_UTILES_CSV = [
    "Fecha", "Item", "Nombre Item", "Referencia Item", "Codigo Barra Item",
    "Unidad Inventario 1 Item", "Proveedor Codigo Item", "Proveedor Nombre Item",
    "Nombre Linea N1", "Nombre Linea N2", "Centro de Operacion", "Tipo de Documento",
    "Cantidad 1", "Precio Uni", "Valor Bruto", "Valor Costo", "Peso",
]

# Mapeo CSV → nombre interno (lo aplica Hop en el step "Select Values")
RENAMES = {
    "Fecha": "fecha",
    "Item": "item",
    "Nombre Item": "nombre_item",
    "Referencia Item": "referencia_item",
    "Codigo Barra Item": "codigo_barra",
    "Unidad Inventario 1 Item": "unidad_inventario",
    "Proveedor Codigo Item": "proveedor_codigo",
    "Proveedor Nombre Item": "proveedor_nombre",
    "Nombre Linea N1": "nombre_linea_n1",
    "Nombre Linea N2": "nombre_linea_n2",
    "Centro de Operacion": "centro_operacion",
    "Tipo de Documento": "tipo_documento",
    "Cantidad 1": "cantidad",
    "Precio Uni": "precio_unitario",
    "Valor Bruto": "valor_bruto",
    "Valor Costo": "valor_costo",
    "Peso": "peso",
}

# ⚠️ Confirmar con ConstruNorte cuáles tipos corresponden a venta efectiva
TIPOS_DOC_VENTA = ["J1"]


# =====================================================================
# 1. Lectura (dos fuentes posibles)
# =====================================================================

def leer_staging(engine: Engine) -> pd.DataFrame:
    """Lee la tabla `ventas_staging` cargada previamente por Apache Hop."""
    logger.info("Leyendo ventas_staging (cargada por Apache Hop)...")
    df = pd.read_sql("SELECT * FROM ventas_staging", engine)
    df = df.drop(columns=["id", "fecha_carga"], errors="ignore")
    logger.info("ventas_staging leida: %s filas", f"{len(df):,}")
    return df


def leer_csv(ruta_csv: Path = CSV_DEFAULT) -> pd.DataFrame:
    """Lee el CSV directamente (modo standalone, sin pasar por Hop).

    Solo se usa para desarrollo o si Apache Hop no esta disponible.
    En produccion el flujo oficial es leer desde `ventas_staging`.
    """
    logger.info("Leyendo CSV directo: %s", ruta_csv)
    df = pd.read_csv(
        ruta_csv,
        sep=";",
        usecols=COLUMNAS_UTILES_CSV,
        dtype=str,
        encoding="utf-8",
    )
    df = df.rename(columns=RENAMES)
    logger.info("CSV leido: %s filas, %d columnas", f"{len(df):,}", len(df.columns))
    return df


# =====================================================================
# 2. Tipificacion y limpieza (siempre se ejecuta en Python)
# =====================================================================

def normalizar_tipos(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte tipos: fecha (YYYYMMDD), numericos con coma decimal, strings."""
    logger.info("Normalizando tipos...")

    df["fecha"] = pd.to_datetime(df["fecha"], format="%Y%m%d", errors="coerce")

    columnas_numericas = ["cantidad", "precio_unitario", "valor_bruto", "valor_costo", "peso"]
    for col in columnas_numericas:
        df[col] = (
            df[col].astype(str)
            .str.replace(",", ".", regex=False)
            .str.strip()
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ["item", "centro_operacion", "tipo_documento"]:
        df[col] = df[col].astype(str).str.strip().str.upper()

    return df


def limpiar(df: pd.DataFrame) -> pd.DataFrame:
    """Filtra tipo doc, cantidades positivas y duplicados."""
    logger.info("Limpiando datos...")
    n_inicial = len(df)

    df = df[df["tipo_documento"].isin(TIPOS_DOC_VENTA)].copy()
    logger.info("Tras filtrar tipo_documento en %s: %s filas", TIPOS_DOC_VENTA, f"{len(df):,}")

    df = df[df["cantidad"] > 0].copy()
    df = df[df["valor_bruto"] >= 0].copy()
    logger.info("Tras filtrar cantidad>0 y valor>=0: %s filas", f"{len(df):,}")

    df = df.dropna(subset=["fecha", "item"]).copy()
    logger.info("Tras eliminar nulos en fecha/item: %s filas", f"{len(df):,}")

    df = df.drop_duplicates()
    logger.info("Tras drop_duplicates: %s filas", f"{len(df):,}")

    logger.info("Limpieza terminada: %s -> %s filas", f"{n_inicial:,}", f"{len(df):,}")
    return df


# =====================================================================
# 3. Cargas a las tablas destino
# =====================================================================

def cargar_ventas_crudas(df: pd.DataFrame, engine: Engine) -> int:
    """Trunca y carga `ventas_crudas` (datos limpios y tipificados)."""
    logger.info("Cargando a ventas_crudas...")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE ventas_crudas"))

    df.to_sql(
        "ventas_crudas",
        engine,
        if_exists="append",
        index=False,
        chunksize=10_000,
        method="multi",
    )

    with engine.connect() as conn:
        n = conn.execute(text("SELECT COUNT(*) FROM ventas_crudas")).scalar()
    logger.info("ventas_crudas cargada: %s filas", f"{n:,}")
    return int(n)


def construir_dim_producto(df: pd.DataFrame, engine: Engine) -> int:
    """Construye `dim_producto` a partir de los datos limpios."""
    logger.info("Construyendo dim_producto...")
    dim = (
        df.groupby("item")
        .agg(
            nombre_item=("nombre_item", "last"),
            referencia_item=("referencia_item", "last"),
            unidad_inventario=("unidad_inventario", "last"),
            proveedor_codigo=("proveedor_codigo", "last"),
            proveedor_nombre=("proveedor_nombre", "last"),
            nombre_linea_n1=("nombre_linea_n1", "last"),
            nombre_linea_n2=("nombre_linea_n2", "last"),
            fecha_primera_venta=("fecha", "min"),
            fecha_ultima_venta=("fecha", "max"),
        )
        .reset_index()
    )
    fecha_corte = df["fecha"].max() - pd.Timedelta(days=90)
    dim["activo"] = (dim["fecha_ultima_venta"] >= fecha_corte).astype(int)

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE dim_producto"))
    dim.to_sql("dim_producto", engine, if_exists="append", index=False)

    logger.info("dim_producto cargada: %s SKUs", f"{len(dim):,}")
    return len(dim)


def construir_ventas_semanales(df: pd.DataFrame, engine: Engine) -> int:
    """Agrega a granularidad (item x centro x anio x semana) y carga a MySQL."""
    logger.info("Agregando a granularidad semanal...")

    df = df.copy()
    iso = df["fecha"].dt.isocalendar()
    df["anio"] = iso.year.astype(int)
    df["semana"] = iso.week.astype(int)
    df["fecha_inicio_semana"] = (
        df["fecha"] - pd.to_timedelta(df["fecha"].dt.weekday, unit="D")
    ).dt.normalize()

    semanales = (
        df.groupby(["item", "centro_operacion", "anio", "semana", "fecha_inicio_semana"])
        .agg(
            cantidad_total=("cantidad", "sum"),
            valor_bruto_total=("valor_bruto", "sum"),
            num_transacciones=("cantidad", "count"),
        )
        .reset_index()
    )

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE ventas_semanales"))
    semanales.to_sql(
        "ventas_semanales",
        engine,
        if_exists="append",
        index=False,
        chunksize=10_000,
        method="multi",
    )

    with engine.connect() as conn:
        n = conn.execute(text("SELECT COUNT(*) FROM ventas_semanales")).scalar()
    logger.info("ventas_semanales cargada: %s filas", f"{n:,}")
    return int(n)


# =====================================================================
# 4. Pipelines completos
# =====================================================================

def run_etl_desde_staging() -> None:
    """Pipeline oficial: parte de `ventas_staging` (cargada por Apache Hop).

    Prerequisito: el flujo `hop/ingesta_csv.hpl` ya se ejecuto y dejo la
    tabla ventas_staging poblada.
    """
    logger.info("=" * 60)
    logger.info("ETL desde ventas_staging (cargada por Apache Hop)")
    logger.info("=" * 60)

    engine = get_engine()
    df = leer_staging(engine)
    df = normalizar_tipos(df)
    df = limpiar(df)

    cargar_ventas_crudas(df, engine)
    construir_dim_producto(df, engine)
    construir_ventas_semanales(df, engine)

    logger.info("=" * 60)
    logger.info("ETL finalizado correctamente")
    logger.info("=" * 60)


def run_etl_desde_csv(ruta_csv: Path = CSV_DEFAULT) -> None:
    """Pipeline alternativo: lee el CSV directamente, sin pasar por Hop.

    Util para desarrollo o cuando Apache Hop no esta disponible.
    """
    logger.info("=" * 60)
    logger.info("ETL desde CSV directo (modo standalone, sin Hop)")
    logger.info("=" * 60)

    engine = get_engine()
    df = leer_csv(ruta_csv)
    df = normalizar_tipos(df)
    df = limpiar(df)

    cargar_ventas_crudas(df, engine)
    construir_dim_producto(df, engine)
    construir_ventas_semanales(df, engine)

    logger.info("=" * 60)
    logger.info("ETL finalizado correctamente")
    logger.info("=" * 60)


def run_etl() -> None:
    """Alias del pipeline oficial (desde staging)."""
    run_etl_desde_staging()


if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(description="Pipeline ETL ConstruNorte")
    parser.add_argument(
        "--modo",
        choices=["staging", "csv"],
        default="staging",
        help="staging: lee de ventas_staging (post-Hop). csv: lee CSV directo.",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=CSV_DEFAULT,
        help="Ruta al CSV (solo aplica si --modo csv).",
    )
    args = parser.parse_args()

    if args.modo == "staging":
        run_etl_desde_staging()
    else:
        run_etl_desde_csv(args.csv)
