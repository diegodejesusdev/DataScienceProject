# Apache Hop — Flujo de ingesta

Esta carpeta contiene el único flujo de Apache Hop del proyecto: la ingesta del CSV crudo a la tabla `ventas_staging` en MySQL.

**Toda la lógica adicional (filtrado por tipo de documento, filtrado por periodo, tipificación, agregación, feature engineering, modelado) está en Python (`src/`).** Apache Hop se usa exclusivamente para esta ingesta inicial visual, cumpliendo el requisito académico del programa.

---

## Requisitos previos

1. **Apache Hop** instalado en el Mac (versión 2.7+).
   - Descarga: https://hop.apache.org/download/
2. **Driver JDBC de MySQL** en `~/.hop/lib/`:
   - Descargar `mysql-connector-j-*.jar` desde https://dev.mysql.com/downloads/connector/j/
   - Copiarlo a `~/.hop/lib/` (crear la carpeta si no existe).
   - Reiniciar Hop después de copiarlo.
3. **Docker corriendo** con MySQL accesible en `localhost:3306`.

---

## El pipeline en 3 steps

```
[Text File Input]  →  [Select Values]  →  [Table Output]
   lee CSV completo   filtra 15 cols     carga a ventas_staging
   (35 cols, todas    renombra a         (Truncate + load)
    como String)      snake_case
```

### Step 1 — `Text File Input`

**Tab "File":**
- Filename / Folder: `${PROJECT_HOME}/data/raw/ventas_construnorte.csv` (o ruta absoluta).

**Tab "Content":**
- Filetype: `CSV`
- Separator: `;`
- Enclosure: `"`
- Header: ✅ (1 línea)
- Encoding: `UTF-8`

**Tab "Fields":**
1. Click **"Get Fields"** → muestreo de **1000 líneas**.
2. Hop detecta automáticamente **las 35 columnas** del CSV.
3. Selecciona todas las filas (Cmd+A) y configura:
   - **Type:** `String` para todas
   - **Format, Length, Precision, Currency, Decimal, Group:** todos vacíos
   - **Trim type:** `none`
   - **Repeat:** `N`

> ⚠️ Las 35 columnas se cargan como String a propósito. Hop tiene problemas con coma decimal en números y con fechas `YYYYMMDD`. Python se encarga del casteo después.

### Step 2 — `Select Values`

Conéctalo después del Text File Input.

**Tab "Select & Alter":** agrega SOLO estas **15 columnas** y renómbralas:

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

**⚠️ CRÍTICO:** desplázate hasta el final del diálogo y **DESMARCA** la opción **"Include unspecified fields, ordered by name"**.

Eso garantiza que las **20 columnas no listadas** (personales, documentos internos, peso, codigo_barra, lapso, etc.) **se descarten automáticamente** y nunca lleguen a MySQL.

### Step 3 — `Table Output`

Conéctalo después del Select Values.

| Campo | Valor |
|---|---|
| Connection | `construnorte_mysql` |
| Target table | `ventas_staging` |
| Commit size | `1000` |
| Truncate table | ✅ |
| Use batch update for inserts | ✅ |
| Specify database fields | ✅ |

**Tab "Database fields":** click "Get fields" para mapear automáticamente los 15 campos del stream con los 15 campos de `ventas_staging`. Los nombres coinciden gracias al renombre del Select Values.

---

## Conexión a MySQL en Hop

Panel izquierdo → Database connections → New connection:

| Campo | Valor |
|---|---|
| Connection name | `construnorte_mysql` |
| Connection type | `MySQL` |
| Host name | `localhost` |
| Database name | `construnorte` (o el del `.env`) |
| Port | `3306` |
| Username | el del `.env` |
| Password | el del `.env` |

Click "Test" para verificar.

> 💡 Hop corre **nativo en el Mac**, por eso usa `localhost`, no `mysql`.

---

## Ejecución y validación

1. Guardar el pipeline como `hop/ingesta_csv.hpl`.
2. Click ▶️ "Run pipeline" → "Local pipeline engine".
3. Observar la pestaña "Execution Results":
   - `Text File Input` debería leer ~600K líneas.
   - `Select Values` debería pasar las mismas filas con 15 columnas.
   - `Table Output` debería insertar las mismas filas en `ventas_staging`.

### Verificar desde Adminer o Python

```sql
-- En Adminer (http://localhost:8080)
SELECT COUNT(*) FROM ventas_staging;
SELECT tipo_documento, COUNT(*) FROM ventas_staging GROUP BY tipo_documento;
```

Los conteos por tipo deberían incluir `1E`, `2E`, `3E`, `J1`, `B1`, `L1`, `CM`, `CT`, `EN` y posiblemente otros. Es normal — Python decide cuáles retener.

---

## Continuar con el ETL en Python

Una vez `ventas_staging` esté poblada, ejecutar Python:

```bash
docker exec -it construnorte_jupyter python -m src.etl
```

Eso aplica:
- Tipificación (fecha YYYYMMDD, números con coma decimal).
- Filtrado por tipo de documento (retiene `1E, 2E, 3E, J1, B1, L1`).
- Filtrado por periodo (`2024-01-01` a `2025-12-31`).
- Eliminación de duplicados.
- Construcción de `ventas_crudas`, `dim_producto`, `ventas_semanales`.

---

## Capturas para el informe

Para el informe ejecutivo, capturar:
1. **El pipeline completo** (los 3 steps conectados visualmente).
2. **El "Execution Results"** con los conteos de cada step.
3. **La preview de datos** después del Select Values (10 filas, 15 columnas en snake_case).

Estas capturas justifican el uso de Apache Hop y enseñan el flujo visual al evaluador.
