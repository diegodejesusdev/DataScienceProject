---
name: etl-pipeline
description: Cómo construir el pipeline ETL del proyecto ConstruNorte. Cubre la carga del CSV crudo, la limpieza, la anonimización (Ley 1581) y la agregación a granularidad semanal por SKU. Léeme antes de procesar el CSV o cargar datos a MySQL.
---

# Pipeline ETL — ConstruNorte

## Flujo general

```
CSV crudo (~600K filas, 33 columnas)
    │
    ▼ [Apache Hop, flujo visual]
ventas_crudas (MySQL)         ← solo las columnas que se retienen, ya sin personales
    │
    ▼ [Python, src/etl.py]
ventas_crudas limpio         ← deduplicación, normalización
    │
    ▼ [src/features.py]
ventas_semanales              ← agregación a granularidad (item × año × semana × centro)
```

---

## Variables del CSV crudo

### RETENER (estas son las útiles)
| Columna CSV | Renombrar a | Tipo |
|---|---|---|
| `Fecha` | `fecha` | DATE |
| `Item` | `item` | VARCHAR(50) |
| `Nombre Item` | `nombre_item` | VARCHAR(255) |
| `Referencia Item` | `referencia_item` | VARCHAR(100) |
| `Codigo Barra Item` | `codigo_barra` | VARCHAR(50) |
| `Unidad Inventario 1 Item` | `unidad_inventario` | VARCHAR(20) |
| `Proveedor Codigo Item` | `proveedor_codigo` | VARCHAR(50) |
| `Proveedor Nombre Item` | `proveedor_nombre` | VARCHAR(255) |
| `Nombre Linea N1` | `nombre_linea_n1` | VARCHAR(100) |
| `Nombre Linea N2` | `nombre_linea_n2` | VARCHAR(100) |
| `Centro de Operacion` | `centro_operacion` | VARCHAR(20) |
| `Tipo de Documento` | `tipo_documento` | VARCHAR(20) |
| `Cantidad 1` | `cantidad` | DECIMAL(18,4) |
| `Precio Uni` | `precio_unitario` | DECIMAL(18,4) |
| `Valor Bruto` | `valor_bruto` | DECIMAL(18,4) |
| `Valor Costo` | `valor_costo` | DECIMAL(18,4) |
| `Peso` | `peso` | DECIMAL(18,4) |

### ELIMINAR (datos personales — Ley 1581)
- `Cliente`, `Nombre Cliente`, `Direccion Cliente`, `Nit Cliente`
- `Ciudad Cliente`, `Ciudad Descripcion Cliente`, `Nombre Criterio Cliente 1`
- `Vendedor`, `Nombre Vendedor`, `Cedula Vendedor`
- `Documento Remision`, `Documento Ventas`, `Documento Pedido`
- `Lapso`, `Cargue`, `Centro de Operacion RM`, `Fecha Remision`, `Fecha Pedido` (no aportan al modelo)

⚠️ La eliminación se hace **en el primer paso del ETL**, antes de escribir a MySQL.

---

## Paso 1 — Lectura y normalización del CSV

```python
import pandas as pd
from pathlib import Path

CSV_PATH = Path("data/raw/ventas_construnorte.csv")

# Columnas a retener (lectura selectiva ahorra memoria)
COLUMNAS_UTILES = [
    "Fecha", "Item", "Nombre Item", "Referencia Item", "Codigo Barra Item",
    "Unidad Inventario 1 Item", "Proveedor Codigo Item", "Proveedor Nombre Item",
    "Nombre Linea N1", "Nombre Linea N2", "Centro de Operacion", "Tipo de Documento",
    "Cantidad 1", "Precio Uni", "Valor Bruto", "Valor Costo", "Peso",
]

df = pd.read_csv(
    CSV_PATH,
    sep=";",                     # ⚠️ el CSV viene separado por ;
    usecols=COLUMNAS_UTILES,
    dtype=str,                   # leer todo como string, casteamos después con seguridad
    encoding="utf-8",            # si falla, probar "latin-1"
)

# Renombrar columnas
df = df.rename(columns={
    "Fecha": "fecha",
    "Item": "item",
    "Nombre Item": "nombre_item",
    "Referencia Item": "referencia_item",
    "Codigo Barra Item": "codigo_barra",
    "Unidad Inventario 1 Item": "unidad_inventario",
    "Proveedor Codigo Item": "proveedor_codigo",
    "Proveedor Nombre Item": "proveedor_nombre",
    "Nombre Linea N1": "nombre_linea_n1",
    "Nombre Linea N2": "nombre_linea_n2",
    "Centro de Operacion": "centro_operacion",
    "Tipo de Documento": "tipo_documento",
    "Cantidad 1": "cantidad",
    "Precio Uni": "precio_unitario",
    "Valor Bruto": "valor_bruto",
    "Valor Costo": "valor_costo",
    "Peso": "peso",
})
```

---

## Paso 2 — Conversión de tipos

El CSV de ConstruNorte trae fechas en formato `YYYYMMDD` (entero) y números con coma decimal en algunos casos:

```python
# Fecha: viene como 20240315 → datetime
df["fecha"] = pd.to_datetime(df["fecha"], format="%Y%m%d", errors="coerce")

# Numéricos: reemplazar coma por punto y convertir
columnas_numericas = ["cantidad", "precio_unitario", "valor_bruto", "valor_costo", "peso"]
for col in columnas_numericas:
    df[col] = (
        df[col]
        .astype(str)
        .str.replace(",", ".", regex=False)
        .str.strip()
    )
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Strings: normalizar
columnas_texto = ["item", "nombre_item", "referencia_item", "centro_operacion", "tipo_documento"]
for col in columnas_texto:
    df[col] = df[col].astype(str).str.strip().str.upper()

# Reportar nulos detectados
print(df.isna().sum())
```

---

## Paso 3 — Filtrado por tipo de documento

⚠️ **Decisión técnica crítica.** El dataset incluye remisiones, ventas y pedidos. Para forecasting de demanda real hay que decidir cuál cuenta.

**Por defecto, retener solo las transacciones de venta efectiva.** El valor exacto de `Tipo de Documento` que corresponde debe confirmarse con ConstruNorte. Plantilla:

```python
TIPOS_DOC_VENTA = ["J1"]  # ⚠️ confirmar con la organización

df = df[df["tipo_documento"].isin(TIPOS_DOC_VENTA)].copy()
print(f"Filas tras filtrar por tipo documento: {len(df):,}")
```

Si la cantidad cae demasiado, revisa qué tipos hay y ajusta la lista.

---

## Paso 4 — Limpieza de outliers y errores

```python
# Cantidad y valor no pueden ser negativos
df = df[df["cantidad"] > 0].copy()
df = df[df["valor_bruto"] >= 0].copy()

# Eliminar duplicados exactos
n_antes = len(df)
df = df.drop_duplicates()
print(f"Duplicados eliminados: {n_antes - len(df):,}")

# Eliminar filas sin fecha o sin item
df = df.dropna(subset=["fecha", "item"]).copy()

# Validar rango de fechas esperado
assert df["fecha"].min() >= pd.Timestamp("2023-12-01"), "Fechas anteriores al periodo esperado"
assert df["fecha"].max() <= pd.Timestamp("2026-06-30"), "Fechas posteriores al periodo esperado"
```

**NO eliminar outliers por IQR sobre cantidad o valor.** En materiales de construcción, los outliers de volumen son ventas reales a obras grandes y NO deben eliminarse. Si sospechas de errores, marcalos pero no los borres.

---

## Paso 5 — Carga a `ventas_crudas` en MySQL

```python
from src.db import get_engine
from sqlalchemy import text

engine = get_engine()

# Truncar antes para cargas idempotentes
with engine.begin() as conn:
    conn.execute(text("TRUNCATE TABLE ventas_crudas"))

df.to_sql(
    "ventas_crudas",
    engine,
    if_exists="append",
    index=False,
    chunksize=10_000,
    method="multi",
)

# Validar
with engine.connect() as conn:
    n = conn.execute(text("SELECT COUNT(*) FROM ventas_crudas")).scalar()
print(f"Filas cargadas en ventas_crudas: {n:,}")
```

---

## Paso 6 — Construir `dim_producto`

```python
dim = (
    df.groupby("item")
    .agg(
        nombre_item=("nombre_item", "last"),
        referencia_item=("referencia_item", "last"),
        unidad_inventario=("unidad_inventario", "last"),
        proveedor_codigo=("proveedor_codigo", "last"),
        proveedor_nombre=("proveedor_nombre", "last"),
        nombre_linea_n1=("nombre_linea_n1", "last"),
        nombre_linea_n2=("nombre_linea_n2", "last"),
        fecha_primera_venta=("fecha", "min"),
        fecha_ultima_venta=("fecha", "max"),
    )
    .reset_index()
)

# Marcar productos activos (con venta en los últimos 90 días)
fecha_corte = df["fecha"].max() - pd.Timedelta(days=90)
dim["activo"] = (dim["fecha_ultima_venta"] >= fecha_corte).astype(int)

with engine.begin() as conn:
    conn.execute(text("TRUNCATE TABLE dim_producto"))
dim.to_sql("dim_producto", engine, if_exists="append", index=False)
```

---

## Paso 7 — Agregar a `ventas_semanales`

Granularidad de modelado: **`(item, centro_operacion, año, semana)`**.

```python
df["anio"] = df["fecha"].dt.isocalendar().year.astype(int)
df["semana"] = df["fecha"].dt.isocalendar().week.astype(int)

# Inicio de la semana ISO (lunes)
df["fecha_inicio_semana"] = df["fecha"] - pd.to_timedelta(df["fecha"].dt.weekday, unit="D")
df["fecha_inicio_semana"] = df["fecha_inicio_semana"].dt.normalize()

ventas_semanales = (
    df.groupby(["item", "centro_operacion", "anio", "semana", "fecha_inicio_semana"])
    .agg(
        cantidad_total=("cantidad", "sum"),
        valor_bruto_total=("valor_bruto", "sum"),
        num_transacciones=("cantidad", "count"),
    )
    .reset_index()
)

with engine.begin() as conn:
    conn.execute(text("TRUNCATE TABLE ventas_semanales"))
ventas_semanales.to_sql(
    "ventas_semanales", engine,
    if_exists="append", index=False, chunksize=10_000, method="multi"
)
```

---

## Paso 8 — Validación final

```python
with engine.connect() as conn:
    print("ventas_crudas:", conn.execute(text("SELECT COUNT(*) FROM ventas_crudas")).scalar())
    print("dim_producto:", conn.execute(text("SELECT COUNT(*) FROM dim_producto")).scalar())
    print("ventas_semanales:", conn.execute(text("SELECT COUNT(*) FROM ventas_semanales")).scalar())

    # Coherencia: la suma de cantidad debe coincidir entre tablas
    q1 = conn.execute(text("SELECT SUM(cantidad) FROM ventas_crudas")).scalar()
    q2 = conn.execute(text("SELECT SUM(cantidad_total) FROM ventas_semanales")).scalar()
    print(f"Suma cantidades coherente: {q1 == q2} ({q1} vs {q2})")
```

---

## Apache Hop

El ETL **también** se documenta como un flujo visual en Apache Hop (`hop/etl_construnorte.hpl`). Esto sirve para:
- Mostrar el pipeline en el informe (es muy visual).
- Defender la ingeniería de datos en la sustentación.

Pasos del flujo en Hop, en orden:
1. **CSV File Input** — leer `data/raw/ventas_construnorte.csv` con separador `;`.
2. **Select Values** — retener solo las 17 columnas útiles.
3. **Field Conversion** — castear fecha y números.
4. **Filter Rows** — `tipo_documento IN ('J1')`.
5. **Filter Rows** — `cantidad > 0 AND valor_bruto >= 0`.
6. **Unique Rows** — eliminar duplicados.
7. **MySQL Bulk Loader** — escribir a `ventas_crudas`.

La agregación a `ventas_semanales` se hace en Python (es más fluido).

---

## Reglas no negociables

1. **Eliminar columnas personales SIEMPRE en el primer paso.**
2. **NO eliminar outliers de cantidad/valor.** Son ventas reales.
3. **Toda carga debe terminar con validación `COUNT(*)`.**
4. **El ETL debe ser idempotente.** Volver a correrlo da el mismo resultado (por eso `TRUNCATE + append`).
5. **Documentar todo paso con `logger.info()`** en `src/etl.py`.
6. **El CSV crudo NUNCA se commitea.** Vive solo en `data/raw/` (gitignored).
