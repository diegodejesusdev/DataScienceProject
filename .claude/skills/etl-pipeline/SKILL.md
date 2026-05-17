---
name: etl-pipeline
description: Como construir el pipeline ETL del proyecto. Apache Hop hace SOLO la ingesta inicial del CSV a `ventas_staging`; todo lo demas (tipificacion, filtrado, agregacion) es Python. Leeme antes de procesar el CSV o cargar datos a MySQL.
---

# Pipeline ETL — ConstruNorte

## Division de responsabilidades

| Etapa | Herramienta | Justificacion |
|---|---|---|
| 1. Ingesta del CSV crudo | **Apache Hop** | Visual, demostrable, cumple requisito academico |
| 2. Tipificacion, filtrado por tipo de documento y periodo | **Python** | Logica condicional y de fechas |
| 3. Construir `dim_producto` y `ventas_semanales` | **Python** | Agregaciones complejas |
| 4. Feature engineering, ABC/XYZ, modelado | **Python** | Obvio |

**Regla:** Apache Hop solo escribe en `ventas_staging`. Todo lo que toca otras tablas se hace en Python.

---

## Flujo general

```
CSV crudo (35 columnas, ~600K filas, 2022 + 2024-2025 + 2026)
    |
    v [Apache Hop — 3 pasos visuales]
ventas_staging (15 columnas como String, sin personales)
    |
    v [Python: src/etl.py]
ventas_crudas (tipificada, filtrada, sin tipo_documento, 14 columnas)
    |
    v
dim_producto + ventas_semanales
```

---

## Parte 1 — Apache Hop (UN flujo, 3 steps)

### Step 1 — `Text File Input`

- **File:** ruta al CSV en `data/raw/ventas_construnorte.csv`
- **Content:**
  - Filetype: `CSV`
  - Separator: `;`
  - Enclosure: `"`
  - Header: si (1 linea)
  - Encoding: `UTF-8`
- **Fields:** click "Get Fields" con muestreo de 1000 lineas. Hop detecta las 35 columnas. Despues:
  - Todas con `Type = String`
  - Limpiar Format, Length, Precision, Currency, Decimal, Group (dejar vacios)
  - Trim type = `none`
  - Repeat = `N`

### Step 2 — `Select Values`

En la pestana "Select & Alter", agregar SOLO estas 15 columnas y renombrar:

| # | Fieldname | Rename to |
|---|---|---|
| 1 | Centro_de_Operacion | centro_operacion |
| 2 | Item | item |
| 3 | Nombre_Item | nombre_item |
| 4 | Referencia_Item | referencia_item |
| 5 | Unidad_Inventario_1_Item | unidad_inventario |
| 6 | Proveedor_Codigo_Item | proveedor_codigo |
| 7 | Proveedor_Nombre_Item | proveedor_nombre |
| 8 | Fecha | fecha |
| 9 | Nombre_Linea_N1 | nombre_linea_n1 |
| 10 | Nombre_Linea_N2 | nombre_linea_n2 |
| 11 | Tipo_de_Documento | tipo_documento |
| 12 | Cantidad_1 | cantidad |
| 13 | Precio_Uni | precio_unitario |
| 14 | Valor_Bruto | valor_bruto |
| 15 | Valor_Costo | valor_costo |

**CRITICO:** "Include unspecified fields, ordered by name" DESMARCADO. Eso descarta las otras 20 columnas (personales, documentos internos, peso, codigo_barra, lapso, etc.).

### Step 3 — `Table Output`

- Connection: `construnorte_mysql`
- Target table: `ventas_staging`
- Commit size: `1000`
- Truncate table: SI
- Use batch update for inserts: SI
- Specify database fields: SI (mapeo 1:1 con los 15 campos)

---

## Parte 2 — Python (filtros + transformaciones)

### Funcion principal
```python
from src.etl import run_etl_desde_staging
run_etl_desde_staging()
```

O por CLI dentro del contenedor:
```bash
python -m src.etl
```

### Filtros aplicados (decisiones definitivas)

**Tipos de documento** (variable `TIPOS_DOC_VENTA = ["1E", "2E", "3E"]` en `src/etl.py`):

| Tipo | Significado | Decision |
|---|---|---|
| 1E, 2E, 3E | Ventas con facturacion electronica (una por bodega) | RETENER |
| J1, B1, L1 | Ventas previas a facturacion electronica (solo hasta nov 2022) | NO APLICA (fuera del periodo 2024-2025) |
| CM | Conversion de mercancia (~89 registros) | DESCARTAR |
| CT | Cotizaciones (no son ventas reales) | DESCARTAR |
| EN | Devoluciones | DESCARTAR (modelamos solo ventas brutas) |

**Periodo de analisis** (variables `FECHA_MIN`, `FECHA_MAX`):
- Solo 2024-01-01 a 2025-12-31 (continuo y completo).
- Se descartan 2022 (datos aislados, contexto distinto) y 2026 (incompletos).

**Otros filtros:**
- `cantidad > 0`
- `valor_bruto >= 0`
- `item` no nulo ni vacio
- `drop_duplicates()` exactos

**Despues de filtrar:**
- Se elimina la columna `tipo_documento` (ya cumplio su rol).
- Se cargan los datos a `ventas_crudas` con 14 columnas.

---

## Columnas finales en `ventas_crudas` (14)

| Columna | Tipo | Origen |
|---|---|---|
| fecha | DATE | YYYYMMDD parseado |
| item | VARCHAR(50) | SKU |
| nombre_item | VARCHAR(255) | descripcion del producto |
| referencia_item | VARCHAR(100) | codigo de referencia |
| unidad_inventario | VARCHAR(20) | UND, KG, M2, etc. |
| proveedor_codigo | VARCHAR(50) | codigo del proveedor |
| proveedor_nombre | VARCHAR(255) | nombre del proveedor |
| nombre_linea_n1 | VARCHAR(100) | linea de producto nivel 1 |
| nombre_linea_n2 | VARCHAR(100) | linea de producto nivel 2 |
| centro_operacion | VARCHAR(20) | bodega (001, 002, 003) |
| cantidad | DECIMAL(18,4) | unidades vendidas |
| precio_unitario | DECIMAL(18,4) | precio por unidad |
| valor_bruto | DECIMAL(18,4) | valor total de la venta |
| valor_costo | DECIMAL(18,4) | costo de la mercancia |

**Columnas descartadas y por que:**
- `Codigo_Barra_Item`: viene vacia en la muestra del CSV.
- `Peso`: informacion no veridica segun el equipo.
- `Tipo_de_Documento`: usado solo como filtro en Python, no es feature.
- Personales (Cliente, Vendedor, etc.): Ley 1581.
- Documentos internos (Remision, Ventas, Pedido): sin valor analitico.
- Control (Lapso, Cargue, Centro_RM, Fecha_Remision, Fecha_Pedido): sin valor analitico.

---

## Validacion post-ETL

```python
from src.db import get_engine
from sqlalchemy import text

engine = get_engine()
with engine.connect() as conn:
    print("ventas_staging:", conn.execute(text("SELECT COUNT(*) FROM ventas_staging")).scalar())
    print("ventas_crudas:", conn.execute(text("SELECT COUNT(*) FROM ventas_crudas")).scalar())
    print("dim_producto:", conn.execute(text("SELECT COUNT(*) FROM dim_producto")).scalar())
    print("ventas_semanales:", conn.execute(text("SELECT COUNT(*) FROM ventas_semanales")).scalar())

    # Verificar rango de fechas
    fechas = conn.execute(text("SELECT MIN(fecha), MAX(fecha) FROM ventas_crudas")).first()
    print(f"Rango fechas: {fechas[0]} -> {fechas[1]}")

    # Coherencia de cantidades
    q1 = conn.execute(text("SELECT SUM(cantidad) FROM ventas_crudas")).scalar()
    q2 = conn.execute(text("SELECT SUM(cantidad_total) FROM ventas_semanales")).scalar()
    print(f"Cantidades coherentes: {q1} vs {q2}")
```

Las fechas DEBEN estar entre 2024-01-01 y 2025-12-31.

---

## Reglas no negociables

1. **Apache Hop solo toca `ventas_staging`.** Nunca otras tablas.
2. **Las columnas personales se descartan en el Select Values de Hop.** Nunca tocan MySQL.
3. **El filtrado de tipos y periodo se hace SIEMPRE en Python.** Hop carga todo lo no-personal y Python decide que queda.
4. **Toda carga termina con validacion `COUNT(*)` y rango de fechas.**
5. **El ETL es idempotente.** TRUNCATE + append siempre.
6. **No eliminar outliers de cantidad/valor.** Son ventas reales.
7. **El CSV crudo vive solo en `data/raw/` (gitignored).** NUNCA se commitea.
