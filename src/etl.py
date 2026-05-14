"""Pipeline ETL — Proyecto ConstruNorte.

Lee el CSV crudo, elimina columnas personales, normaliza tipos,
filtra por tipo de documento de venta y carga a MySQL.

Ver `.claude/skills/etl-pipeline/SKILL.md` para los detalles.
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

COLUMNAS_UTILES_CSV = [
    "Fecha", "Item", "Nombre Item", "Referencia Item", "Codigo Barra Item",
    "Unidad Inventario 1 Item", "Proveedor Codigo Item", "Proveedor Nombre Item",
    "Nombre Linea N1", "Nombre Linea N2", "Centro de Operacion", "Tipo de Documento",
    "Cantidad 1", "Precio Uni", "Valor Bruto", "Valor Costo", "Peso",
]

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

# ⚠️ CONFIRMAR con ConstruNorte cuáles tipos de documento corresponden a venta efectiva
TIPOS_DOC_VENTA = ["J1"]


def leer_csv(ruta_csv: Path = CSV_DEFAULT) -> pd.DataFrame:
    """Lee el CSV crudo retiendo solo las columnas útiles."""
    logger.info("Leyendo CSV: %s", ruta_csv)
    df = pd.read_csv(
        ruta_csv,
        sep=";",
        usecols=COLUMNAS_UTILES_CSV,
        dtype=str,
        encoding="utf-8",
    )
    df = df.rename(columns=RENAMES)
    logger.info("CSV leído: %d filas, %d columnas", len(df), len(df.columns))
    return df


def normalizar_tipos(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte tipos: fecha, numéricos, normaliza strings."""
    logger.info("Normalizando tipos...")

    # Fecha en formato YYYYMMDD
    df["fecha"] = pd.to_datetime(df["fecha"], format="%Y%m%d", errors="coerce")

    # Numéricos: reemplazar coma decimal por punto
    columnas_numericas = ["cantidad", "precio_unitario", "valor_bruto", "valor_costo", "peso"]
    for col in columnas_numericas:
        df[col] = (
            df[col].astype(str)
            .str.replace(",", ".", regex=False)
            .str.strip()
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Strings: trim + upper para identificadores
    for col in ["item", "centro_operacion", "tipo_documento"]:
        df[col] = df[col].astype(str).str.strip().str.upper()

    return df


def limpiar(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica limpieza: filtrado de tipo doc, cantidades positivas, duplicados."""
    logger.info("Limpiando datos...")
    n_inicial = len(df)

    df = df[df["tipo_documento"].isin(TIPOS_DOC_VENTA)].copy()
    logger.info("Tras filtrar tipo_documento ∈ %s: %d filas", TIPOS_DOC_VENTA, len(df))

    df = df[df["cantidad"] > 0].copy()
    df = df[df["valor_bruto"] >= 0].copy()
    logger.info("Tras filtrar cantidad>0 y valor>=0: %d filas", len(df))

    df = df.dropna(subset=["fecha", "item"]).copy()
    logger.info("Tras eliminar nulos en fecha/item: %d filas", len(df))

    df = df.drop_duplicates()
    logger.info("Tras drop_duplicates: %d filas", len(df))

    logger.info("Limpieza terminada: %d → %d filas", n_inicial, len(df))
    return df


def cargar_ventas_crudas(df: pd.DataFrame, engine: Engine) -> int:
    """Trunca y carga la tabla ventas_crudas. Devuelve el conteo final."""
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
    """Construye dim_producto a partir de las ventas crudas."""
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
    """Agrega a granularidad (item × centro × año × semana) y carga a MySQL."""
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


def run_etl(ruta_csv: Path = CSV_DEFAULT) -> None:
    """Ejecuta el pipeline ETL completo."""
    logger.info("=" * 60)
    logger.info("Inicio del pipeline ETL")
    logger.info("=" * 60)

    engine = get_engine()
    df = leer_csv(ruta_csv)
    df = normalizar_tipos(df)
    df = limpiar(df)

    cargar_ventas_crudas(df, engine)
    construir_dim_producto(df, engine)
    construir_ventas_semanales(df, engine)

    logger.info("=" * 60)
    logger.info("Pipeline ETL finalizado correctamente")
    logger.info("=" * 60)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    run_etl()
