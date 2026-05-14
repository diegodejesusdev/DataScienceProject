# Apache Hop — Flujo de ingesta

Esta carpeta contiene el único flujo de Apache Hop del proyecto: la ingesta del CSV crudo a la tabla `ventas_staging` en MySQL.

**Toda la lógica adicional (limpieza, tipificación, agregación, feature engineering, modelado) está en Python (`src/`).** Apache Hop se usa exclusivamente para esta ingesta inicial visual, cumpliendo el requisito académico del programa.

---

## Requisitos previos

1. **Apache Hop** instalado en el Mac (versión 2.7+ recomendada).
   - Descarga: https://hop.apache.org/download/
2. **Driver JDBC de MySQL** colocado en `~/.hop/lib/`:
   - Descargar `mysql-connector-j-*.jar` desde https://dev.mysql.com/downloads/connector/j/
   - Copiarlo en `~/.hop/lib/` (crear la carpeta si no existe).
   - Reiniciar Hop después de copiarlo.
3. **Docker corriendo** con MySQL accesible en `localhost:3306`.

---

## Cómo construir el flujo

Abre Apache Hop, crea un nuevo Pipeline (`File → New → Pipeline`) y guárdalo como `hop/ingesta_csv.hpl` dentro del repo.

### Step 1 — `Text File Input`

Arrástralo desde el panel izquierdo (categoría "Input").

**Tab "File":**
- Filename / Folder: ruta al CSV. Recomendado usar variable de proyecto: `${PROJECT_HOME}/data/raw/ventas_construnorte.csv`

**Tab "Content":**
- Filetype: `CSV`
- Separator: `;`
- Enclosure: `"`
- Header: ✅ (1 línea)
- Format: `Unix`
- Encoding: `UTF-8`
- Compression: `None`

**Tab "Fields":**
Click en "Get fields" para que Hop infiera las columnas, luego deja **solo estas 17** (elimina las demás filas con clic derecho → "Remove selected lines"):

| Name | Type |
|---|---|
| Fecha | String |
| Item | String |
| Nombre Item | String |
| Referencia Item | String |
| Codigo Barra Item | String |
| Unidad Inventario 1 Item | String |
| Proveedor Codigo Item | String |
| Proveedor Nombre Item | String |
| Nombre Linea N1 | String |
| Nombre Linea N2 | String |
| Centro de Operacion | String |
| Tipo de Documento | String |
| Cantidad 1 | String |
| Precio Uni | String |
| Valor Bruto | String |
| Valor Costo | String |
| Peso | String |

> ⚠️ **Todos como String** a propósito. Hop tiene problemas con coma decimal en números y con fechas en formato `YYYYMMDD`. Python se encarga del casteo.

### Step 2 — `Select Values`

Arrástralo desde "Transform". Conéctalo después del Text File Input.

**Tab "Select & Alter":**
Renombra las columnas a snake_case:

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

### Step 3 — `Table Output`

Arrástralo desde "Output". Conéctalo después del Select Values.

**Configuración:**
- Connection: crear nueva (ver abajo "Conexión a MySQL")
- Target table: `ventas_staging`
- Commit size: `1000`
- Truncate table: ✅
- Use batch update for inserts: ✅
- Specify database fields: ✅

**Tab "Database fields":**
Click "Get fields" o "Enter field mapping" para mapear los 17 campos del stream con los 17 campos de la tabla. Los nombres deben coincidir (ya están en snake_case gracias al Select Values).

---

## Conexión a MySQL

En el panel izquierdo, Database connections → New connection:

| Campo | Valor |
|---|---|
| Connection name | `construnorte_mysql` |
| Connection type | `MySQL` |
| Host name | `localhost` |
| Database name | `construnorte` (o el valor de tu `.env`) |
| Port | `3306` |
| Username | el de tu `.env` |
| Password | el de tu `.env` |

Click "Test" para verificar.

> 💡 **Tip:** Hop corre **nativo en el Mac**, no dentro de Docker. Por eso usa `localhost`, no `mysql`.

---

## Ejecutar el flujo

1. Guarda el pipeline (Cmd+S).
2. En la barra superior, click ▶️ "Run pipeline".
3. En el diálogo, selecciona "Local pipeline engine" y "Launch".
4. Observa la pestaña "Execution Results" abajo:
   - "ventas_staging" debe recibir ~600.000 filas leídas y escritas.
   - El step "Text File Input" muestra el número de líneas leídas.
   - "Table Output" muestra el número insertado.

### Tiempo esperado
Con 600K filas: entre 30 segundos y 2 minutos según el rendimiento del Mac.

---

## Validación post-Hop

Desde Adminer (`http://localhost:8080`) o cualquier cliente MySQL:

```sql
SELECT COUNT(*) FROM ventas_staging;
-- debe estar cerca de las ~600.000 esperadas

SELECT * FROM ventas_staging LIMIT 10;
-- las filas deben mostrar las 17 columnas en snake_case
```

O desde Python:

```python
from src.db import get_engine
from sqlalchemy import text

engine = get_engine()
with engine.connect() as conn:
    n = conn.execute(text("SELECT COUNT(*) FROM ventas_staging")).scalar()
    print(f"Filas en staging: {n:,}")
```

---

## Continuar con el ETL en Python

Una vez `ventas_staging` esté poblada, ejecuta el resto del ETL en Python:

```bash
# Desde el contenedor Jupyter (o desde el host con el venv activo)
python -m src.etl --modo staging
```

Eso construye:
- `ventas_crudas` (datos tipificados y limpios)
- `dim_producto` (dimensión de productos)
- `ventas_semanales` (granularidad modelable)

---

## Estructura final esperada

```
hop/
├── README.md                # Este archivo
├── ingesta_csv.hpl          # El pipeline visual de Hop
└── .hop/                    # (gitignored) metadatos locales de Hop
```

El archivo `ingesta_csv.hpl` es un XML legible que sí se commitea. Permite que otros reproduzcan el flujo abriéndolo en su instalación de Hop.

---

## Capturas para el informe

Para el informe ejecutivo, capturar:

1. **El pipeline completo** (los 3 steps conectados visualmente).
2. **El "Execution Results"** mostrando los conteos.
3. **La preview de datos** después del Select Values (10 filas, 17 columnas en snake_case).

Estas capturas justifican el uso de Apache Hop en el proyecto y enseñan el flujo visual al evaluador.
