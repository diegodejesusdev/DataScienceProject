# 05 — Decisiones técnicas

Registro de las decisiones de arquitectura y stack del proyecto. Sirve para la sustentación.

---

## Base de datos: MySQL 8.0

**Por qué MySQL y no PostgreSQL o SQLite:**
- Requisito explícito del programa formativo.
- Conector nativo de Tableau Desktop con un driver oficial maduro.
- Soporte directo en Apache Hop para carga masiva con `MySQL Bulk Loader`.
- Adminer como GUI ligera para verificación visual.

---

## Contenedorización con Docker

**Por qué Docker:**
- Requisito explícito del programa.
- Ambiente reproducible: cualquier evaluador levanta el stack con `docker compose up`.
- Aísla el motor de base de datos del sistema operativo del Mac.
- Permite versionar la infraestructura junto al código.

**Qué va y qué no va en Docker:**
- ✅ MySQL, Adminer, Jupyter Lab → contenedores.
- ❌ Apache Hop → nativo (la GUI no se contenedoriza con sentido).
- ❌ Tableau Desktop → nativo (no tiene versión Linux).

---

## Granularidad de modelado: semanal por SKU × centro

**Por qué no diaria:**
- ~600.000 filas crudas; a granularidad diaria por SKU el dataset queda esparso (muchos ceros) y los lags pierden significado.
- La decisión de aprovisionamiento real se toma semanalmente, no diariamente.
- Reduce la varianza estructural sin perder señal estacional.

**Por qué incluir centro de operación:**
- Distintos centros tienen patrones de demanda diferentes para el mismo SKU.
- Permite predicciones diferenciadas para decisiones logísticas locales.

---

## Modelos: LightGBM como principal

**Por qué LightGBM:**
- Eficiente con datos tabulares con features de calendario y rezagos.
- Soporta features categóricas nativas (item, línea de producto, proveedor).
- Mucho más rápido de entrenar que Random Forest sobre 200k–300k filas.
- Robusto a outliers y a valores faltantes en lags iniciales.

**Por qué XGBoost como comparación:**
- Sirve como punto de comparación reconocido en la literatura.
- Misma estrategia (global con SKU como feature), buena segunda referencia.

**Por qué Prophet solo en top 50:**
- Modelo univariante: uno por SKU. No escala a miles.
- Útil para los SKUs A donde queremos descomponer estacionalidad y tendencia.

**Por qué NO Random Forest, redes neuronales, Spark:**
- Random Forest es más pesado para series temporales con muchos lags.
- Redes neuronales no agregan valor con 100 semanas de historia.
- Spark es sobreingeniería para ~600k filas (caben en RAM).

---

## Partición temporal (NO aleatoria)

**Por qué partición temporal:**
- Es serie de tiempo: el `train_test_split` aleatorio filtra futuro al modelo y produce métricas optimistas falsas.

**Cortes:**
- Train: enero 2024 – 30 sep 2025.
- Valid: octubre 2025.
- Test: noviembre–diciembre 2025.

---

## Tableau Desktop para el dashboard

**Por qué Tableau:**
- Licencia académica gratuita.
- Conector MySQL maduro.
- Permite presentar el resultado a la organización beneficiaria de forma profesional.

**Plan B:** Looker Studio (gratuito, requiere exportar a CSV o conectar vía intermediarios).

---

## Apache Hop solo para la ingesta inicial

**Por qué Apache Hop:**
- Requisito académico del programa: el diplomado exige el uso de una herramienta ETL visual.
- Se ve bien en el informe ejecutivo: muestra un flujo gráfico fácil de leer.
- Es la herramienta de ETL visual recomendada por el programa.

**Por qué solo UN flujo simple en Hop:**
- Toda la lógica de tipificación, limpieza, filtrado y agregación requiere condicionales, manejo de fechas en formato `YYYYMMDD` y normalización de decimales con coma. Eso es mucho más natural y mantenible en Python.
- Implementar lógica condicional compleja en Hop alarga el ciclo de desarrollo, dificulta el debugging y no aporta valor frente a Python.
- Hop con un solo flujo cumple el requisito de uso de herramienta ETL sin sacrificar productividad.

**División concreta:**
- **Hop hace SOLO:** lectura del CSV → filtrado de las 15 columnas útiles (descarta las personales, peso, código de barras y demás) → carga a `ventas_staging` en MySQL. 3 pasos visuales: `Text File Input → Select Values → Table Output`.
- **Python hace todo lo demás:** desde `ventas_staging` → tipificación → filtrado por tipo de documento → filtrado por periodo → construcción de `ventas_crudas`, `dim_producto`, `ventas_semanales`.

Esta separación da lo mejor de ambos mundos: lo visual y demostrable para el evaluador, y la mantenibilidad de código Python para el equipo.

---

## Decisiones sobre el dataset

### Columnas descartadas

- **Datos personales** (`Cliente`, `Nombre_Cliente`, `Direccion_Cliente`, `Nit_Cliente`, `Ciudad_Cliente`, `Ciudad_Descripcion_Cliente`, `Nombre_Criterio_Cliente_1`, `Vendedor`, `Nombre_Vendedor`, `Cedula_Vendedor`): se descartan en cumplimiento de la Ley 1581 de 2012 (Habeas Data) de Colombia.
- **Documentos internos** (`Documento_Remision`, `Documento_Ventas`, `Documento_Pedido`): identificadores de transacciones que no aportan al modelo predictivo ni al dashboard.
- **Variables de control** (`Lapso`, `Cargue`, `Centro_de_Operacion_RM`, `Fecha_Remision`, `Fecha_Pedido`): metadatos operativos sin valor analítico.
- **`Codigo_Barra_Item`**: en la muestra inicial del CSV viene vacía en la gran mayoría de registros. No es feature ni dimensión de análisis.
- **`Peso`**: el equipo identificó que la información de esta columna no es verídica (probablemente por errores en la captura del peso en el ERP). Incluirla podría confundir interpretaciones futuras.
- **`Tipo_de_Documento`**: se mantiene en `ventas_staging` para que Python pueda filtrar las ventas efectivas, pero se descarta antes de cargar `ventas_crudas` porque no es feature predictiva.

### Filtros aplicados en Python

**Por tipo de documento** (variable `TIPOS_DOC_VENTA = ["1E", "2E", "3E"]` en `src/etl.py`):

Después de revisar con ConstruNorte la semántica de cada tipo:

| Tipo | Significado | Decisión |
|---|---|---|
| `1E`, `2E`, `3E` | Ventas con facturación electrónica (una por bodega) | **Retener** |
| `J1`, `B1`, `L1` | Ventas previas a facturación electrónica — solo existen hasta noviembre 2022 | No aplica (fuera del periodo 2024-2025) |
| `CM` | Conversión de mercancía (~89 registros) | Descartar |
| `CT` | Cotizaciones (intención de compra, no venta efectiva) | Descartar |
| `EN` | Devoluciones | Descartar (modelamos solo ventas brutas) |

Como el periodo de análisis es 2024-2025 estricto y `J1/B1/L1` solo aparecen hasta noviembre de 2022, en la práctica solo retenemos `1E`, `2E` y `3E`.

**Por periodo de análisis** (`FECHA_MIN = 2024-01-01`, `FECHA_MAX = 2026-03-31`):

La auditoría inicial del dataset evidenció tres bloques temporales con calidad distinta:

| Bloque | Filas | Decisión |
|---|---|---|
| **2022** | 22.611 | Descartado |
| **2024–2025** | 543.808 | Periodo principal de modelado |
| **2026-Q1** (enero–marzo) | 75.213 | Test extendido (datos del "futuro real") |
| **2026-04** (parcial) | 18.950 | Descartado |

**Justificaciones:**

- **2022 descartado:** los registros son aislados (no hay continuidad con 2023, que falta totalmente) y reflejan un contexto operativo distinto. Los tipos de documento `J1/B1/L1` propios de ese año (anteriores a la facturación electrónica) confirman que las dinámicas de captura de datos cambiaron. Mezclarlos con 2024-2025 introduciría sesgo en los lags y en las estadísticas por SKU.

- **2024-2025 como periodo principal de modelado:** corresponde al alcance acordado en el anteproyecto. Son 24 meses continuos y completos.

- **2026-Q1 como test extendido (decisión metodológica clave):** los tres primeros meses de 2026 están completos y representan datos posteriores al periodo de modelado, por lo que constituyen una prueba "out of sample real" — el modelo no los vio durante el entrenamiento. Esto fortalece la evaluación metodológica del proyecto sin alterar el periodo de entrenamiento acordado.

- **2026-04 descartado:** la consulta `SELECT MAX(fecha) FROM ventas_staging WHERE SUBSTRING(fecha, 1, 4) = '2026'` devolvió 20260424. Abril 2026 está incompleto (solo hasta el día 24), por lo que se excluye para no sesgar la prueba.

**Partición temporal resultante:**

| Conjunto | Periodo | Uso |
|---|---|---|
| Train | 2024-01-01 → 2025-09-30 | Entrenamiento |
| Validation | 2025-10-01 → 2025-12-31 | Ajuste de hiperparámetros |
| Test 2026 | 2026-01-01 → 2026-03-31 | Evaluación final out-of-sample |

Esta estrategia respeta el alcance del anteproyecto (modelar 2024-2025) y al mismo tiempo aprovecha los datos de 2026-Q1 como prueba adicional de generalización temporal.