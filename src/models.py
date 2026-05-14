"""Entrenamiento de modelos de pronóstico de demanda.

Implementa baseline (media móvil 4 semanas), LightGBM y XGBoost.
Prophet vive en su propio notebook por correr SKU a SKU.

⚠️ Regla crítica: nunca split aleatorio en series de tiempo.
Ver `.claude/skills/time-series-modeling/SKILL.md` para detalles.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

# Features estándar del proyecto (deben existir en el df tras correr build_features)
FEATURES_DEFAULT = [
    "item_enc", "centro_operacion_enc",
    "nombre_linea_n1_enc", "nombre_linea_n2_enc", "proveedor_codigo_enc",
    "mes", "semana_iso", "trimestre",
    "mes_sin", "mes_cos", "semana_sin", "semana_cos",
    "num_festivos_semana",
    "lag_1", "lag_2", "lag_4", "lag_8", "lag_13", "lag_52",
    "rolling_mean_4", "rolling_mean_13", "rolling_std_4",
    "diff_1", "ratio_vs_media",
    "sku_media", "sku_mediana", "sku_std",
    "clase_abc_num", "clase_xyz_num",
]
TARGET = "cantidad_total"


def partir_temporal(
    df: pd.DataFrame,
    fecha_fin_train: str,
    fecha_fin_valid: str,
    col_fecha: str = "fecha_inicio_semana",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Particiona el DataFrame en train/valid/test por fecha.

    Args:
        df: DataFrame con las features y el target.
        fecha_fin_train: fecha máxima del set de entrenamiento (ISO string).
        fecha_fin_valid: fecha máxima del set de validación (ISO string).

    Returns:
        Tupla (train, valid, test).
    """
    train = df[df[col_fecha] <= fecha_fin_train].copy()
    valid = df[(df[col_fecha] > fecha_fin_train) & (df[col_fecha] <= fecha_fin_valid)].copy()
    test = df[df[col_fecha] > fecha_fin_valid].copy()

    logger.info("Train: %s filas (%s → %s)", f"{len(train):,}",
                train[col_fecha].min(), train[col_fecha].max())
    logger.info("Valid: %s filas (%s → %s)", f"{len(valid):,}",
                valid[col_fecha].min() if len(valid) else "—",
                valid[col_fecha].max() if len(valid) else "—")
    logger.info("Test:  %s filas (%s → %s)", f"{len(test):,}",
                test[col_fecha].min() if len(test) else "—",
                test[col_fecha].max() if len(test) else "—")
    return train, valid, test


def predecir_baseline_media_movil(df_eval: pd.DataFrame) -> np.ndarray:
    """Baseline: la predicción es la media móvil 4 semanas precalculada."""
    preds = df_eval["rolling_mean_4"].fillna(0).to_numpy()
    return np.clip(preds, 0, None)


def entrenar_lightgbm(
    train: pd.DataFrame,
    valid: pd.DataFrame,
    features: list[str] | None = None,
    params: dict | None = None,
    num_boost_round: int = 2000,
    early_stopping_rounds: int = 50,
):
    """Entrena un LightGBM Regressor con validación temporal.

    Returns:
        Tupla (modelo, predicciones_valid_clipeadas).
    """
    import lightgbm as lgb

    features = features or FEATURES_DEFAULT
    features = [f for f in features if f in train.columns]

    default_params = {
        "objective": "regression",
        "metric": "mae",
        "learning_rate": 0.05,
        "num_leaves": 63,
        "min_data_in_leaf": 30,
        "feature_fraction": 0.8,
        "bagging_fraction": 0.8,
        "bagging_freq": 5,
        "verbose": -1,
        "seed": 42,
    }
    if params:
        default_params.update(params)

    train_data = lgb.Dataset(train[features], label=train[TARGET])
    valid_data = lgb.Dataset(valid[features], label=valid[TARGET], reference=train_data)

    logger.info("Entrenando LightGBM con %d features...", len(features))
    model = lgb.train(
        default_params,
        train_data,
        num_boost_round=num_boost_round,
        valid_sets=[train_data, valid_data],
        valid_names=["train", "valid"],
        callbacks=[
            lgb.early_stopping(stopping_rounds=early_stopping_rounds),
            lgb.log_evaluation(period=100),
        ],
    )

    preds = model.predict(valid[features], num_iteration=model.best_iteration)
    preds = np.clip(preds, 0, None)
    return model, preds


def entrenar_xgboost(
    train: pd.DataFrame,
    valid: pd.DataFrame,
    features: list[str] | None = None,
    params: dict | None = None,
    n_estimators: int = 2000,
    early_stopping_rounds: int = 50,
):
    """Entrena un XGBoost Regressor con validación temporal.

    Returns:
        Tupla (modelo, predicciones_valid_clipeadas).
    """
    import xgboost as xgb

    features = features or FEATURES_DEFAULT
    features = [f for f in features if f in train.columns]

    default_params = {
        "learning_rate": 0.05,
        "max_depth": 6,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "min_child_weight": 10,
        "random_state": 42,
        "tree_method": "hist",
        "enable_categorical": False,
    }
    if params:
        default_params.update(params)

    logger.info("Entrenando XGBoost con %d features...", len(features))
    model = xgb.XGBRegressor(
        n_estimators=n_estimators,
        early_stopping_rounds=early_stopping_rounds,
        **default_params,
    )
    model.fit(
        train[features], train[TARGET],
        eval_set=[(valid[features], valid[TARGET])],
        verbose=100,
    )

    preds = np.clip(model.predict(valid[features]), 0, None)
    return model, preds


def guardar_predicciones(
    df_eval: pd.DataFrame,
    predicciones: Iterable[float],
    modelo: str,
    engine,
    col_fecha: str = "fecha_inicio_semana",
) -> int:
    """Guarda predicciones en la tabla `pronosticos`."""
    from sqlalchemy import text

    pron = pd.DataFrame({
        "item": df_eval["item"].values,
        "centro_operacion": df_eval["centro_operacion"].values,
        "fecha_inicio_semana": df_eval[col_fecha].values,
        "modelo": modelo,
        "prediccion": list(predicciones),
        "limite_inferior": None,
        "limite_superior": None,
    })

    # Borrar predicciones previas del mismo modelo para no duplicar
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM pronosticos WHERE modelo = :m"), {"m": modelo})

    pron.to_sql("pronosticos", engine, if_exists="append", index=False, chunksize=10_000)

    with engine.connect() as conn:
        n = conn.execute(
            text("SELECT COUNT(*) FROM pronosticos WHERE modelo = :m"),
            {"m": modelo},
        ).scalar()
    logger.info("Pronósticos cargados para %s: %s filas", modelo, f"{n:,}")
    return int(n)


def guardar_modelo(model, nombre: str) -> Path:
    """Persiste el modelo entrenado en disco."""
    ruta = MODELS_DIR / f"{nombre}.pkl"
    joblib.dump(model, ruta)
    logger.info("Modelo guardado en %s", ruta)
    return ruta
