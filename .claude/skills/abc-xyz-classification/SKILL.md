---
name: abc-xyz-classification
description: Cómo construir la clasificación ABC (por valor) y XYZ (por variabilidad de demanda) sobre los SKUs. Léeme antes de calcular o usar las clases ABC/XYZ.
---

# Clasificación ABC/XYZ

## Concepto

- **ABC** ordena los SKUs por su contribución al valor total (Pareto).
- **XYZ** ordena los SKUs por la estabilidad de su demanda (coeficiente de variación).
- La **matriz ABC/XYZ** combina ambas en 9 segmentos.

Esto sirve para:
- Decidir qué SKUs vale la pena modelar a fondo (clases A, B con X o Y).
- Diseñar políticas de aprovisionamiento diferenciadas.
- Reportar al negocio dónde está concentrado el valor.

---

## Clasificación ABC

### Datos de entrada
`ventas_semanales` agregada por `item`, sumando `valor_bruto_total` sobre el periodo.

### Algoritmo
1. Sumar `valor_bruto_total` por `item`.
2. Ordenar de mayor a menor.
3. Calcular el porcentaje acumulado del valor total.
4. Aplicar cortes:
   - **A**: hasta 80% del valor acumulado.
   - **B**: del 80% al 95%.
   - **C**: del 95% al 100%.

### Implementación

```python
import pandas as pd
from src.db import get_engine

engine = get_engine()
df = pd.read_sql("SELECT item, valor_bruto_total FROM ventas_semanales", engine)

# Paso 1: sumar por SKU
valor_por_sku = df.groupby("item")["valor_bruto_total"].sum().reset_index()
valor_por_sku.columns = ["item", "valor_total_periodo"]

# Paso 2: ordenar descendente
valor_por_sku = valor_por_sku.sort_values("valor_total_periodo", ascending=False).reset_index(drop=True)

# Paso 3: porcentaje acumulado
valor_total = valor_por_sku["valor_total_periodo"].sum()
valor_por_sku["porcentaje_acumulado"] = (
    valor_por_sku["valor_total_periodo"].cumsum() / valor_total * 100
)

# Paso 4: clase
def asignar_abc(pct: float) -> str:
    if pct <= 80:
        return "A"
    elif pct <= 95:
        return "B"
    else:
        return "C"

valor_por_sku["clase_abc"] = valor_por_sku["porcentaje_acumulado"].apply(asignar_abc)

# Validar la distribución
print(valor_por_sku["clase_abc"].value_counts())
print(valor_por_sku.groupby("clase_abc")["valor_total_periodo"].sum())
```

### Validación esperada
- **Clase A**: ~20% de los SKUs, ~80% del valor.
- **Clase B**: ~30% de los SKUs, ~15% del valor.
- **Clase C**: ~50% de los SKUs, ~5% del valor.

Si la distribución difiere mucho de Pareto, no es error: es información de negocio.

---

## Clasificación XYZ

### Datos de entrada
`ventas_semanales` con todas las semanas de cada SKU.

### Algoritmo
1. Para cada SKU, calcular el **coeficiente de variación (CV)** sobre `cantidad_total`:
   ```
   CV = desviación_estándar / media
   ```
2. Aplicar cortes:
   - **X**: CV < 0.5 (demanda muy estable).
   - **Y**: CV entre 0.5 y 1.0 (variabilidad moderada).
   - **Z**: CV > 1.0 (demanda errática).

### Implementación

```python
import numpy as np

# Agrupar por SKU y calcular media y desviación
estats = (
    df.groupby("item")["cantidad_total"]
    .agg(media="mean", desvio="std", n_semanas="count")
    .reset_index()
)

# Coeficiente de variación
estats["coef_variacion"] = (
    estats["desvio"] / estats["media"].replace(0, np.nan)
)

# Para SKUs con muy pocas semanas o media cero, CV no aplica
estats["coef_variacion"] = estats["coef_variacion"].fillna(np.inf)

def asignar_xyz(cv: float) -> str:
    if cv < 0.5:
        return "X"
    elif cv <= 1.0:
        return "Y"
    else:
        return "Z"

estats["clase_xyz"] = estats["coef_variacion"].apply(asignar_xyz)
```

⚠️ **Cuidado:** SKUs con menos de 8 semanas de historia o con valores cero predominantes pueden dar CV poco confiable. Recomendación: marcarlos como Z explícitamente o excluirlos del cálculo y reportarlo aparte.

```python
# Marcar como "Z" automático SKUs con pocas semanas o muchos ceros
poca_historia = estats["n_semanas"] < 8
estats.loc[poca_historia, "clase_xyz"] = "Z"
```

---

## Importante: estabilidad calculada sobre serie continua

Si un SKU tiene semanas faltantes (no se vendió), el CV calculado solo sobre las semanas en que sí vendió es engañoso. **Antes de calcular XYZ, expande la serie a todas las semanas y rellena con cero las ausencias.**

```python
# Construir grid completo de semanas por SKU
todas_las_semanas = pd.date_range(
    df["fecha_inicio_semana"].min(),
    df["fecha_inicio_semana"].max(),
    freq="W-MON"
)

grid = (
    pd.DataFrame({"item": df["item"].unique()})
    .merge(pd.DataFrame({"fecha_inicio_semana": todas_las_semanas}), how="cross")
)

df_completo = grid.merge(
    df[["item", "fecha_inicio_semana", "cantidad_total"]],
    on=["item", "fecha_inicio_semana"],
    how="left"
)
df_completo["cantidad_total"] = df_completo["cantidad_total"].fillna(0)

# Ahora SÍ calcular CV sobre esta serie completa
# ... (mismo código que arriba)
```

---

## Combinar en matriz ABC/XYZ

```python
clasificacion = valor_por_sku.merge(estats, on="item", how="outer")
clasificacion["segmento_abc_xyz"] = (
    clasificacion["clase_abc"].fillna("C") + clasificacion["clase_xyz"].fillna("Z")
)

# Distribución de los 9 segmentos
matriz = (
    clasificacion.groupby(["clase_abc", "clase_xyz"])
    .agg(num_skus=("item", "count"), valor_total=("valor_total_periodo", "sum"))
    .reset_index()
)
print(matriz)
```

### Lectura de la matriz

| | X (estable) | Y (variable) | Z (errática) |
|---|---|---|---|
| **A** (alto valor) | **AX** — modelar a fondo, stock seguro | **AY** — modelar con estacionalidad | **AZ** — atención manual, alto riesgo |
| **B** (medio) | **BX** — política automatizada simple | **BY** — política moderada | **BZ** — pedido bajo demanda |
| **C** (bajo) | **CX** — punto de pedido fijo | **CY** — revisión periódica | **CZ** — candidatos a discontinuar |

---

## Cargar a MySQL

```python
clasificacion_final = clasificacion[[
    "item", "valor_total_periodo", "porcentaje_acumulado",
    "clase_abc", "coef_variacion", "clase_xyz", "segmento_abc_xyz"
]]

with engine.begin() as conn:
    conn.execute(text("TRUNCATE TABLE clasificacion_abc_xyz"))
clasificacion_final.to_sql(
    "clasificacion_abc_xyz", engine,
    if_exists="append", index=False
)
```

---

## Visualizaciones obligatorias para el informe

1. **Curva de Pareto**: % acumulado del valor vs % acumulado de SKUs (eje x). Muestra dónde caen los cortes A/B/C.
2. **Heatmap 3×3** de la matriz ABC/XYZ con conteo de SKUs en cada celda.
3. **Heatmap 3×3** con porcentaje del valor en cada celda (debería estar muy concentrado en la fila A).

---

## Reglas no negociables

1. **SIEMPRE usar serie completa (con ceros)** para calcular el CV de XYZ.
2. **NUNCA aplicar XYZ a SKUs con <8 semanas.** Marcarlos como Z por convención.
3. **CALCULAR ABC y XYZ una sola vez por corte temporal** del proyecto, no por cada experimento.
4. **GUARDAR la clasificación en MySQL** para que Tableau y los modelos la consulten.
5. **NUNCA modelar SKUs clase C con técnicas pesadas.** Para los CZ basta con un baseline o reportar "demanda esporádica".
