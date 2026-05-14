---
name: project-conventions
description: Convenciones de código, estilo y organización del proyecto ConstruNorte. Léeme antes de crear cualquier archivo nuevo (script Python, notebook, módulo, SQL) para que el resultado sea coherente con el resto del repositorio.
---

# Convenciones del proyecto ConstruNorte

## Python

### Estilo
- **PEP 8** estricto.
- Indentación: 4 espacios, nunca tabs.
- Longitud máxima de línea: 100 caracteres.
- Codificación: UTF-8.
- **Type hints obligatorios** en toda función pública.
- **Docstrings** en formato Google:
  ```python
  def calcular_abc(df: pd.DataFrame, columna_valor: str = "valor_bruto") -> pd.DataFrame:
      """Calcula la clasificación ABC sobre el DataFrame agregado por SKU.

      Args:
          df: DataFrame con una fila por SKU.
          columna_valor: nombre de la columna que contiene el valor monetario.

      Returns:
          DataFrame con columnas `item`, `valor_total`, `porcentaje_acumulado`, `clase_abc`.
      """
  ```

### Nombres
- **Funciones, variables, módulos** → `snake_case`.
- **Clases** → `PascalCase`.
- **Constantes** → `UPPER_SNAKE_CASE`.
- **Dominio en español, técnica en inglés:**
  - ✅ `cantidad_total`, `valor_bruto`, `item`, `centro_operacion`
  - ✅ `train_test_split`, `model`, `predictions`
  - ❌ `totalQuantity`, `gross_value`, `Item`

### Imports
Orden y separación con líneas en blanco:
```python
# 1. Standard library
import os
from pathlib import Path
from datetime import date, timedelta

# 2. Third-party
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import lightgbm as lgb

# 3. Local
from src.db import get_engine
from src.features import build_features
```

### Logging vs print
- **En `src/` y módulos**: usar `logging`, no `print`.
  ```python
  import logging
  logger = logging.getLogger(__name__)
  logger.info("Cargando dataset...")
  ```
- **En notebooks**: `print()` está bien para explorar.

### Rutas
- **NUNCA** uses rutas absolutas (`/Users/diego/...`).
- **NUNCA** uses `os.path.join` (anticuado). Usa `pathlib.Path`.
- Define una constante `BASE_DIR` al inicio de cada script:
  ```python
  from pathlib import Path
  BASE_DIR = Path(__file__).resolve().parent.parent
  DATA_RAW = BASE_DIR / "data" / "raw"
  ```

---

## SQL

### Nombres
- Tablas y columnas en **`snake_case`**, en **español** para el dominio:
  - ✅ `ventas_semanales`, `cantidad_total`, `clase_abc`
  - ❌ `WeeklySales`, `totalQty`
- **Llave primaria** siempre se llama `id`.
- **Llaves foráneas** se llaman `<tabla_referida>_id`.

### Tipos
- Fechas → `DATE`.
- Timestamps → `TIMESTAMP DEFAULT CURRENT_TIMESTAMP`.
- IDs → `BIGINT AUTO_INCREMENT` para tablas de hechos, `VARCHAR` para identificadores de negocio (como `item`).
- Decimales monetarios → `DECIMAL(18,4)`. **Nunca** `FLOAT` o `DOUBLE` para dinero.
- Strings → `VARCHAR(N)` con N apropiado, no `TEXT` salvo necesidad.
- Booleanos → `TINYINT(1)`.

### Índices
- Toda llave foránea debe tener índice.
- Tablas grandes de hechos (`ventas_crudas`, `ventas_semanales`) deben tener índices en `fecha` e `item`.

---

## Notebooks

### Numeración
Los notebooks van numerados por orden de ejecución, alineados con CRISP-DM:
- `01_perfil_inicial.ipynb` — comprensión de datos
- `02_eda.ipynb` — análisis exploratorio
- `03_preparacion.ipynb` — limpieza y features
- `04_abc_xyz.ipynb` — clasificación
- `05_baseline.ipynb` — modelo baseline
- `06_lightgbm.ipynb` — LightGBM
- `07_xgboost.ipynb` — XGBoost
- `08_prophet.ipynb` — Prophet
- `09_evaluacion_final.ipynb` — comparación

### Estructura interna
- Primera celda Markdown: título, objetivo, inputs, outputs.
- Segunda celda código: imports.
- Tercera celda código: configuración (paths, conexión).
- Después: secciones con Markdown (`## Sección`).

Ver detalle completo en la skill `notebook-style/`.

---

## Git

### Mensajes de commit
- **Imperativo, en español.**
- **Con prefijo** del tipo de cambio:
  - `feat:` nueva funcionalidad
  - `fix:` corrección de bug
  - `docs:` documentación
  - `refactor:` reorganización sin cambio de comportamiento
  - `chore:` configuración, build, dependencias
  - `test:` tests
  - `wip:` trabajo en progreso (usar con moderación)

Ejemplos buenos:
- `feat: agregar clasificación ABC sobre ventas_semanales`
- `fix: corregir cálculo de coeficiente de variación en XYZ`
- `docs: actualizar README con instrucciones de Tableau`

Ejemplos malos:
- `cambios` ❌
- `update` ❌
- `WIP final` ❌

### Qué NO commitear
- `data/raw/*` y `data/processed/*` (excepto `.gitkeep`)
- `.env`
- `models/*.pkl`
- `mlruns/` (si llegara a crearse)
- Notebooks con outputs pesados (>1MB)
- Archivos del sistema operativo (`.DS_Store`, `Thumbs.db`)
- Carpetas de entornos virtuales (`venv/`, `.venv/`)
- `__pycache__/`, `.ipynb_checkpoints/`

### Ramas
- `main`: estable.
- `dev`: integración.
- `feature/<nombre>`: trabajo específico (ej. `feature/abc-xyz`).

---

## Documentación

### Cada módulo en `src/` debe tener:
1. Docstring de módulo arriba que explique qué hace.
2. Función `main()` o equivalente como punto de entrada.
3. Bloque `if __name__ == "__main__":`.

### Cada decisión técnica importante va a `docs/05_decisiones_tecnicas.md`:
- Por qué MySQL y no Postgres.
- Por qué LightGBM y no Random Forest.
- Por qué granularidad semanal y no diaria.
- Etc.

Esto sirve para la sustentación del proyecto.

---

## Reglas no negociables

1. **No commitear secretos.** Si por error subes una contraseña, hay que rotarla.
2. **No usar `pip install` global.** Si algo falta, va al `requirements.txt` y se hace rebuild.
3. **No usar `os.path`.** Usar `pathlib`.
4. **No usar `print` en `src/`.** Usar `logging`.
5. **No usar rutas absolutas.** Usar `BASE_DIR / "subcarpeta" / "archivo"`.
6. **No hacer split aleatorio en series de tiempo.** Particionar por fecha.
7. **No mezclar Markdown en mitad de un script Python.** Esos archivos son solo código.
