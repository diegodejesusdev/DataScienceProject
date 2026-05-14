---
name: evaluation-metrics
description: Cómo calcular y reportar correctamente MAE, RMSE, MAPE y sMAPE en problemas de forecasting. Léeme antes de evaluar cualquier modelo o comparar resultados entre modelos.
---

# Métricas de evaluación de forecasting

## Las tres métricas obligatorias

Todo modelo del proyecto debe reportar **MAE, RMSE y MAPE juntos**. Nunca una sola.

### MAE — Mean Absolute Error
- **Fórmula:** promedio del error absoluto.
- **Unidades:** mismas que la variable (cantidad vendida).
- **Interpretación:** "en promedio el modelo se equivoca por X unidades".
- **Ventaja:** directamente interpretable.
- **Limitación:** trata todos los errores por igual.

```python
import numpy as np

def mae(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return np.mean(np.abs(y_true - y_pred))
```

### RMSE — Root Mean Squared Error
- **Fórmula:** raíz del promedio del error cuadrático.
- **Unidades:** mismas que la variable.
- **Interpretación:** parecido al MAE pero penaliza más los errores grandes.
- **Útil cuando:** los errores grandes son particularmente costosos (un quiebre de stock grande es peor que muchos pequeños).
- **Relación:** RMSE ≥ MAE siempre. Si RMSE >> MAE, hay outliers de error.

```python
def rmse(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return np.sqrt(np.mean((y_true - y_pred) ** 2))
```

### MAPE — Mean Absolute Percentage Error
- **Fórmula:** promedio del error absoluto como porcentaje del valor real.
- **Unidades:** porcentaje (adimensional).
- **Interpretación:** "el modelo se equivoca en promedio un X% respecto al real".
- **Ventaja:** permite comparar SKUs con escalas muy distintas.
- **Limitación crítica:** explota cuando hay valores reales en cero o muy bajos.

```python
def mape(y_true, y_pred, epsilon: float = 1e-6):
    """Mean Absolute Percentage Error.

    Si y_true contiene ceros, esos puntos se excluyen (con aviso).
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    mask = np.abs(y_true) > epsilon
    if not mask.any():
        return np.nan
    if (~mask).sum() > 0:
        # opcional: registrar advertencia
        pass

    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
```

---

## sMAPE — alternativa cuando hay muchos ceros

Si los SKUs tienen demanda con muchos ceros (típico en clase Z), MAPE se rompe. Usar **sMAPE (symmetric MAPE)**:

```python
def smape(y_true, y_pred):
    """Symmetric Mean Absolute Percentage Error. Robusto a ceros.

    Rango: 0% (perfecto) a 200% (peor).
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    denominator = (np.abs(y_true) + np.abs(y_pred)) / 2
    mask = denominator > 0
    if not mask.any():
        return 0.0
    return np.mean(np.abs(y_true[mask] - y_pred[mask]) / denominator[mask]) * 100
```

**Cuándo usar sMAPE en vez de MAPE:**
- Segmentos de clase Z (demanda errática).
- Productos con muchas semanas en cero.
- Si MAPE da valores > 200% sospechosamente altos.

---

## Función unificada de reporte

Pon esto en `src/evaluation.py`:

```python
import numpy as np
import pandas as pd


def calcular_metricas(y_true, y_pred) -> dict:
    """Calcula MAE, RMSE, MAPE y sMAPE de forma robusta.

    Returns:
        Diccionario con las 4 métricas y el número de observaciones.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    # Filtrar NaN
    mask = ~(np.isnan(y_true) | np.isnan(y_pred))
    y_true, y_pred = y_true[mask], y_pred[mask]

    if len(y_true) == 0:
        return {"mae": np.nan, "rmse": np.nan, "mape": np.nan, "smape": np.nan, "n": 0}

    mae_val = np.mean(np.abs(y_true - y_pred))
    rmse_val = np.sqrt(np.mean((y_true - y_pred) ** 2))

    mask_nonzero = np.abs(y_true) > 1e-6
    mape_val = (
        np.mean(np.abs((y_true[mask_nonzero] - y_pred[mask_nonzero]) / y_true[mask_nonzero])) * 100
        if mask_nonzero.any() else np.nan
    )

    den = (np.abs(y_true) + np.abs(y_pred)) / 2
    mask_smape = den > 0
    smape_val = (
        np.mean(np.abs(y_true[mask_smape] - y_pred[mask_smape]) / den[mask_smape]) * 100
        if mask_smape.any() else 0.0
    )

    return {
        "mae": round(mae_val, 4),
        "rmse": round(rmse_val, 4),
        "mape": round(mape_val, 4),
        "smape": round(smape_val, 4),
        "n": int(len(y_true)),
    }
```

---

## Métricas por segmento

⚠️ **No reportes solo métricas globales.** Reporta también por segmento ABC/XYZ:

```python
def metricas_por_segmento(df_eval: pd.DataFrame) -> pd.DataFrame:
    """df_eval debe tener columnas: y_true, y_pred, segmento_abc_xyz."""
    filas = []
    for segmento, sub in df_eval.groupby("segmento_abc_xyz"):
        m = calcular_metricas(sub["y_true"], sub["y_pred"])
        m["segmento"] = segmento
        filas.append(m)
    return pd.DataFrame(filas)[["segmento", "n", "mae", "rmse", "mape", "smape"]]
```

Ejemplo de tabla esperada en el informe:

| Segmento | n | MAE | RMSE | MAPE | sMAPE |
|---|---|---|---|---|---|
| AX | 200 | 4.2 | 5.8 | 7.1 | 7.0 |
| AY | 150 | 8.7 | 14.3 | 18.2 | 17.9 |
| AZ | 50 | 12.1 | 25.4 | NaN | 65.3 |
| BX | 400 | 3.5 | 5.0 | 9.5 | 9.2 |
| ... | ... | ... | ... | ... | ... |

**Lectura típica:** los segmentos X tienen errores bajos (demanda estable, fácil de predecir), los Z tienen errores altos (demanda errática, difícil).

---

## Comparación entre modelos

Tabla final de comparación que debe ir al informe:

```python
modelos = {
    "Baseline (media 4 sem)": y_pred_baseline,
    "LightGBM": y_pred_lgb,
    "XGBoost": y_pred_xgb,
    "Prophet (top 50)": y_pred_prophet,
}

filas = []
for nombre, preds in modelos.items():
    m = calcular_metricas(y_valid, preds)
    m["modelo"] = nombre
    filas.append(m)

tabla = pd.DataFrame(filas)[["modelo", "n", "mae", "rmse", "mape", "smape"]]
print(tabla.to_string(index=False))
```

Salida esperada:

```
modelo                    n     mae    rmse    mape   smape
Baseline (media 4 sem)  8500   12.40   18.50   25.30   23.10
LightGBM                8500    7.20   11.40   15.80   14.20
XGBoost                 8500    7.50   11.90   16.40   14.80
Prophet (top 50)         400    6.10    9.80   12.30   11.50
```

**Criterio de selección del modelo principal:** menor MAE (o menor MAPE, dependiendo de la prioridad del negocio).

---

## Guardar métricas a MySQL

Insertar en la tabla `metricas_modelos`:

```python
metricas_df = pd.DataFrame([
    {
        "modelo": "lightgbm_v1",
        "segmento_abc_xyz": "GLOBAL",
        "mae": 7.20, "rmse": 11.40, "mape": 15.80,
        "num_skus": 600,
        "horizonte_semanas": 4,
    },
    # ... una fila por segmento
])
metricas_df.to_sql("metricas_modelos", engine, if_exists="append", index=False)
```

---

## Visualizaciones obligatorias

Para cada modelo, generar y guardar en `reports/figures/`:

1. **Scatter `y_true` vs `y_pred`** — debe estar cerca de la diagonal.
2. **Histograma de residuales** — ideal centrado en cero, simétrico.
3. **Residuales vs `y_pred`** — para detectar heterocedasticidad.
4. **Curvas reales vs predichas para 5–10 SKUs ejemplo** (1 AX, 1 AY, 1 BX, 1 CZ, etc.).

```python
import matplotlib.pyplot as plt

# Scatter
fig, ax = plt.subplots(figsize=(8, 8))
ax.scatter(y_valid, y_pred_valid, alpha=0.3, s=10)
lims = [0, max(y_valid.max(), y_pred_valid.max())]
ax.plot(lims, lims, "r--", linewidth=1)
ax.set_xlabel("Real")
ax.set_ylabel("Predicción")
ax.set_title("LightGBM — Validación")
fig.savefig("reports/figures/lgb_scatter.png", dpi=120, bbox_inches="tight")
plt.close(fig)
```

---

## Reglas no negociables

1. **SIEMPRE reportar MAE, RMSE, MAPE juntos.**
2. **NUNCA reportar solo métrica global.** Hay que segmentar por ABC/XYZ.
3. **Usar sMAPE** cuando hay muchos ceros (segmento Z).
4. **El baseline debe estar en la tabla comparativa.**
5. **NO redondear excesivamente.** Usar 4 decimales en el cálculo, redondear al reportar.
6. **GUARDAR las métricas en `metricas_modelos`** para que Tableau pueda graficarlas.
7. **NO usar `from sklearn.metrics import mean_absolute_percentage_error`** porque la versión nueva lanza warnings con ceros. Usar la implementación propia.
