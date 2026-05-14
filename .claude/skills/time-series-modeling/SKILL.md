---
name: time-series-modeling
description: Cómo entrenar correctamente modelos de pronóstico de demanda (baseline, LightGBM, XGBoost, Prophet) respetando el orden temporal. Léeme antes de cualquier entrenamiento o validación de modelo.
---

# Modelado de Series Temporales

## Regla suprema: NUNCA split aleatorio

⚠️ **Las series de tiempo NO se parten con `train_test_split` aleatorio.** Hacerlo significa entrenar con datos del futuro y evaluar sobre el pasado, lo cual es leakage grave y produce métricas optimistas falsas.

✅ **Correcto:** partición por fecha (tradicional o `TimeSeriesSplit`).
❌ **Incorrecto:** `train_test_split(X, y, test_size=0.2, random_state=42)`.

---

## Partición temporal recomendada

Dado el periodo del proyecto (ene 2024 – dic 2025, ~104 semanas):

| Conjunto | Periodo | Uso |
|---|---|---|
| Train | 2024-01-01 → 2025-09-30 | Entrenar modelos |
| Validation | 2025-10-01 → 2025-10-31 | Ajustar hiperparámetros |
| Test | 2025-11-01 → 2025-12-31 | Evaluación final, NO TOCAR durante el desarrollo |

```python
import pandas as pd

FECHA_FIN_TRAIN = "2025-09-30"
FECHA_FIN_VALID = "2025-10-31"

train = df[df["fecha_inicio_semana"] <= FECHA_FIN_TRAIN]
valid = df[(df["fecha_inicio_semana"] > FECHA_FIN_TRAIN) & (df["fecha_inicio_semana"] <= FECHA_FIN_VALID)]
test = df[df["fecha_inicio_semana"] > FECHA_FIN_VALID]

print(f"Train: {len(train):,} filas ({train['fecha_inicio_semana'].min()} → {train['fecha_inicio_semana'].max()})")
print(f"Valid: {len(valid):,} filas")
print(f"Test:  {len(test):,} filas")
```

---

## Baseline obligatorio

⚠️ **El baseline va PRIMERO. Si el modelo no le gana al baseline, no sirve.**

**Baseline 1: persistencia simple** — predice que la próxima semana es igual a la anterior.

```python
# Para cada SKU, la predicción es el cantidad_total de la semana anterior
baseline_pred = valid.groupby(["item", "centro_operacion"])["cantidad_total"].shift(1)
```

**Baseline 2: media móvil de 4 semanas** — predice el promedio de las últimas 4 semanas.

```python
# Usa la feature rolling_mean_4 que ya viene calculada
baseline_pred = valid["rolling_mean_4"]
```

**Baseline 3: misma semana del año anterior** — útil si hay estacionalidad anual.

```python
baseline_pred = valid["lag_52"]
```

**Reportar el MAE/RMSE/MAPE del baseline en el informe.** Es referencia obligatoria.

---

## LightGBM (modelo principal)

```python
import lightgbm as lgb
from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np

# Features y target
FEATURES = [
    "item_enc", "centro_operacion_enc", "nombre_linea_n1_enc", "nombre_linea_n2_enc",
    "proveedor_codigo_enc", "mes", "semana_iso", "trimestre",
    "mes_sin", "mes_cos", "semana_sin", "semana_cos", "num_festivos_semana",
    "lag_1", "lag_2", "lag_4", "lag_8", "lag_52",
    "rolling_mean_4", "rolling_mean_13", "rolling_std_4",
    "diff_1", "ratio_vs_media",
    "sku_media", "sku_mediana", "sku_std",
    "clase_abc_num", "clase_xyz_num",
]
TARGET = "cantidad_total"

X_train, y_train = train[FEATURES], train[TARGET]
X_valid, y_valid = valid[FEATURES], valid[TARGET]
X_test, y_test = test[FEATURES], test[TARGET]

# Hiperparámetros razonables como punto de partida
params = {
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

train_data = lgb.Dataset(X_train, label=y_train)
valid_data = lgb.Dataset(X_valid, label=y_valid, reference=train_data)

model_lgb = lgb.train(
    params,
    train_data,
    num_boost_round=2000,
    valid_sets=[train_data, valid_data],
    valid_names=["train", "valid"],
    callbacks=[
        lgb.early_stopping(stopping_rounds=50),
        lgb.log_evaluation(period=100),
    ],
)

# Predicciones
y_pred_valid = model_lgb.predict(X_valid, num_iteration=model_lgb.best_iteration)

# Evitar predicciones negativas (no tiene sentido vender cantidad negativa)
y_pred_valid = np.clip(y_pred_valid, 0, None)
```

### Notas técnicas
- **No tunees hiperparámetros con grid search exhaustivo.** No hay tiempo. Empieza con los valores de arriba, ajusta solo si hay margen claro de mejora.
- **`early_stopping`** te evita sobreajustar.
- **`np.clip(pred, 0, None)`** porque las predicciones de demanda no pueden ser negativas.

---

## XGBoost (modelo de comparación)

```python
import xgboost as xgb

model_xgb = xgb.XGBRegressor(
    n_estimators=2000,
    learning_rate=0.05,
    max_depth=6,
    subsample=0.8,
    colsample_bytree=0.8,
    min_child_weight=10,
    early_stopping_rounds=50,
    random_state=42,
    tree_method="hist",
    enable_categorical=False,
)

model_xgb.fit(
    X_train, y_train,
    eval_set=[(X_valid, y_valid)],
    verbose=100,
)

y_pred_xgb = np.clip(model_xgb.predict(X_valid), 0, None)
```

---

## Prophet (modelo individual por SKU)

⚠️ **Prophet NO se aplica al dataset completo.** Es un modelo univariante: uno por cada SKU.

Recomendación: aplicarlo solo a los **top 50 SKUs por valor (clase A)** o un subset definido. No tiene sentido entrenar Prophet sobre los miles de SKUs C.

```python
from prophet import Prophet

# Obtener los top SKUs
top_skus = (
    pd.read_sql("SELECT item FROM clasificacion_abc_xyz WHERE clase_abc = 'A' ORDER BY valor_total_periodo DESC LIMIT 50", engine)
    ["item"].tolist()
)

resultados_prophet = []

for sku in top_skus:
    serie_sku = (
        df[(df["item"] == sku) & (df["fecha_inicio_semana"] <= FECHA_FIN_TRAIN)]
        .groupby("fecha_inicio_semana")["cantidad_total"].sum()
        .reset_index()
    )
    serie_sku.columns = ["ds", "y"]

    if len(serie_sku) < 30:
        continue  # poca historia, saltar

    m = Prophet(
        weekly_seasonality=False,    # ya estamos a granularidad semanal
        yearly_seasonality=True,
        daily_seasonality=False,
        changepoint_prior_scale=0.05,
        seasonality_prior_scale=10,
    )

    # Festivos de Colombia
    festivos_co = pd.DataFrame({
        "holiday": "festivo_co",
        "ds": pd.to_datetime([str(d) for d in holidays.country_holidays("CO", years=range(2024, 2027))]),
    })
    m.add_country_holidays(country_name="CO")

    m.fit(serie_sku)

    futuro = m.make_future_dataframe(periods=8, freq="W-MON")
    pronostico = m.predict(futuro)
    pronostico["item"] = sku
    resultados_prophet.append(pronostico[["item", "ds", "yhat", "yhat_lower", "yhat_upper"]])

prophet_predicciones = pd.concat(resultados_prophet, ignore_index=True)
prophet_predicciones["yhat"] = prophet_predicciones["yhat"].clip(lower=0)
```

---

## Validación cruzada temporal (opcional pero recomendada)

Si tienen tiempo, usen `TimeSeriesSplit` de sklearn para más robustez:

```python
from sklearn.model_selection import TimeSeriesSplit

tscv = TimeSeriesSplit(n_splits=5, test_size=4)  # ventanas de validación de 4 semanas

scores = []
for i, (train_idx, valid_idx) in enumerate(tscv.split(df)):
    train_fold, valid_fold = df.iloc[train_idx], df.iloc[valid_idx]
    # ... entrenar y evaluar
    scores.append(score)

print(f"MAE promedio CV: {np.mean(scores):.3f} ± {np.std(scores):.3f}")
```

---

## Guardar modelos

```python
import joblib
from pathlib import Path

MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)

# Para LightGBM/XGBoost
joblib.dump(model_lgb, MODELS_DIR / "lightgbm_v1.pkl")
joblib.dump(model_xgb, MODELS_DIR / "xgboost_v1.pkl")

# ⚠️ NO commitear los .pkl al repo. Están en .gitignore.
```

---

## Guardar predicciones a MySQL

```python
predicciones_df = pd.DataFrame({
    "item": valid["item"].values,
    "fecha_inicio_semana": valid["fecha_inicio_semana"].values,
    "modelo": "lightgbm_v1",
    "prediccion": y_pred_valid,
    "limite_inferior": None,    # LightGBM no entrega intervalos por defecto
    "limite_superior": None,
})

predicciones_df.to_sql("pronosticos", engine, if_exists="append", index=False)
```

---

## Reglas no negociables

1. **NUNCA split aleatorio en series de tiempo.** Siempre partición por fecha.
2. **SIEMPRE entrenar el baseline primero** y reportar sus métricas.
3. **NUNCA permitir predicciones negativas.** Usar `np.clip(pred, 0, None)`.
4. **NUNCA usar el test set durante el desarrollo.** Solo al final para reporte.
5. **SIEMPRE comparar al menos 2 modelos** (LightGBM y XGBoost, o LightGBM y Prophet).
6. **DOCUMENTAR los hiperparámetros usados** en `docs/04_modelado.md`.
7. **NO tunear con grid search exhaustivo.** Empezar con valores razonables.
8. **GUARDAR todas las predicciones en `pronosticos`** para que Tableau pueda graficarlas.
