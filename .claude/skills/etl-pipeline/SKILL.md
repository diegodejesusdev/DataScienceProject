---
name: etl-pipeline
description: Como construir el pipeline ETL del proyecto. Apache Hop hace SOLO la ingesta inicial del CSV a una tabla de staging; todo lo demas (tipificacion, limpieza, agregacion) es Python. Leeme antes de procesar el CSV o cargar datos a MySQL.
---

# Pipeline ETL — ConstruNorte

## Division de responsabilidades

| Etapa | Herramienta | Justificacion |
|---|---|---|
| 1. Ingesta del CSV crudo | **Apache Hop** | Visual, defendible, cumple requisito academico. Hace SOLO ingesta. |
| 2. Tipificacion, limpieza, filtrado | **Python** | Logica condicional, manejo de fechas YYYYMMDD, normalizacion |
| 3. Construir `dim_producto` y `ventas_semanales` | **Python** | Agregaciones complejas |
| 4. Feature engineering, ABC/XYZ, modelado | **Python** | Obvio |

**Regla:** Apache Hop solo escribe en `ventas_staging`. Todo lo que toca otras tablas se hace en Python.

---

## Flujo general

```
CSV crudo (33 columnas, ~600K filas)
    |
    v [Apache Hop — 3 pasos visuales]
ventas_staging (MySQL, 17 columnas todas VARCHAR)
    |
    v [Python: src/etl.py — run_etl_desde_staging()]
ventas_crudas (tipificada, limpia, sin duplicados)
    |
    v [Python]
dim_producto (1 fila por SKU)
ventas_semanales (granularidad modelable)
```

---

## Parte 1 — Apache Hop (UN solo flujo, sencillo)

### Objetivo
Leer el CSV original y cargar las 17 columnas utiles a la tabla `ventas_staging` en MySQL, descartando las columnas con datos personales.

### Steps del flujo (`hop/ingesta_csv.hpl`)

**Step 1 — `Text File Input`**
- Filename: ruta al CSV (ej. `${PROJECT_HOME}/data/raw/ventas_construnorte.csv`)
- Separator: `;`
- Enclosure: `"`
- Encoding: `UTF-8`
- Header: si (1 linea)
- En la pestana "Fields", agregar las 17 columnas como `String`:
  ```
  Fecha, Item, Nombre Item, Referencia Item, Codigo Barra Item,
  Unidad Inventario 1 Item, Proveedor Codigo Item, Proveedor Nombre Item,
  Nombre Linea N1, Nombre Linea N2, Centro de Operacion, Tipo de Documento,
  Cantidad 1, Precio Uni, Valor Bruto, Valor Costo, Peso
  ```

**Step 2 — `Select Values`**
- En "Select & Alter", renombrar las columnas al formato snake_case:
  | Fieldname | Rename to |
  |---|---|
  | Fecha | fecha |
  | Item | item |
  | Nombre Item | nombre_item |
  | Referencia Item | referencia_item |
  | Codigo Barra Item | codigo_barra |
  | Unidad Inventario 1 Item | unidad_inventario |
  | Proveedor Codigo Item | proveedor_codigo |
  | Proveedor Nombre Item | proveedor_nombre |
  | Nombre Linea N1 | nombre_linea_n1 |
  | Nombre Linea N2 | nombre_linea_n2 |
  | Centro de Operacion | centro_operacion |
  | Tipo de Documento | tipo_documento |
  | Cantidad 1 | cantidad |
  | Precio Uni | precio_unitario |
  | Valor Bruto | valor_bruto |
  | Valor Costo | valor_costo |
  | Peso | peso |

**Step 3 — `Table Output`**
- Connection: conexion a MySQL del proyecto
- Target table: `ventas_staging`
- Truncate table: si (para hacerlo idempotente)
- Commit size: 1000
- Use batch update for inserts: si

### Conexion MySQL en Hop
- Connection name: `construnorte_mysql`
- Connection type: `MySQL`
- Host name: `localhost` (Hop corre nativo en el Mac)
- Port: `3306`
- Database name: el de tu `.env`
- Username / password: los de tu `.env`

### Reglas en Hop
- No agregar mas steps. El flujo debe quedar en 3 nodos.
- No tipificar en Hop (deja todo como `String`). Python se encarga.
- No filtrar filas en Hop (Python hace ese filtrado). La intencion es mantener Hop como una herramienta de ingesta pura.

---

## Parte 2 — Python (todo lo demas)

### Funcion principal
Modulo: `src/etl.py`, funcion: `run_etl_desde_staging()`.

```python
from src.etl import run_etl_desde_staging
run_etl_desde_staging()
```

O por linea de comandos dentro del contenedor Jupyter:

```bash
python -m src.etl --modo staging
```

### Pasos internos del pipeline Python

1. **`leer_staging(engine)`** — carga `SELECT * FROM ventas_staging` a un DataFrame.
2. **`normalizar_tipos(df)`** — convierte:
   - `fecha`: de string `YYYYMMDD` a `datetime` (`pd.to_datetime(..., format="%Y%m%d", errors="coerce")`)
   - numericos: reemplaza coma decimal por punto y casteo a `float` (`errors="coerce"`)
   - strings de identificadores: trim + upper
3. **`limpiar(df)`** — aplica los filtros:
   - Solo registros con `tipo_documento in TIPOS_DOC_VENTA` (variable global, hay que confirmar el codigo correcto con ConstruNorte)
   - `cantidad > 0`
   - `valor_bruto >= 0`
   - Elimina filas con `fecha` o `item` nulos
   - `drop_duplicates()`
4. **`cargar_ventas_crudas(df, engine)`** — TRUNCATE + append.
5. **`construir_dim_producto(df, engine)`** — agrupa por `item` con `agg` y marca `activo` segun ventas en los ultimos 90 dias.
6. **`construir_ventas_semanales(df, engine)`** — agrega a granularidad semanal por SKU x centro.

---

## Modo CSV directo (sin Hop)

Util para desarrollo, pruebas rapidas o ambientes donde Hop no esta disponible.

```bash
python -m src.etl --modo csv --csv data/raw/ventas_construnorte.csv
```

Esto salta `ventas_staging` y lee el CSV directamente con pandas. **Equivalente funcional** al modo staging, no es una via permitida para entregar el proyecto final (porque no usa Hop), pero es valido durante el desarrollo.

---

## Variables del CSV crudo

### RETENER (estas son las utiles)
| Columna CSV | Renombrar a | Tipo final (en Python) |
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

### DESCARTAR EN HOP (no se incluyen en el Text File Input)
- `Cliente`, `Nombre Cliente`, `Direccion Cliente`, `Nit Cliente`
- `Ciudad Cliente`, `Ciudad Descripcion Cliente`, `Nombre Criterio Cliente 1`
- `Vendedor`, `Nombre Vendedor`, `Cedula Vendedor`
- `Documento Remision`, `Documento Ventas`, `Documento Pedido`
- `Lapso`, `Cargue`, `Centro de Operacion RM`, `Fecha Remision`, `Fecha Pedido`

La anonimizacion ocurre en la **ingesta**. Los datos personales nunca tocan MySQL.

---

## Validacion final

Despues de correr el ETL completo, verificar:

```python
from src.db import get_engine
from sqlalchemy import text

engine = get_engine()
with engine.connect() as conn:
    print("ventas_staging:", conn.execute(text("SELECT COUNT(*) FROM ventas_staging")).scalar())
    print("ventas_crudas:", conn.execute(text("SELECT COUNT(*) FROM ventas_crudas")).scalar())
    print("dim_producto:", conn.execute(text("SELECT COUNT(*) FROM dim_producto")).scalar())
    print("ventas_semanales:", conn.execute(text("SELECT COUNT(*) FROM ventas_semanales")).scalar())

    q1 = conn.execute(text("SELECT SUM(cantidad) FROM ventas_crudas")).scalar()
    q2 = conn.execute(text("SELECT SUM(cantidad_total) FROM ventas_semanales")).scalar()
    print(f"Cantidades coherentes: {q1} vs {q2}")
```

La suma de cantidades en `ventas_crudas` debe igualar la de `ventas_semanales`.

---

## Decisiones tecnicas

### Por que NO outliers de cantidad/valor
En materiales de construccion, las cantidades grandes son ventas reales a obras grandes (bodegas de constructores, conjuntos residenciales). Eliminar outliers por IQR borra datos legitimos. Si hay sospecha de error, marcar la fila pero no borrarla.

### Por que `ventas_staging` con todo VARCHAR
Apache Hop tiene problemas con tipos numericos cuando el CSV usa comas como separador decimal o cuando hay valores faltantes. Cargar como string evita todos esos errores en Hop y deja la tipificacion a Python que la maneja mejor.

### Por que TRUNCATE + append y no DROP + recreate
TRUNCATE preserva el schema, los indices y las restricciones definidas en `01_schema.sql`. Es idempotente y rapido.

---

## Reglas no negociables

1. **Apache Hop solo toca `ventas_staging`.** Nunca otras tablas.
2. **Las columnas personales se descartan en la ingesta de Hop.** Nunca tocan MySQL.
3. **Toda carga termina con validacion `COUNT(*)`.**
4. **El ETL es idempotente.** TRUNCATE + append siempre.
5. **No eliminar outliers de cantidad/valor.** Son ventas reales.
6. **Documentar cualquier cambio de logica en `docs/03_preparacion_datos.md`.**
7. **El CSV crudo vive solo en `data/raw/` (gitignored).** NUNCA se commitea.
