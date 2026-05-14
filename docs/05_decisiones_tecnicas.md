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

## Apache Hop para ETL visual

**Por qué Apache Hop y no solo Python:**
- Visual: facilita explicar el pipeline en el informe y a la organización.
- Permite reutilizar el flujo si se actualizan datos futuros.
- Es la herramienta de ETL visual recomendada por el programa.

**División de responsabilidades:**
- Hop: lectura del CSV, filtrado de columnas, carga a `ventas_crudas`.
- Python: limpieza fina, agregaciones, feature engineering, modelado.
