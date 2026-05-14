---
name: notebook-style
description: Cómo estructurar y escribir notebooks de Jupyter consistentes en el proyecto ConstruNorte. Léeme antes de crear o modificar cualquier `.ipynb`.
---

# Estilo de Notebooks

## Estructura obligatoria de todo notebook

Cada notebook debe tener esta estructura:

### 1. Celda Markdown de portada
```markdown
# 04 — Clasificación ABC/XYZ

**Objetivo:** Generar la clasificación ABC (por valor) y XYZ (por estabilidad) de los SKUs y almacenarla en `clasificacion_abc_xyz`.

**Inputs:**
- Tabla `ventas_semanales` (MySQL)

**Outputs:**
- Tabla `clasificacion_abc_xyz` (MySQL)
- `reports/figures/pareto_abc.png`
- `reports/figures/matriz_abc_xyz.png`

**Autor:** Diego Andrés De Jesús Montenegro
**Fecha:** 2026-05-10
```

### 2. Celda código — imports

```python
# =========================
# Imports
# =========================
import sys
from pathlib import Path

# Permitir importar módulos de src/
ROOT = Path().resolve().parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from src.db import get_engine
```

### 3. Celda código — configuración

```python
# =========================
# Configuración
# =========================
pd.set_option("display.max_columns", 50)
pd.set_option("display.width", 200)

sns.set_style("whitegrid")
plt.rcParams["figure.figsize"] = (10, 6)

# Rutas
FIGURES_DIR = ROOT / "reports" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Conexión a la BD
engine = get_engine()
```

### 4. Celdas de trabajo, agrupadas por sección Markdown

```markdown
## 1. Cargar datos
```
```python
# código
```
```markdown
## 2. Calcular clasificación ABC
```
```python
# código
```

Etc.

### 5. Celda Markdown final con conclusiones

```markdown
## Conclusiones

- Se clasificaron N SKUs en X% A, Y% B, Z% C.
- La matriz ABC/XYZ muestra que el segmento AX concentra el N% del valor.
- Próximo paso: usar la columna `segmento_abc_xyz` como feature en el modelado.
```

---

## Reglas de estilo

### Separadores visuales
Para separar bloques lógicos dentro de una celda larga:
```python
# =========================
# 1. Cargar datos
# =========================
df = pd.read_sql(...)

# =========================
# 2. Transformar
# =========================
df["nueva_col"] = ...
```

### Variables de configuración al inicio
Si el notebook tiene parámetros, ponlos en una celda al principio claramente identificada:
```python
# =========================
# PARÁMETROS DEL NOTEBOOK
# =========================
FECHA_FIN_TRAIN = "2025-09-30"
N_TOP_SKUS = 50
N_HORIZONTE_SEMANAS = 8
```

### Mostrar el progreso del trabajo
- Usar `df.shape`, `df.head()`, `df.info()` con liberalidad para entender los datos.
- Usar `print()` para reportar conteos importantes.
- Para procesos largos, usar `tqdm`:
  ```python
  from tqdm.auto import tqdm
  for sku in tqdm(top_skus, desc="Entrenando Prophet"):
      ...
  ```

### Gráficos
- Siempre guarda los gráficos relevantes en `reports/figures/`.
- Cierra las figuras después de guardarlas para no inflar la memoria:
  ```python
  fig, ax = plt.subplots()
  # ... dibujar
  fig.savefig(FIGURES_DIR / "mi_grafico.png", dpi=120, bbox_inches="tight")
  plt.close(fig)
  ```

### Outputs y peso del notebook
- **Antes de commitear**, limpia outputs pesados:
  ```bash
  jupyter nbconvert --clear-output --inplace notebooks/*.ipynb
  ```
- O usa `nbstripout`:
  ```bash
  pip install nbstripout
  nbstripout --install
  ```

---

## Numeración de notebooks

Por orden de ejecución, alineados con CRISP-DM:

| # | Notebook | Fase CRISP-DM |
|---|---|---|
| 01 | `01_perfil_inicial.ipynb` | Comprensión de datos |
| 02 | `02_eda.ipynb` | Comprensión de datos |
| 03 | `03_preparacion.ipynb` | Preparación |
| 04 | `04_abc_xyz.ipynb` | Preparación / Análisis |
| 05 | `05_baseline.ipynb` | Modelado |
| 06 | `06_lightgbm.ipynb` | Modelado |
| 07 | `07_xgboost.ipynb` | Modelado |
| 08 | `08_prophet.ipynb` | Modelado |
| 09 | `09_evaluacion_final.ipynb` | Evaluación |

---

## Anti-patrones (NO hacer)

❌ **Mezclar celdas de exploración con celdas finales.** Si exploraste algo y no aporta al resultado, bórralo antes del commit.

❌ **Reusar nombres de variable confusos.** Si tienes `df`, no uses también `df1`, `df2`, `df3`. Renombra a `df_crudo`, `df_limpio`, `df_modelable`.

❌ **Hardcodear rutas absolutas.**
```python
# ❌
df = pd.read_csv("/Users/diego/proyecto/data/raw/ventas.csv")

# ✅
df = pd.read_csv(ROOT / "data" / "raw" / "ventas.csv")
```

❌ **Definir funciones complejas en notebooks.** Si una función pasa de ~20 líneas o se va a reutilizar, muévela a `src/`.

❌ **Cargar el CSV en cada notebook.** Cárgalo desde MySQL si ya está allá. Los notebooks son consumidores de la BD, no productores.

❌ **Outputs gigantes en celdas (heatmaps con 600 SKUs).** Si la salida pesa más de 5 MB, repensar.

---

## Patrones recomendados

✅ **Cada notebook es atómico**: si lo corres de arriba a abajo, debe completarse sin errores.

✅ **Documentar decisiones técnicas inline.** Si tomas una decisión no obvia, explícala en Markdown:
```markdown
> **Decisión:** se excluyen SKUs con menos de 12 semanas de historia porque el modelo global necesita un mínimo de observaciones para los lags.
```

✅ **Mostrar la tabla intermedia.** No pases de paso a paso sin verificar:
```python
print(f"Antes del filtro: {len(df):,} filas")
df = df[df["fecha"] >= "2024-01-01"]
print(f"Después del filtro: {len(df):,} filas")
```

✅ **Para análisis exploratorios largos**, usar índice / tabla de contenido al inicio (con secciones bien nombradas, Jupyter las muestra automáticamente).

---

## Plantilla mínima de notebook nuevo

```python
# CELDA 1 (Markdown)
"""
# NN — Título

**Objetivo:**
**Inputs:**
**Outputs:**
**Autor:**
**Fecha:**
"""

# CELDA 2 (Code)
import sys
from pathlib import Path
ROOT = Path().resolve().parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from src.db import get_engine

# CELDA 3 (Code)
pd.set_option("display.max_columns", 50)
sns.set_style("whitegrid")
plt.rcParams["figure.figsize"] = (10, 6)

FIGURES_DIR = ROOT / "reports" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

engine = get_engine()

# CELDA 4 (Markdown)
"""
## 1. Cargar datos
"""

# CELDA 5 (Code)
df = pd.read_sql("SELECT * FROM ventas_semanales", engine)
print(f"Shape: {df.shape}")
df.head()
```

---

## Reglas no negociables

1. **TODO notebook empieza con celda de portada** (objetivo, inputs, outputs).
2. **NUNCA uses rutas absolutas.** Usa `ROOT / "subcarpeta"`.
3. **NUNCA mantengas outputs >5MB.** Limpia antes de commit.
4. **SIEMPRE guarda figuras importantes** en `reports/figures/`.
5. **SI una función supera 20 líneas o se reutiliza**, va a `src/`.
6. **SIEMPRE deja al final** una celda de conclusiones.
