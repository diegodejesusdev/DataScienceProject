---
name: mysql-operations
description: Cómo conectarse a MySQL desde Python, leer y escribir tablas, manejar el esquema, hacer queries seguras y validar cargas. Léeme antes de cualquier operación que toque la base de datos.
---

# Operaciones con MySQL en este proyecto

## Conexión

**SIEMPRE** usa el helper `src/db.py`:

```python
from src.db import get_engine
engine = get_engine()
```

**NUNCA** hardcodees credenciales. Todo viene de `.env`:

```python
# src/db.py — única fuente de verdad para la conexión
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from dotenv import load_dotenv

# Cargar .env desde la raíz del repo
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def get_engine() -> Engine:
    """Devuelve un Engine de SQLAlchemy conectado a la BD del proyecto.

    Detecta automáticamente si corre dentro del contenedor Jupyter
    (host=`mysql`) o en el host nativo (host=`localhost`).
    """
    host = os.getenv("MYSQL_HOST", "localhost")
    port = os.getenv("MYSQL_PORT", "3306")
    user = os.getenv("MYSQL_USER")
    password = os.getenv("MYSQL_PASSWORD")
    database = os.getenv("MYSQL_DATABASE")

    url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    return create_engine(url, pool_pre_ping=True, pool_recycle=3600)
```

### Por qué `pool_pre_ping` y `pool_recycle`
- `pool_pre_ping=True`: prueba la conexión antes de usarla, evita errores de "MySQL has gone away".
- `pool_recycle=3600`: recicla conexiones cada hora.

---

## Lectura

### Lectura completa
```python
import pandas as pd
from src.db import get_engine

engine = get_engine()
df = pd.read_sql("SELECT * FROM ventas_semanales", engine)
```

### Lectura con parámetros (SIEMPRE parametrizar, nunca f-strings)
```python
from sqlalchemy import text

query = text("""
    SELECT item, fecha_inicio_semana, cantidad_total
    FROM ventas_semanales
    WHERE fecha_inicio_semana >= :fecha_desde
      AND item IN :items
""")

df = pd.read_sql(
    query,
    engine,
    params={"fecha_desde": "2024-01-01", "items": tuple(items_lista)}
)
```

⚠️ **NUNCA** construyas SQL con f-strings o concatenación. Es vulnerable a SQL injection.

### Lectura por chunks (para tablas grandes)
```python
for chunk in pd.read_sql("SELECT * FROM ventas_crudas", engine, chunksize=50_000):
    procesar(chunk)
```

---

## Escritura

### `to_sql` con `if_exists`
```python
df.to_sql(
    name="ventas_semanales",
    con=engine,
    if_exists="append",         # "append", "replace", o "fail"
    index=False,
    chunksize=10_000,           # carga por lotes
    method="multi"              # inserts más eficientes
)
```

### Reglas sobre `if_exists`
- **`append`** — por defecto en cargas incrementales. Es lo más seguro.
- **`replace`** — borra y recrea la tabla (¡pierde índices y restricciones!). Solo en desarrollo.
- **`fail`** — falla si la tabla existe. Útil para asegurar que estás creando algo nuevo.

⚠️ **`replace` es peligroso:** pierdes índices, claves, restricciones definidas en `01_schema.sql`. Prefiere `TRUNCATE TABLE` + `append`.

### Patrón seguro para reemplazar contenido de una tabla
```python
with engine.begin() as conn:
    conn.execute(text("TRUNCATE TABLE ventas_semanales"))
df.to_sql("ventas_semanales", engine, if_exists="append", index=False)
```

### Tipos de columnas al cargar
`to_sql` infiere tipos de pandas. Para forzar tipos correctos en MySQL:

```python
from sqlalchemy.types import DATE, DECIMAL, VARCHAR, INTEGER

df.to_sql(
    "ventas_semanales",
    engine,
    if_exists="append",
    index=False,
    dtype={
        "fecha_inicio_semana": DATE(),
        "cantidad_total": DECIMAL(18, 4),
        "valor_bruto_total": DECIMAL(18, 4),
        "item": VARCHAR(50),
        "anio": INTEGER(),
    }
)
```

---

## Validación obligatoria después de cargas

**SIEMPRE** después de cargar datos, valida con un `COUNT`:

```python
from sqlalchemy import text

with engine.connect() as conn:
    n_filas = conn.execute(text("SELECT COUNT(*) FROM ventas_semanales")).scalar()
    n_skus = conn.execute(text("SELECT COUNT(DISTINCT item) FROM ventas_semanales")).scalar()
    fechas = conn.execute(text("SELECT MIN(fecha_inicio_semana), MAX(fecha_inicio_semana) FROM ventas_semanales")).first()

print(f"Filas cargadas: {n_filas:,}")
print(f"SKUs únicos: {n_skus:,}")
print(f"Rango de fechas: {fechas[0]} → {fechas[1]}")
```

Compara contra los totales esperados del CSV crudo. Si no coinciden, hay un problema.

---

## Schema de las tablas del proyecto

Definido en `db/init/01_schema.sql` (se ejecuta automáticamente al primer arranque de Docker).

### Tablas principales

| Tabla | Granularidad | Origen | Uso |
|---|---|---|---|
| `ventas_crudas` | 1 fila = 1 línea de remisión/venta | Apache Hop carga el CSV | Insumo crudo, no modelar directamente |
| `dim_producto` | 1 fila por SKU | Derivada de `ventas_crudas` | Dimensión de productos |
| `ventas_semanales` | 1 fila por (SKU × centro × año × semana) | Agregación desde `ventas_crudas` | **Tabla de modelado** |
| `clasificacion_abc_xyz` | 1 fila por SKU | Notebook `04_abc_xyz.ipynb` | Clasificación |
| `pronosticos` | 1 fila por (SKU × fecha futura × modelo) | Notebooks de modelado | Predicciones |
| `metricas_modelos` | 1 fila por evaluación | Notebook `09_evaluacion_final.ipynb` | Comparación |

---

## Adminer (GUI web)

Acceso: `http://localhost:8080`

Para entrar:
- Sistema: **MySQL**
- Servidor: **`mysql`** (¡así escrito, no `localhost`! es el nombre del servicio Docker)
- Usuario, contraseña, BD: del `.env`

Útil para:
- Verificar el schema visualmente.
- Hacer queries ad-hoc rápidas.
- Exportar resultados a CSV.

---

## Errores comunes

### `Can't connect to MySQL server on 'mysql' ([Errno -2] Name or service not known)`
Estás corriendo Python desde el host nativo, no desde el contenedor.
**Solución:** cambia `MYSQL_HOST=localhost` (no `mysql`) en `.env` cuando corras desde host.

### `pymysql.err.OperationalError: (2013, 'Lost connection to MySQL server during query')`
Carga muy grande sin chunks.
**Solución:** usa `chunksize=10_000` en `to_sql`.

### `Specified key was too long; max key length is 3072 bytes`
Índice sobre columnas `VARCHAR` largas con `utf8mb4`.
**Solución:** acorta el `VARCHAR` o usa prefijo de índice (`INDEX(col(50))`).

### `1366 Incorrect string value`
Problema de encoding.
**Solución:** asegúrate de que la BD esté en `utf8mb4` y de pasar `df = df.astype({"col": "string"})` antes de subir.

---

## Reglas no negociables

1. **NUNCA hardcodees credenciales.** Todo en `.env`.
2. **NUNCA construyas SQL con f-strings.** Parametriza siempre con `:nombre`.
3. **SIEMPRE valida con `COUNT(*)` después de cargar.**
4. **NUNCA uses `if_exists="replace"`** si la tabla tiene índices definidos en el schema.
5. **NUNCA conectes Tableau con el usuario `root`.** Usa `construnorte_user`.
6. **SIEMPRE cierra explícitamente** las conexiones cuando uses `with engine.connect()`.
