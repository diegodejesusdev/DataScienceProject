---
name: feature-engineering
description: Cómo crear features para forecasting de demanda (lags, medias móviles, calendario, festivos, estacionalidad). Léeme antes de generar features para los modelos LightGBM, XGBoost o Prophet.
---

# Feature Engineering — Forecasting de demanda

## Principios

1. **Toda feature se calcula sobre `ventas_semanales`** (granularidad item × centro × año × semana).
2. **Las features de rezago (lags) NUNCA usan información del futuro.** Para la fila de la semana W, solo se permiten valores de semanas estrictamente anteriores.
3. **Por SKU + centro de operación.** Los lags y rolling means se calculan dentro de cada grupo `(item, centro_operacion)`.
4. **Ordenar SIEMPRE por fecha** antes de calcular lags. Olvidar esto es el error más común.

---

## Estructura base

```python
import pandas as pd
from src.db import get_engine

engine = get_engine()
df = pd.read_sql("SELECT * FROM ventas_semanales ORDER BY item, centro_operacion, fecha_inicio_semana", engine)

# Asegurar ordenamiento
df = df.sort_values(["item", "centro_operacion", "fecha_inicio_semana"]).reset_index(drop=True)
```

---

## Features de calendario (sin riesgo de leakage)

Estas se derivan solo de la fecha, así que siempre son seguras:

```python
df["anio"] = df["fecha_inicio_semana"].dt.year
df["mes"] = df["fecha_inicio_semana"].dt.month
df["semana_iso"] = df["fecha_inicio_semana"].dt.isocalendar().week.astype(int)
df["trimestre"] = df["fecha_inicio_semana"].dt.quarter
df["dia_del_anio"] = df["fecha_inicio_semana"].dt.dayofyear

# Indicadores cíclicos (importantes para que el modelo capte estacionalidad)
import numpy as np
df["mes_sin"] = np.sin(2 * np.pi * df["mes"] / 12)
df["mes_cos"] = np.cos(2 * np.pi * df["mes"] / 12)
df["semana_sin"] = np.sin(2 * np.pi * df["semana_iso"] / 52)
df["semana_cos"] = np.cos(2 * np.pi * df["semana_iso"] / 52)
```

### Festivos de Colombia
```python
import holidays
co_holidays = holidays.country_holidays("CO", years=range(2024, 2027))

# Contar festivos en la semana
def festivos_en_semana(fecha_inicio):
    return sum(1 for i in range(7) if (fecha_inicio + pd.Timedelta(days=i)) in co_holidays)

df["num_festivos_semana"] = df["fecha_inicio_semana"].apply(festivos_en_semana)
```

---

## Features de rezago (lags)

⚠️ **Estas son las más propensas a errores. Atención máxima.**

```python
# El shift se hace POR GRUPO (item, centro_operacion)
grupo = df.groupby(["item", "centro_operacion"])

# Lag 1 = la cantidad de la semana ANTERIOR
df["lag_1"] = grupo["cantidad_total"].shift(1)

# Otros lags útiles
df["lag_2"] = grupo["cantidad_total"].shift(2)
df["lag_4"] = grupo["cantidad_total"].shift(4)    # un mes atrás
df["lag_8"] = grupo["cantidad_total"].shift(8)    # dos meses atrás
df["lag_13"] = grupo["cantidad_total"].shift(13)  # un trimestre atrás
df["lag_52"] = grupo["cantidad_total"].shift(52)  # mismo periodo año anterior
```

### Validación crítica
```python
# Verificar que el lag_1 de la primera observación de cada SKU es NaN
primer_registro = df.groupby(["item", "centro_operacion"]).head(1)
assert primer_registro["lag_1"].isna().all(), "Error: lag_1 no es NaN en primeras observaciones"
```

---

## Medias móviles (rolling)

⚠️ **Usar `shift(1)` ANTES del rolling para no incluir la semana actual.**

```python
# Media móvil de 4 semanas (excluyendo la semana actual)
df["rolling_mean_4"] = (
    grupo["cantidad_total"]
    .shift(1)            # primero excluir semana actual
    .rolling(window=4, min_periods=1)
    .mean()
    .reset_index(drop=True)
)

# Media móvil de 13 semanas
df["rolling_mean_13"] = (
    grupo["cantidad_total"]
    .shift(1)
    .rolling(window=13, min_periods=1)
    .mean()
    .reset_index(drop=True)
)

# Desviación estándar móvil (mide volatilidad)
df["rolling_std_4"] = (
    grupo["cantidad_total"]
    .shift(1)
    .rolling(window=4, min_periods=2)
    .std()
    .reset_index(drop=True)
)
```

### Por qué `shift(1)` antes del rolling
Si no lo haces, el rolling de la semana W incluye la propia semana W, lo cual es leakage.

✅ Correcto: `rolling_mean_4` en W = promedio de (W-4, W-3, W-2, W-1)
❌ Incorrecto: `rolling_mean_4` en W = promedio de (W-3, W-2, W-1, W)

---

## Features de tendencia

```python
# Diferencias (cambio respecto a la semana anterior)
df["diff_1"] = grupo["cantidad_total"].diff(1)

# Razón con el promedio histórico (cuánto se desvía del promedio del SKU)
media_sku = grupo["cantidad_total"].transform("mean")
df["ratio_vs_media"] = df["cantidad_total"] / media_sku.replace(0, np.nan)
```

---

## Features categóricas

Para LightGBM y XGBoost, las categóricas pueden ir como `category` o codificadas.

### Opción A — Codificación numérica (recomendada)
```python
from sklearn.preprocessing import LabelEncoder

CATEGORICAS = ["item", "centro_operacion", "nombre_linea_n1", "nombre_linea_n2", "proveedor_codigo"]

encoders = {}
for col in CATEGORICAS:
    if col in df.columns:
        le = LabelEncoder()
        df[f"{col}_enc"] = le.fit_transform(df[col].astype(str))
        encoders[col] = le

# Guardar encoders para inferencia
import joblib
joblib.dump(encoders, "models/label_encoders.pkl")
```

### Opción B — Tipo `category` nativo (LightGBM lo soporta)
```python
for col in CATEGORICAS:
    df[col] = df[col].astype("category")

# En LightGBM:
lgb.train(..., categorical_feature=CATEGORICAS)
```

---

## Features de SKU agregadas

Calcular estadísticas históricas por SKU (calculadas SOLO sobre el período de training):

```python
fecha_corte_train = "2025-09-30"  # ejemplo

# Solo usar datos antes del corte para no filtrar el futuro
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
```

---

## Features de ABC/XYZ

Estas vienen de `clasificacion_abc_xyz` y son features de segmento:

```python
abc = pd.read_sql("SELECT item, clase_abc, clase_xyz, segmento_abc_xyz FROM clasificacion_abc_xyz", engine)
df = df.merge(abc, on="item", how="left")

# Codificar para el modelo
df["clase_abc_num"] = df["clase_abc"].map({"A": 1, "B": 2, "C": 3})
df["clase_xyz_num"] = df["clase_xyz"].map({"X": 1, "Y": 2, "Z": 3})
```

---

## Manejo de NaN en features de lag

Los lags introducen NaN al inicio de cada serie (no hay historia previa).

**Opciones, en orden de preferencia:**

1. **Dejar como NaN** y que LightGBM/XGBoost los manejen (lo hacen bien por defecto).
2. **Llenar con 0** — solo si tienes razón para creer que "sin venta = 0".
3. **Eliminar las filas iniciales** — solo en SKUs con mucha historia.

```python
# Opción 1 (recomendada)
# No hacer nada, LightGBM/XGBoost los entienden

# Opción 3: filtrar SKUs con menos de N semanas de historia
n_semanas_min = 12
counts = df.groupby("item")["fecha_inicio_semana"].count()
items_validos = counts[counts >= n_semanas_min].index
df = df[df["item"].isin(items_validos)].copy()
```

---

## Imputación de "semanas sin venta"

Si un SKU no se vendió en cierta semana, la fila no existe en `ventas_semanales`. Hay que decidir: ¿es ausencia de información, o es un cero?

**Recomendación: rellenar con cero las semanas faltantes para SKUs activos.**

```python
# Crear un grid completo de (item × centro × semana) y hacer merge
fechas_completas = pd.date_range(
    df["fecha_inicio_semana"].min(),
    df["fecha_inicio_semana"].max(),
    freq="W-MON",
)

combinaciones = (
    df[["item", "centro_operacion"]]
    .drop_duplicates()
)

grid = combinaciones.merge(
    pd.DataFrame({"fecha_inicio_semana": fechas_completas}),
    how="cross"
)

df_completo = grid.merge(df, on=["item", "centro_operacion", "fecha_inicio_semana"], how="left")
df_completo["cantidad_total"] = df_completo["cantidad_total"].fillna(0)
df_completo["valor_bruto_total"] = df_completo["valor_bruto_total"].fillna(0)
df_completo["num_transacciones"] = df_completo["num_transacciones"].fillna(0).astype(int)
```

⚠️ Esto puede inflar mucho el dataset. Para 600 SKUs × 100 semanas × 5 centros = 300.000 filas. Está bien.

---

## Lista final recomendada de features para el modelo principal

| Feature | Tipo | Origen |
|---|---|---|
| `item_enc` | categórica | LabelEncoder |
| `centro_operacion_enc` | categórica | LabelEncoder |
| `nombre_linea_n1_enc` | categórica | LabelEncoder |
| `nombre_linea_n2_enc` | categórica | LabelEncoder |
| `proveedor_codigo_enc` | categórica | LabelEncoder |
| `mes`, `semana_iso`, `trimestre` | numérica | Calendario |
| `mes_sin`, `mes_cos` | numérica | Calendario cíclico |
| `num_festivos_semana` | numérica | Festivos CO |
| `lag_1`, `lag_2`, `lag_4`, `lag_8`, `lag_52` | numérica | Rezagos |
| `rolling_mean_4`, `rolling_mean_13` | numérica | Medias móviles |
| `rolling_std_4` | numérica | Volatilidad |
| `diff_1`, `ratio_vs_media` | numérica | Tendencia |
| `sku_media`, `sku_mediana`, `sku_std` | numérica | Estadísticas SKU |
| `clase_abc_num`, `clase_xyz_num` | numérica | ABC/XYZ |

**Variable objetivo:** `cantidad_total` (la cantidad vendida en la semana).

---

## Reglas no negociables

1. **SIEMPRE `sort_values` antes de calcular lags.**
2. **SIEMPRE agrupar por `(item, centro_operacion)` para los shifts y rollings.**
3. **NUNCA usar la semana actual en su propio rolling.** `shift(1)` antes de `rolling`.
4. **NUNCA calcular `sku_media` global sobre todo el dataset.** Solo sobre train.
5. **NUNCA imputar lags con la media de toda la columna.** Es leakage.
6. **DOCUMENTAR cada feature** en `docs/03_preparacion_datos.md` con su definición exacta.
