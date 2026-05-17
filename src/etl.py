"""Pipeline ETL — Proyecto ConstruNorte.

Estrategia de ETL:
- Apache Hop hace la INGESTA INICIAL del CSV crudo a la tabla `ventas_staging`
  (15 columnas como String: las utiles + tipo_documento para filtrar despues).
- Python toma `ventas_staging`, tipifica, filtra (tipo de documento + periodo),
  limpia, descarta `tipo_documento` y construye:
    - ventas_crudas (datos transaccionales limpios, 14 columnas finales)
    - dim_producto (dimension de productos)
    - ventas_semanales (tabla de hechos modelable, granularidad semanal)

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

# ===================================================================
# Reglas de filtrado (decisiones tomadas con ConstruNorte)
# ===================================================================

# Tipos de documento en el dataset y su tratamiento:
#   1E, 2E, 3E = ventas con facturacion electronica (una por bodega) - INCLUIR
#   J1, B1, L1 = ventas previas a facturacion electronica - solo existen hasta
#                noviembre 2022. Como filtramos a 2024-2025, no aparecen.
#   CM = conversion de mercancia (89 registros) - DESCARTAR
#   CT = cotizaciones (no son ventas reales) - DESCARTAR
#   EN = devoluciones - DESCARTAR (modelamos solo ventas brutas)
#
# Solo dejamos 1E/2E/3E. Si por algun error de fecha llegara un J1/B1/L1
# al periodo 2024-2025, queda fuera y se reporta en la auditoria.
TIPOS_DOC_VENTA = ["1E", "2E", "3E"]

# Periodo de analisis acordado en el anteproyecto:
# El dataset tiene 2022, salto, 2024-2025, y primeros meses de 2026.
# Solo modelamos el periodo continuo y completo: 2024-2025 estricto.
# Datos de 2022 (pre-facturacion electronica) y 2026 (incompletos) quedan fuera.
FECHA_MIN = "2024-01-01"
FECHA_MAX = "2025-12-31"


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


# =====================================================================
# 2. Tipificacion
# =====================================================================

def normalizar_tipos(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte tipos: fecha (YYYYMMDD), numericos con coma decimal, strings."""
    logger.info("Normalizando tipos...")

    df["fecha"] = pd.to_datetime(df["fecha"], format="%Y%m%d", errors="coerce")

    columnas_numericas = ["cantidad", "precio_unitario", "valor_bruto", "valor_costo"]
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


# =====================================================================
# 3. Auditoria y limpieza
# =====================================================================

def auditar_tipos_documento(df: pd.DataFrame) -> None:
    """Reporta la distribucion de tipos de documento (para auditoria)."""
    distribucion = df["tipo_documento"].value_counts().to_dict()
    logger.info("Distribucion de tipos de documento (antes de filtrar):")
    for tipo, n in sorted(distribucion.items(), key=lambda x: -x[1]):
        marcador = "RETENER" if tipo in TIPOS_DOC_VENTA else "DESCARTAR"
        logger.info("  %s: %s filas [%s]", tipo, f"{n:,}", marcador)


def auditar_rango_fechas(df: pd.DataFrame) -> None:
    """Reporta la distribucion de fechas por anio (para auditoria)."""
    df_fechas = df.dropna(subset=["fecha"])
    if df_fechas.empty:
        logger.warning("No hay fechas validas en el dataset")
        return
    por_anio = df_fechas["fecha"].dt.year.value_counts().sort_index()
    logger.info("Distribucion de filas por anio (antes de filtrar):")
    for anio, n in por_anio.items():
        retener = FECHA_MIN[:4] <= str(anio) <= FECHA_MAX[:4]
        marcador = "RETENER" if retener else "DESCARTAR"
        logger.info("  %s: %s filas [%s]", anio, f"{n:,}", marcador)


def filtrar(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica todos los filtros del proyecto en orden, reportando cada paso."""
    logger.info("Aplicando filtros...")
    n_inicial = len(df)

    # Auditoria antes de filtrar
    auditar_tipos_documento(df)
    auditar_rango_fechas(df)

    # 1. Filtrar por tipo de documento (ventas efectivas)
    df = df[df["tipo_documento"].isin(TIPOS_DOC_VENTA)].copy()
    logger.info("Tras filtrar tipos de venta %s: %s filas", TIPOS_DOC_VENTA, f"{len(df):,}")

    # 2. Filtrar por periodo de analisis (2024-2025)
    df = df.dropna(subset=["fecha"]).copy()
    df = df[(df["fecha"] >= FECHA_MIN) & (df["fecha"] <= FECHA_MAX)].copy()
    logger.info("Tras filtrar periodo %s - %s: %s filas", FECHA_MIN, FECHA_MAX, f"{len(df):,}")

    # 3. Filtrar cantidades y valores invalidos
    df = df[df["cantidad"] > 0].copy()
    df = df[df["valor_bruto"] >= 0].copy()
    logger.info("Tras filtrar cantidad>0 y valor>=0: %s filas", f"{len(df):,}")

    # 4. Eliminar filas con item nulo
    df = df.dropna(subset=["item"]).copy()
    df = df[df["item"].str.strip() != ""].copy()
    logger.info("Tras eliminar nulos en item: %s filas", f"{len(df):,}")

    # 5. Eliminar duplicados exactos
    df = df.drop_duplicates()
    logger.info("Tras drop_duplicates: %s filas", f"{len(df):,}")

    logger.info("Filtrado terminado: %s -> %s filas (%.1f%% retenido)",
                f"{n_inicial:,}", f"{len(df):,}", len(df) / n_inicial * 100)

    # tipo_documento ya cumplio su funcion, lo descartamos antes de cargar
    df = df.drop(columns=["tipo_documento"])

    return df


# =====================================================================
# 4. Cargas a las tablas destino
# =====================================================================

def cargar_ventas_crudas(df: pd.DataFrame, engine: Engine) -> int:
    """Trunca y carga `ventas_crudas` (datos limpios, tipificados, sin tipo_documento)."""
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
# 5. Pipeline completo
# =====================================================================

def run_etl_desde_staging() -> None:
    """Pipeline oficial: parte de `ventas_staging` (cargada por Apache Hop)."""
    logger.info("=" * 60)
    logger.info("ETL desde ventas_staging (cargada por Apache Hop)")
    logger.info("=" * 60)

    engine = get_engine()
    df = leer_staging(engine)
    df = normalizar_tipos(df)
    df = filtrar(df)

    cargar_ventas_crudas(df, engine)
    construir_dim_producto(df, engine)
    construir_ventas_semanales(df, engine)

    logger.info("=" * 60)
    logger.info("ETL finalizado correctamente")
    logger.info("=" * 60)


def run_etl() -> None:
    """Alias del pipeline oficial."""
    run_etl_desde_staging()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    run_etl_desde_staging()
