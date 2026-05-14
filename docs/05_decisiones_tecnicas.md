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
- **Hop hace SOLO:** lectura del CSV → filtrado de las 17 columnas útiles (descarta las personales) → carga a `ventas_staging` en MySQL. 3 pasos visuales: `Text File Input → Select Values → Table Output`.
- **Python hace todo lo demás:** desde `ventas_staging` → tipificación → limpieza → filtrado por tipo de documento → construcción de `ventas_crudas`, `dim_producto`, `ventas_semanales`.

Esta separación da lo mejor de ambos mundos: lo visual y demostrable para el evaluador, y la mantenibilidad de código Python para el equipo.
