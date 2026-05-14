"""Feature engineering para forecasting de demanda.

Genera features de calendario, rezagos (lags), medias móviles,
festivos de Colombia, estadísticas por SKU y codificación categórica.

Ver `.claude/skills/feature-engineering/SKILL.md` para detalles y reglas.
"""

from __future__ import annotations

import logging

import holidays
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

CATEGORICAS = [
    "item",
    "centro_operacion",
    "nombre_linea_n1",
    "nombre_linea_n2",
    "proveedor_codigo",
]


def construir_grid_completo(df: pd.DataFrame) -> pd.DataFrame:
    """Expande la serie a todas las (item × centro × semana) y rellena con cero.

    Necesario porque `ventas_semanales` solo tiene filas para semanas con venta.
    Las semanas sin venta deben aparecer explícitamente como cero para que
    los lags y rollings se calculen correctamente.
    """
    logger.info("Construyendo grid completo de combinaciones...")

    fechas = pd.date_range(
        df["fecha_inicio_semana"].min(),
        df["fecha_inicio_semana"].max(),
        freq="W-MON",
    )

    combinaciones = df[["item", "centro_operacion"]].drop_duplicates()
    grid = combinaciones.merge(
        pd.DataFrame({"fecha_inicio_semana": fechas}),
        how="cross",
    )

    df_completo = grid.merge(
        df,
        on=["item", "centro_operacion", "fecha_inicio_semana"],
        how="left",
    )

    df_completo["cantidad_total"] = df_completo["cantidad_total"].fillna(0)
    df_completo["valor_bruto_total"] = df_completo["valor_bruto_total"].fillna(0)
    df_completo["num_transacciones"] = (
        df_completo["num_transacciones"].fillna(0).astype(int)
    )

    iso = df_completo["fecha_inicio_semana"].dt.isocalendar()
    df_completo["anio"] = iso.year.astype(int)
    df_completo["semana"] = iso.week.astype(int)

    logger.info("Grid expandido: %s filas", f"{len(df_completo):,}")
    return df_completo


def agregar_features_calendario(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega features derivadas de la fecha (mes, trimestre, cíclicas, festivos)."""
    logger.info("Agregando features de calendario...")
    df = df.copy()

    df["mes"] = df["fecha_inicio_semana"].dt.month
    df["semana_iso"] = df["fecha_inicio_semana"].dt.isocalendar().week.astype(int)
    df["trimestre"] = df["fecha_inicio_semana"].dt.quarter
    df["dia_del_anio"] = df["fecha_inicio_semana"].dt.dayofyear

    # Cíclicas (importantes para captar estacionalidad)
    df["mes_sin"] = np.sin(2 * np.pi * df["mes"] / 12)
    df["mes_cos"] = np.cos(2 * np.pi * df["mes"] / 12)
    df["semana_sin"] = np.sin(2 * np.pi * df["semana_iso"] / 52)
    df["semana_cos"] = np.cos(2 * np.pi * df["semana_iso"] / 52)

    # Festivos de Colombia
    anios_unicos = sorted(df["fecha_inicio_semana"].dt.year.unique().tolist())
    co_holidays = holidays.country_holidays("CO", years=anios_unicos)

    def festivos_en_semana(fecha_inicio: pd.Timestamp) -> int:
        return sum(
            1 for i in range(7) if (fecha_inicio + pd.Timedelta(days=i)) in co_holidays
        )

    df["num_festivos_semana"] = df["fecha_inicio_semana"].apply(festivos_en_semana)

    return df


def agregar_lags_y_rollings(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega features de rezago y medias móviles.

    ⚠️ Las medias móviles usan shift(1) ANTES del rolling
    para no incluir la semana actual (evita data leakage).
    """
    logger.info("Agregando lags y rolling means...")
    df = df.sort_values(["item", "centro_operacion", "fecha_inicio_semana"]).reset_index(drop=True)

    grupo = df.groupby(["item", "centro_operacion"])["cantidad_total"]

    # Lags
    for lag in [1, 2, 4, 8, 13, 52]:
        df[f"lag_{lag}"] = grupo.shift(lag)

    # Rolling means y std (siempre con shift(1) antes)
    df["rolling_mean_4"] = (
        grupo.shift(1).rolling(window=4, min_periods=1).mean().reset_index(level=[0, 1], drop=True)
    )
    df["rolling_mean_13"] = (
        grupo.shift(1).rolling(window=13, min_periods=1).mean().reset_index(level=[0, 1], drop=True)
    )
    df["rolling_std_4"] = (
        grupo.shift(1).rolling(window=4, min_periods=2).std().reset_index(level=[0, 1], drop=True)
    )

    # Tendencia
    df["diff_1"] = grupo.diff(1)

    media_sku = grupo.transform("mean")
    df["ratio_vs_media"] = df["cantidad_total"] / media_sku.replace(0, np.nan)

    return df


def agregar_stats_sku(df: pd.DataFrame, fecha_corte_train: str) -> pd.DataFrame:
    """Agrega estadísticas por SKU calculadas SOLO sobre el periodo de train.

    Critico: si se calculan sobre todo el dataset hay data leakage.

    Args:
        df: DataFrame con todas las observaciones.
        fecha_corte_train: fecha máxima del set de entrenamiento (string ISO).
    """
    logger.info("Agregando estadísticas por SKU (calculadas sobre train)...")

    df_train_solo = df[df["fecha_inicio_semana"] <= fecha_corte_train]
    stats_sku = (
        df_train_solo.groupby("item")["cantidad_total"]
        .agg(
            sku_media="mean",
            sku_mediana="median",
            sku_std="std",
            sku_max="max",
            sku_min="min",
        )
        .reset_index()
    )

    df = df.merge(stats_sku, on="item", how="left")
    return df


def codificar_categoricas(
    df: pd.DataFrame,
    categoricas: list[str] | None = None,
) -> tuple[pd.DataFrame, dict]:
    """Codifica variables categóricas con LabelEncoder.

    Returns:
        Tupla (DataFrame con columnas `{col}_enc`, dict de encoders para inferencia).
    """
    from sklearn.preprocessing import LabelEncoder

    if categoricas is None:
        categoricas = CATEGORICAS

    logger.info("Codificando categóricas: %s", categoricas)
    df = df.copy()
    encoders: dict = {}

    for col in categoricas:
        if col not in df.columns:
            logger.warning("Columna %s no presente, se omite", col)
            continue
        encoder = LabelEncoder()
        df[f"{col}_enc"] = encoder.fit_transform(df[col].astype(str))
        encoders[col] = encoder

    return df, encoders


def build_features(
    df: pd.DataFrame,
    fecha_corte_train: str,
    incluir_abc_xyz: bool = True,
    engine=None,
) -> tuple[pd.DataFrame, dict]:
    """Pipeline completo de feature engineering.

    Args:
        df: DataFrame con `ventas_semanales`.
        fecha_corte_train: fecha máxima del set de entrenamiento (para sku_stats).
        incluir_abc_xyz: si True, merge con `clasificacion_abc_xyz` (requiere engine).
        engine: SQLAlchemy engine, necesario si incluir_abc_xyz=True.

    Returns:
        (df_con_features, encoders).
    """
    df = construir_grid_completo(df)
    df = agregar_features_calendario(df)
    df = agregar_lags_y_rollings(df)
    df = agregar_stats_sku(df, fecha_corte_train)

    if incluir_abc_xyz:
        if engine is None:
            raise ValueError("Se necesita `engine` cuando incluir_abc_xyz=True")
        abc = pd.read_sql(
            "SELECT item, clase_abc, clase_xyz, segmento_abc_xyz FROM clasificacion_abc_xyz",
            engine,
        )
        df = df.merge(abc, on="item", how="left")
        df["clase_abc_num"] = df["clase_abc"].map({"A": 1, "B": 2, "C": 3})
        df["clase_xyz_num"] = df["clase_xyz"].map({"X": 1, "Y": 2, "Z": 3})

    df, encoders = codificar_categoricas(df)
    logger.info("Features finalizadas: %s filas, %s columnas", f"{len(df):,}", len(df.columns))
    return df, encoders
