"""Métricas de evaluación para forecasting.

Implementa MAE, RMSE, MAPE y sMAPE de forma robusta a NaN y ceros.
Ver `.claude/skills/evaluation-metrics/SKILL.md` para detalles.
"""

from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd


def calcular_metricas(
    y_true: Iterable[float],
    y_pred: Iterable[float],
    epsilon: float = 1e-6,
) -> dict:
    """Calcula MAE, RMSE, MAPE y sMAPE.

    Filtra valores NaN automáticamente.
    MAPE excluye observaciones con y_true cercano a cero.
    sMAPE es robusto a ceros.

    Args:
        y_true: valores reales.
        y_pred: predicciones del modelo.
        epsilon: umbral para considerar y_true ≈ 0 en el cálculo de MAPE.

    Returns:
        Diccionario con claves: mae, rmse, mape, smape, n.
    """
    y_true_arr = np.asarray(list(y_true), dtype=float)
    y_pred_arr = np.asarray(list(y_pred), dtype=float)

    # Filtrar NaN
    mask = ~(np.isnan(y_true_arr) | np.isnan(y_pred_arr))
    y_true_arr = y_true_arr[mask]
    y_pred_arr = y_pred_arr[mask]

    if len(y_true_arr) == 0:
        return {"mae": np.nan, "rmse": np.nan, "mape": np.nan, "smape": np.nan, "n": 0}

    # MAE
    mae_val = float(np.mean(np.abs(y_true_arr - y_pred_arr)))

    # RMSE
    rmse_val = float(np.sqrt(np.mean((y_true_arr - y_pred_arr) ** 2)))

    # MAPE (excluye y_true ≈ 0)
    mask_nonzero = np.abs(y_true_arr) > epsilon
    if mask_nonzero.any():
        mape_val = float(np.mean(
            np.abs((y_true_arr[mask_nonzero] - y_pred_arr[mask_nonzero]) / y_true_arr[mask_nonzero])
        ) * 100)
    else:
        mape_val = float("nan")

    # sMAPE (robusto a ceros)
    den = (np.abs(y_true_arr) + np.abs(y_pred_arr)) / 2
    mask_smape = den > 0
    if mask_smape.any():
        smape_val = float(np.mean(
            np.abs(y_true_arr[mask_smape] - y_pred_arr[mask_smape]) / den[mask_smape]
        ) * 100)
    else:
        smape_val = 0.0

    return {
        "mae": round(mae_val, 4),
        "rmse": round(rmse_val, 4),
        "mape": round(mape_val, 4) if not np.isnan(mape_val) else float("nan"),
        "smape": round(smape_val, 4),
        "n": int(len(y_true_arr)),
    }


def metricas_por_segmento(
    df_eval: pd.DataFrame,
    col_true: str = "y_true",
    col_pred: str = "y_pred",
    col_segmento: str = "segmento_abc_xyz",
) -> pd.DataFrame:
    """Calcula métricas agrupadas por segmento ABC/XYZ.

    Args:
        df_eval: DataFrame con valores reales, predicciones y segmento.
        col_true: nombre de la columna con valores reales.
        col_pred: nombre de la columna con predicciones.
        col_segmento: nombre de la columna con el segmento ABC/XYZ.

    Returns:
        DataFrame con una fila por segmento y columnas de métricas.
    """
    filas = []
    for segmento, sub in df_eval.groupby(col_segmento):
        m = calcular_metricas(sub[col_true], sub[col_pred])
        m["segmento"] = segmento
        filas.append(m)
    return pd.DataFrame(filas)[["segmento", "n", "mae", "rmse", "mape", "smape"]]


def tabla_comparativa(
    y_true: Iterable[float],
    predicciones_por_modelo: dict[str, Iterable[float]],
) -> pd.DataFrame:
    """Genera una tabla comparativa de métricas para múltiples modelos.

    Args:
        y_true: valores reales (compartidos por todos los modelos).
        predicciones_por_modelo: dict con {nombre_modelo: predicciones}.

    Returns:
        DataFrame con columnas: modelo, n, mae, rmse, mape, smape.
    """
    filas = []
    for nombre, preds in predicciones_por_modelo.items():
        m = calcular_metricas(y_true, preds)
        m["modelo"] = nombre
        filas.append(m)
    return pd.DataFrame(filas)[["modelo", "n", "mae", "rmse", "mape", "smape"]]
