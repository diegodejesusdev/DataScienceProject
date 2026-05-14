"""Clasificación ABC/XYZ de SKUs.

ABC: ordena por valor monetario (Pareto, cortes 80/95).
XYZ: ordena por coeficiente de variación de la demanda (cortes 0.5/1.0).

Ver `.claude/skills/abc-xyz-classification/SKILL.md` para detalles.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# Cortes estándar (ajustables si el negocio lo requiere)
CORTE_A = 80.0
CORTE_B = 95.0
CORTE_X = 0.5
CORTE_Y = 1.0
MIN_SEMANAS_XYZ = 8  # SKUs con menos historia se marcan como Z


def clasificar_abc(df_ventas: pd.DataFrame) -> pd.DataFrame:
    """Calcula la clasificación ABC por SKU.

    Args:
        df_ventas: DataFrame con columnas `item` y `valor_bruto_total` (granular o agregado).

    Returns:
        DataFrame con `item`, `valor_total_periodo`, `porcentaje_acumulado`, `clase_abc`.
    """
    logger.info("Calculando clasificación ABC...")

    valor_por_sku = (
        df_ventas.groupby("item")["valor_bruto_total"]
        .sum()
        .reset_index()
        .rename(columns={"valor_bruto_total": "valor_total_periodo"})
        .sort_values("valor_total_periodo", ascending=False)
        .reset_index(drop=True)
    )

    valor_total = valor_por_sku["valor_total_periodo"].sum()
    valor_por_sku["porcentaje_acumulado"] = (
        valor_por_sku["valor_total_periodo"].cumsum() / valor_total * 100
    ).round(2)

    def asignar_abc(pct: float) -> str:
        if pct <= CORTE_A:
            return "A"
        if pct <= CORTE_B:
            return "B"
        return "C"

    valor_por_sku["clase_abc"] = valor_por_sku["porcentaje_acumulado"].apply(asignar_abc)

    distribucion = valor_por_sku["clase_abc"].value_counts().to_dict()
    logger.info("Distribución ABC (n SKUs): %s", distribucion)
    return valor_por_sku


def clasificar_xyz(df_ventas: pd.DataFrame) -> pd.DataFrame:
    """Calcula la clasificación XYZ por SKU.

    Importante: el DataFrame debe tener la serie EXPANDIDA (con ceros para
    semanas sin venta). Si no, el CV se calcula sobre una serie incompleta
    y queda subestimado.

    Args:
        df_ventas: DataFrame con `item`, `fecha_inicio_semana`, `cantidad_total`,
                   ya expandido a todas las semanas del periodo.

    Returns:
        DataFrame con `item`, `coef_variacion`, `clase_xyz`.
    """
    logger.info("Calculando clasificación XYZ...")

    stats = (
        df_ventas.groupby("item")["cantidad_total"]
        .agg(media="mean", desvio="std", n_semanas="count")
        .reset_index()
    )

    stats["coef_variacion"] = (
        stats["desvio"] / stats["media"].replace(0, np.nan)
    ).fillna(np.inf)

    def asignar_xyz(cv: float) -> str:
        if cv < CORTE_X:
            return "X"
        if cv <= CORTE_Y:
            return "Y"
        return "Z"

    stats["clase_xyz"] = stats["coef_variacion"].apply(asignar_xyz)

    # SKUs con poca historia → Z
    poca_historia = stats["n_semanas"] < MIN_SEMANAS_XYZ
    if poca_historia.any():
        n = int(poca_historia.sum())
        logger.info("Marcando %d SKUs como Z por tener <%d semanas", n, MIN_SEMANAS_XYZ)
        stats.loc[poca_historia, "clase_xyz"] = "Z"

    # CV se reporta truncado a un valor razonable para almacenar
    stats["coef_variacion"] = stats["coef_variacion"].replace(np.inf, 999.0).round(4)

    distribucion = stats["clase_xyz"].value_counts().to_dict()
    logger.info("Distribución XYZ (n SKUs): %s", distribucion)
    return stats[["item", "coef_variacion", "clase_xyz"]]


def construir_matriz(abc: pd.DataFrame, xyz: pd.DataFrame) -> pd.DataFrame:
    """Combina ABC y XYZ en una única tabla con el segmento."""
    matriz = abc.merge(xyz, on="item", how="outer")
    matriz["clase_abc"] = matriz["clase_abc"].fillna("C")
    matriz["clase_xyz"] = matriz["clase_xyz"].fillna("Z")
    matriz["segmento_abc_xyz"] = matriz["clase_abc"] + matriz["clase_xyz"]
    return matriz[[
        "item", "valor_total_periodo", "porcentaje_acumulado",
        "clase_abc", "coef_variacion", "clase_xyz", "segmento_abc_xyz",
    ]]


def cargar_clasificacion(matriz: pd.DataFrame, engine: Engine) -> int:
    """Trunca y carga la tabla clasificacion_abc_xyz."""
    logger.info("Cargando clasificación a MySQL...")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE clasificacion_abc_xyz"))
    matriz.to_sql("clasificacion_abc_xyz", engine, if_exists="append", index=False)

    with engine.connect() as conn:
        n = conn.execute(text("SELECT COUNT(*) FROM clasificacion_abc_xyz")).scalar()
    logger.info("clasificacion_abc_xyz cargada: %s SKUs", f"{n:,}")
    return int(n)


def ejecutar_clasificacion(engine: Engine) -> pd.DataFrame:
    """Pipeline completo: lee de MySQL, clasifica y carga resultados.

    Args:
        engine: SQLAlchemy engine.

    Returns:
        DataFrame con la clasificación final.
    """
    logger.info("=" * 60)
    logger.info("Inicio de clasificación ABC/XYZ")
    logger.info("=" * 60)

    df = pd.read_sql(
        "SELECT item, fecha_inicio_semana, cantidad_total, valor_bruto_total FROM ventas_semanales",
        engine,
        parse_dates=["fecha_inicio_semana"],
    )

    # Expandir a serie completa (necesario para que XYZ no quede subestimado)
    fechas = pd.date_range(
        df["fecha_inicio_semana"].min(),
        df["fecha_inicio_semana"].max(),
        freq="W-MON",
    )
    grid = (
        pd.DataFrame({"item": df["item"].unique()})
        .merge(pd.DataFrame({"fecha_inicio_semana": fechas}), how="cross")
    )
    df_completo = grid.merge(df, on=["item", "fecha_inicio_semana"], how="left")
    df_completo["cantidad_total"] = df_completo["cantidad_total"].fillna(0)
    df_completo["valor_bruto_total"] = df_completo["valor_bruto_total"].fillna(0)

    abc = clasificar_abc(df_completo)
    xyz = clasificar_xyz(df_completo)
    matriz = construir_matriz(abc, xyz)
    cargar_clasificacion(matriz, engine)

    logger.info("=" * 60)
    logger.info("Clasificación finalizada")
    logger.info("=" * 60)
    return matriz


if __name__ == "__main__":
    from src.db import get_engine

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    engine = get_engine()
    resultado = ejecutar_clasificacion(engine)
    print(resultado.head(20))
