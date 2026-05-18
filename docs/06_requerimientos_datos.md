# 06 — Requerimientos de datos

> Aplicación de la metodología de requerimientos del programa (épica → funcionalidad → historia de usuario → requerimiento de datos) al proyecto ConstruNorte.
>
> Este documento es la versión markdown del Anexo A. La versión Word formal vive en `reports/Anexo_A_Requerimientos.docx`.

---

## 1. Introducción

### 1.1 Contexto del problema descriptivo

ConstruNorte Comercializadora S.A.S. carece de una caracterización sistemática del comportamiento de rotación de los productos que comercializa. Aunque el sistema transaccional registra las ventas, no existe un análisis que clasifique los productos según su contribución al valor de las ventas ni según la estabilidad de su demanda. Esta carencia limita la capacidad de orientar la organización física de la bodega y de identificar productos críticos.

Este problema se aborda mediante un **análisis descriptivo**, porque inicialmente se busca conocer el estado actual: cuántos productos concentran la mayor parte del valor, qué tan estable es su demanda, qué productos son críticos por su movimiento y cuáles tienen baja rotación.

### 1.2 Contexto del problema predictivo

ConstruNorte necesita anticipar la demanda futura por producto para apoyar las decisiones de aprovisionamiento. Actualmente las compras se realizan principalmente con base en la experiencia del personal y en revisiones manuales del inventario, lo cual genera quiebres de stock en productos críticos y sobreinventario en productos de baja rotación.

Este problema se aborda mediante un **enfoque predictivo** basado en machine learning, que permita estimar la cantidad esperada de unidades a vender de cada producto a nivel semanal, segmentado por bodega.

---

## 2. Tema 1: Análisis descriptivo de rotación

### 2.1 Épica o tema de negocio

> **Como** Gerente de Operaciones de ConstruNorte Comercializadora S.A.S.,
> **quiero** conocer los patrones de rotación de los productos comercializados durante 2024-2025,
> **para** disponer de información clasificada y visualizada que oriente las decisiones sobre organización de bodega.

### 2.2 Tipo de análisis

**Tabla 1.** Caracterización del enfoque descriptivo.

| Elemento | Descripción |
|---|---|
| Tipo de proyecto | Análisis de datos |
| Enfoque | Descriptivo |
| Pregunta que responde | ¿Cuál es el patrón actual de rotación de los productos? |
| Propósito | Caracterizar los productos según valor de ventas y estabilidad de demanda |
| Producto esperado | Clasificación ABC/XYZ + dashboard de rotación + ranking de SKUs |

### 2.3 Pregunta analítica

**Pregunta principal:**

> ¿Cuál es el patrón de rotación de los productos comercializados por ConstruNorte durante el período 2024-2025, según su contribución al valor de ventas y la estabilidad de su demanda, que permita orientar las decisiones de organización de la bodega?

**Preguntas secundarias:**

**Tabla 2.** Preguntas secundarias del análisis descriptivo.

| Pregunta | Propósito |
|---|---|
| ¿Qué productos concentran la mayor parte del valor de ventas (clase A)? | Identificar los SKUs críticos para el negocio |
| ¿Qué productos tienen demanda estable (clase X) versus errática (clase Z)? | Caracterizar la variabilidad de la demanda |
| ¿Cómo se distribuyen los SKUs en la matriz ABC × XYZ? | Caracterizar el portafolio en sus 9 segmentos |
| ¿Qué líneas de producto (N1 y N2) concentran mayor valor? | Orientar decisiones de organización por categoría |
| ¿Existen diferencias de rotación entre los tres centros de operación? | Identificar patrones específicos por bodega |
| ¿Qué SKUs tienen baja rotación y podrían considerarse candidatos a revisión? | Identificar productos con poco movimiento |

### 2.4 Funcionalidad analítica

**Tabla 3.** Funcionalidad analítica descriptiva.

| Campo | Descripción |
|---|---|
| Nombre de la funcionalidad | Caracterización de la rotación de productos comercializados por ConstruNorte |
| Descripción | Permite caracterizar el comportamiento de rotación de los SKUs a partir de su contribución al valor de ventas y la estabilidad de su demanda, durante el período 2024-2025, generando una clasificación ABC/XYZ y visualizaciones que orienten la organización de la bodega. |
| Preguntas de negocio | ¿Qué productos concentran el valor? ¿Qué productos tienen demanda estable o errática? ¿Qué SKUs requieren mayor atención por su rotación? |
| Tipo de solución | Análisis descriptivo + visualización |
| Variables o dimensiones involucradas | Item (SKU), centro de operación, línea de producto N1 y N2, proveedor, fecha, cantidad, valor bruto |
| Métricas o indicadores | Valor total por SKU, porcentaje acumulado del valor, coeficiente de variación, clase ABC, clase XYZ, segmento ABC/XYZ |
| Nivel de análisis o granularidad | SKU, centro de operación, línea de producto |
| Fuente de datos | Tabla `ventas_semanales` (derivada del CSV transaccional 2024-2025) |
| Transformaciones requeridas | Agregación por SKU, cálculo de porcentajes acumulados, cálculo del coeficiente de variación, asignación de clases ABC y XYZ |
| Salida esperada | Tabla `clasificacion_abc_xyz` en MySQL, dashboard en Tableau, gráficos en notebook |
| Frecuencia de actualización | Única vez para el alcance del proyecto académico |

### 2.5 Historias de usuario

#### Historia de usuario 1

**Tabla 4.** HU-01: Distribución general de SKUs según clasificación ABC.

| Campo | Descripción |
|---|---|
| ID | HU-01 |
| Nombre | Distribución general de SKUs según clasificación ABC |
| Rol | Gerente de Operaciones |
| Descripción | Como Gerente de Operaciones, quiero visualizar cómo se distribuyen los productos comercializados según su contribución al valor total de ventas, para identificar qué porcentaje de SKUs concentra la mayor parte del valor del negocio. |
| Variables o dimensiones | Item (SKU), valor bruto, clase ABC |
| Métricas | Número de SKUs por clase, porcentaje del valor acumulado, valor total por clase |
| Filtro o contexto | Período 2024-2025 |
| Fuente de datos | Tablas `ventas_semanales` y `clasificacion_abc_xyz` |
| Salida esperada | Gráfico de Pareto, tabla resumen por clase ABC |

#### Historia de usuario 2

**Tabla 5.** HU-02: Identificación de productos con baja rotación o demanda errática.

| Campo | Descripción |
|---|---|
| ID | HU-02 |
| Nombre | Identificación de productos con baja rotación o demanda errática |
| Rol | Gerente de Operaciones |
| Descripción | Como Gerente de Operaciones, quiero identificar los productos clasificados como clase C (bajo valor) y clase Z (demanda errática), para disponer de un listado que oriente la revisión de productos con poco movimiento o comportamiento irregular. |
| Variables o dimensiones | Item, clase ABC, clase XYZ, segmento ABC/XYZ, línea de producto |
| Métricas | Número de SKUs por segmento, coeficiente de variación, valor total por SKU |
| Filtro o contexto | Segmentos CZ, CY, BZ |
| Fuente de datos | Tabla `clasificacion_abc_xyz` |
| Salida esperada | Listado de SKUs ordenados por segmento, exportable a Excel |

#### Historia de usuario 3

**Tabla 6.** HU-03: Consulta del dashboard de rotación por línea y centro.

| Campo | Descripción |
|---|---|
| ID | HU-03 |
| Nombre | Consulta del dashboard de rotación por línea de producto y centro de operación |
| Rol | Analista de Datos |
| Descripción | Como Analista de Datos del equipo del proyecto, quiero consultar un dashboard interactivo con los principales indicadores de rotación, segmentables por línea de producto y centro de operación, para validar los resultados de la clasificación y comunicarlos a la organización beneficiaria. |
| Variables o dimensiones | Item, línea N1, línea N2, centro de operación, clase ABC, clase XYZ |
| Métricas | Número de SKUs, valor total, distribución por segmento, top 20 SKUs |
| Filtro o contexto | Filtros interactivos por línea, centro, segmento |
| Fuente de datos | Conexión Tableau a MySQL (tablas `clasificacion_abc_xyz`, `dim_producto`, `ventas_semanales`) |
| Salida esperada | Dashboard interactivo en Tableau Desktop |

### 2.6 Requerimientos de datos

#### Requerimiento 1

**Tabla 7.** RD-01: Construcción de la clasificación ABC.

| Campo | Descripción |
|---|---|
| ID | RD-01 |
| Nombre del requerimiento | Construcción de la clasificación ABC de los SKUs |
| Descripción | Se requiere clasificar los productos comercializados según su contribución acumulada al valor total de ventas (regla 80/95/100), generando las clases A, B y C. |
| Historia de usuario asociada | HU-01 |
| Tipo de requerimiento | Analítico / descriptivo |
| Variables o dimensiones involucradas | Item, valor bruto |
| Métricas requeridas | Valor total por SKU, porcentaje acumulado del valor, clase ABC |
| Nivel de granularidad | SKU |
| Filtros o criterios | Período 2024-2025, solo registros de venta efectiva |
| Fuente de datos | Tabla `ventas_semanales` |
| Transformaciones requeridas | Agregación por SKU, ordenamiento descendente, cálculo de porcentaje acumulado, asignación de clase según cortes 80% / 95% |
| Técnica o método sugerido | Análisis de Pareto |
| Salida esperada | Columnas `clase_abc`, `valor_total_periodo` y `porcentaje_acumulado` en la tabla `clasificacion_abc_xyz` |
| Criterios de aceptación | Cada SKU con registros de venta válidos debe quedar clasificado como A, B o C; la suma del porcentaje acumulado debe llegar al 100%. |

#### Requerimiento 2

**Tabla 8.** RD-02: Construcción de la clasificación XYZ.

| Campo | Descripción |
|---|---|
| ID | RD-02 |
| Nombre del requerimiento | Construcción de la clasificación XYZ de los SKUs |
| Descripción | Se requiere clasificar los productos según la estabilidad de su demanda, mediante el cálculo del coeficiente de variación sobre la serie semanal de unidades vendidas. |
| Historia de usuario asociada | HU-02 |
| Tipo de requerimiento | Analítico / descriptivo |
| Variables o dimensiones involucradas | Item, cantidad, fecha de inicio de semana |
| Métricas requeridas | Promedio semanal, desviación estándar semanal, coeficiente de variación, clase XYZ |
| Nivel de granularidad | SKU |
| Filtros o criterios | Período 2024-2025, mínimo 8 semanas de historia; SKUs con menor historia se marcan como Z |
| Fuente de datos | Tabla `ventas_semanales` (serie expandida con ceros para semanas sin venta) |
| Transformaciones requeridas | Expansión de la serie a todas las semanas, cálculo del CV, asignación de clase según cortes 0.5 / 1.0 |
| Técnica o método sugerido | Estadística descriptiva (coeficiente de variación) |
| Salida esperada | Columnas `coef_variacion` y `clase_xyz` en la tabla `clasificacion_abc_xyz` |
| Criterios de aceptación | Cada SKU debe quedar clasificado como X, Y o Z; el cálculo del CV debe basarse en la serie semanal completa (incluyendo semanas sin venta). |

#### Requerimiento 3

**Tabla 9.** RD-03: Matriz combinada ABC/XYZ y dashboard descriptivo.

| Campo | Descripción |
|---|---|
| ID | RD-03 |
| Nombre del requerimiento | Generación de matriz combinada ABC/XYZ y dashboard descriptivo |
| Descripción | Se requiere construir la matriz combinada ABC × XYZ (9 segmentos), generar los indicadores de rotación correspondientes y publicarlos en un dashboard interactivo. |
| Historia de usuario asociada | HU-03 |
| Tipo de requerimiento | Visualización / producto analítico |
| Variables o dimensiones involucradas | Item, clase ABC, clase XYZ, segmento ABC/XYZ, línea N1, línea N2, centro de operación |
| Métricas requeridas | Número de SKUs por segmento, valor total por segmento, porcentaje del valor por segmento |
| Nivel de granularidad | SKU, segmento, línea de producto |
| Filtros o criterios | Filtros interactivos por línea, centro de operación y segmento |
| Fuente de datos | Tablas `clasificacion_abc_xyz`, `dim_producto` y `ventas_semanales` en MySQL |
| Transformaciones requeridas | Cruce de ABC y XYZ, concatenación de segmento, unión con `dim_producto` para incluir líneas |
| Técnica o método sugerido | Tablas dinámicas, heatmap, dashboard interactivo |
| Salida esperada | Columna `segmento_abc_xyz` en la tabla `clasificacion_abc_xyz` y dashboard en Tableau Desktop |
| Criterios de aceptación | Los 9 segmentos deben estar representados; el dashboard debe permitir filtrar por línea de producto y centro de operación. |

### 2.7 Indicadores propuestos

**Tabla 10.** Indicadores propuestos para el análisis descriptivo.

| Indicador | Fórmula o descripción | Uso |
|---|---|---|
| Número total de SKUs | Conteo de SKUs distintos con venta en el período | Caracterizar el portafolio |
| Porcentaje de SKUs clase A | (SKUs clase A / total SKUs) × 100 | Medir concentración del valor |
| Porcentaje del valor en clase A | (Valor clase A / valor total) × 100 | Confirmar regla de Pareto |
| Coeficiente de variación promedio | Promedio del CV de todos los SKUs | Medir variabilidad general |
| Número de SKUs en segmento CZ | Conteo de SKUs con clase C y clase Z | Identificar candidatos a revisión |
| Valor total comercializado | Suma de `valor_bruto_total` en el período | Caracterizar volumen económico |
| Top 20 SKUs por valor | Listado ordenado descendente | Identificar productos críticos |

### 2.8 Salidas esperadas

**Tabla 11.** Salidas esperadas del análisis descriptivo.

| Salida | Descripción |
|---|---|
| Tabla `clasificacion_abc_xyz` | Tabla en MySQL con un registro por SKU y sus clases ABC, XYZ y segmento combinado |
| Curva de Pareto | Gráfico que muestra la concentración del valor en los SKUs clase A |
| Heatmap de la matriz ABC/XYZ | Visualización de los 9 segmentos con número de SKUs y valor por celda |
| Dashboard de rotación | Tableau Desktop conectado a MySQL, con filtros interactivos |
| Listado de SKUs en segmento CZ | Exportable a Excel para revisión por la organización beneficiaria |

---

## 3. Tema 2: Análisis predictivo de demanda

### 3.1 Épica o tema de negocio predictivo

> **Como** Gerente de Operaciones de ConstruNorte Comercializadora S.A.S.,
> **quiero** anticipar la demanda futura semanal de los productos comercializados,
> **para** disponer de un insumo analítico de pronósticos que oriente las decisiones de aprovisionamiento.

**Tabla 12.** Caracterización del enfoque predictivo.

| Elemento | Descripción |
|---|---|
| Tipo de proyecto | Ciencia de datos |
| Enfoque | Predictivo (forecasting / regresión sobre series temporales) |
| Pregunta que responde | ¿Qué cantidad de cada producto se estima vender en las próximas semanas? |
| Propósito | Anticipar la demanda para orientar decisiones de aprovisionamiento |
| Producto esperado | Modelo entrenado, pronósticos semanales, comparación de modelos, tabla de métricas |

### 3.2 Pregunta predictiva

**Pregunta principal:**

> ¿Cómo puede un modelo de machine learning, entrenado con los datos transaccionales de ConstruNorte del período 2024-2025, pronosticar la demanda futura por producto a nivel semanal con la precisión suficiente para apoyar decisiones de aprovisionamiento?

**Preguntas secundarias:**

**Tabla 13.** Preguntas secundarias del análisis predictivo.

| Pregunta | Propósito |
|---|---|
| ¿Qué variables predictoras explican mejor la demanda semanal? | Identificar features relevantes (lags, calendario, ABC/XYZ) |
| ¿Qué tan preciso es el modelo predictivo comparado con un baseline ingenuo? | Validar el valor agregado del modelo |
| ¿Cómo varía el desempeño del modelo entre segmentos ABC/XYZ? | Identificar para qué tipos de SKU el modelo es más útil |
| ¿Qué modelo entre LightGBM, XGBoost y Prophet ofrece el mejor desempeño? | Seleccionar el modelo definitivo |
| ¿Qué productos tienen alto riesgo de quiebre de stock según las predicciones? | Generar insumo para aprovisionamiento |

### 3.3 Funcionalidad predictiva

**Tabla 14.** Funcionalidad predictiva.

| Campo | Descripción |
|---|---|
| Nombre de la funcionalidad | Pronóstico semanal de demanda por SKU y centro de operación |
| Descripción | Permite estimar la cantidad esperada de unidades a vender de cada producto en las próximas semanas, a partir de variables temporales, de calendario, de rezagos históricos y de clasificación de rotación. |
| Preguntas de negocio | ¿Cuánto se espera vender de cada producto? ¿Qué productos tienen mayor riesgo de agotarse? |
| Tipo de solución | Modelo predictivo de regresión sobre series temporales |
| Variables o dimensiones involucradas | Item, centro de operación, año, semana, mes, línea N1 y N2, proveedor, clase ABC y XYZ, rezagos de cantidad, medias móviles, festivos de Colombia |
| Métricas o indicadores | MAE, RMSE, MAPE, sMAPE, predicción semanal por SKU |
| Nivel de análisis o granularidad | SKU × centro de operación × semana |
| Fuente de datos | Tabla `ventas_semanales` enriquecida con features generadas en `src/features.py` |
| Transformaciones requeridas | Expansión de la serie, generación de lags, medias móviles, codificación categórica, partición temporal, entrenamiento de modelos, generación de predicciones |
| Salida esperada | Modelos entrenados, tabla `pronosticos` con predicciones, tabla `metricas_modelos` con desempeño |
| Frecuencia de actualización | Única vez para el alcance del proyecto académico |

### 3.4 Historias de usuario predictivas

#### Historia de usuario 4

**Tabla 15.** HU-04: Pronóstico semanal de unidades por SKU.

| Campo | Descripción |
|---|---|
| ID | HU-04 |
| Nombre | Pronóstico semanal de unidades por SKU |
| Rol | Gerente de Operaciones |
| Descripción | Como Gerente de Operaciones, quiero conocer la cantidad estimada de unidades que se venderán de cada producto en las próximas semanas, para disponer de un insumo cuantitativo que oriente las decisiones de aprovisionamiento. |
| Variables o dimensiones | Item, centro de operación, fecha de inicio de semana |
| Métricas | Cantidad predicha, modelo utilizado |
| Filtro o contexto | Filtros por SKU, centro, período de predicción |
| Fuente de datos | Tabla `pronosticos` |
| Salida esperada | Listado de predicciones con valor estimado por semana, exportable a Excel |

#### Historia de usuario 5

**Tabla 16.** HU-05: Identificación de productos con riesgo de quiebre de stock.

| Campo | Descripción |
|---|---|
| ID | HU-05 |
| Nombre | Identificación de productos con riesgo de quiebre de stock |
| Rol | Gerente de Operaciones |
| Descripción | Como Gerente de Operaciones, quiero identificar los productos cuya demanda predicha muestre tendencia creciente o supere niveles históricos, para disponer de información que oriente la priorización en compras y minimice el riesgo de quiebre de stock. |
| Variables o dimensiones | Item, clase ABC, clase XYZ, cantidad predicha, cantidad histórica |
| Métricas | Predicción semanal, variación respecto a la media histórica, ranking de riesgo |
| Filtro o contexto | SKUs clase A y B, ventana de 4-8 semanas hacia adelante |
| Fuente de datos | Tablas `pronosticos`, `clasificacion_abc_xyz`, `ventas_semanales` |
| Salida esperada | Listado priorizado de SKUs con alto riesgo de quiebre, exportable a Excel |

#### Historia de usuario 6

**Tabla 17.** HU-06: Evaluación del desempeño del modelo predictivo.

| Campo | Descripción |
|---|---|
| ID | HU-06 |
| Nombre | Evaluación del desempeño del modelo predictivo |
| Rol | Analista de Datos |
| Descripción | Como Analista de Datos del equipo del proyecto, quiero evaluar la confiabilidad del modelo predictivo mediante métricas estandarizadas (MAE, RMSE, MAPE, sMAPE) globales y por segmento ABC/XYZ, para sustentar técnicamente la selección del modelo y comunicar sus limitaciones a la organización. |
| Variables o dimensiones | Modelo, segmento ABC/XYZ, horizonte de predicción |
| Métricas | MAE, RMSE, MAPE, sMAPE, número de SKUs y observaciones por segmento |
| Filtro o contexto | Comparación entre baseline, LightGBM, XGBoost y Prophet |
| Fuente de datos | Tabla `metricas_modelos` |
| Salida esperada | Tabla comparativa de modelos + gráficos de residuales en notebook |

### 3.5 Requerimientos de datos predictivos

#### Requerimiento 4

**Tabla 18.** RD-04: Preparación del dataset semanal y construcción de features.

| Campo | Descripción |
|---|---|
| ID | RD-04 |
| Nombre del requerimiento | Preparación del dataset semanal y construcción de features predictivas |
| Descripción | Se requiere transformar las ventas transaccionales en una serie semanal por SKU × centro, generando las features necesarias para el modelado (lags, medias móviles, variables de calendario, festivos, clasificación ABC/XYZ, estadísticas por SKU). |
| Historia de usuario asociada | HU-04 |
| Tipo de requerimiento | Ciencia de datos / preparación para modelo predictivo |
| Variables o dimensiones involucradas | Item, centro de operación, fecha de inicio de semana, cantidad, valor bruto |
| Métricas requeridas | Variable objetivo `cantidad_total`, features predictivas |
| Nivel de granularidad | SKU × centro × semana |
| Filtros o criterios | Período 2024-2025 estricto; serie expandida con ceros para semanas sin venta |
| Fuente de datos | Tabla `ventas_semanales` |
| Transformaciones requeridas | Expansión de serie, generación de lags (1, 2, 4, 8, 13, 52), medias móviles (4, 13 semanas), variables cíclicas, festivos de Colombia, codificación categórica, estadísticas por SKU calculadas solo sobre train |
| Técnica o método sugerido | Feature engineering para series temporales (sin data leakage) |
| Salida esperada | Dataset listo para modelado, dividido en train / validación / test por fecha |
| Criterios de aceptación | Las features de rezago deben respetar el orden temporal; las estadísticas por SKU deben calcularse exclusivamente sobre el set de entrenamiento. |

#### Requerimiento 5

**Tabla 19.** RD-05: Entrenamiento de modelos de forecasting.

| Campo | Descripción |
|---|---|
| ID | RD-05 |
| Nombre del requerimiento | Entrenamiento y comparación de modelos de forecasting |
| Descripción | Se requiere entrenar un baseline (media móvil 4 semanas), un modelo principal (LightGBM) y dos modelos de comparación (XGBoost para todo el portafolio, Prophet para el top 50 SKUs clase A). |
| Historia de usuario asociada | HU-04, HU-06 |
| Tipo de requerimiento | Ciencia de datos / machine learning |
| Variables o dimensiones involucradas | Todas las features generadas en RD-04 |
| Métricas requeridas | MAE, RMSE, MAPE, sMAPE en validación y test, globales y por segmento ABC/XYZ |
| Nivel de granularidad | SKU × centro × semana |
| Filtros o criterios | Partición temporal estricta: train 2024-01 a 2025-09, validation Q4 2025, test 2026 (enero-marzo). Los datos de 2022 y abril 2026 (parcial) se descartan. |
| Fuente de datos | Dataset preparado en RD-04 |
| Transformaciones requeridas | Partición temporal, entrenamiento con early stopping, predicciones con `np.clip(0, None)` para evitar valores negativos |
| Técnica o método sugerido | Baseline + LightGBM (principal) + XGBoost (comparación) + Prophet (top 50 SKUs A) |
| Salida esperada | Modelos serializados, predicciones cargadas en tabla `pronosticos`, métricas cargadas en tabla `metricas_modelos` |
| Criterios de aceptación | Al menos un modelo debe superar al baseline en MAE; las métricas deben reportarse globales y por segmento; las predicciones no pueden ser negativas. |

#### Requerimiento 6

**Tabla 20.** RD-06: Generación de pronósticos finales y análisis comparativo.

| Campo | Descripción |
|---|---|
| ID | RD-06 |
| Nombre del requerimiento | Generación de pronósticos finales y análisis comparativo por segmento ABC/XYZ |
| Descripción | Se requiere consolidar las predicciones del modelo seleccionado, generar el ranking de productos con mayor demanda esperada y producir las visualizaciones comparativas que respaldan la recomendación final. |
| Historia de usuario asociada | HU-05, HU-06 |
| Tipo de requerimiento | Producto analítico |
| Variables o dimensiones involucradas | Item, centro de operación, fecha de inicio de semana, predicción, segmento ABC/XYZ |
| Métricas requeridas | Cantidad predicha, variación vs. media histórica, ranking de riesgo |
| Nivel de granularidad | SKU × semana de predicción |
| Filtros o criterios | Horizonte de 4 a 8 semanas |
| Fuente de datos | Tabla `pronosticos` consolidada |
| Transformaciones requeridas | Ordenamiento por predicción y por desviación respecto a la media; cruce con `clasificacion_abc_xyz` |
| Técnica o método sugerido | Scoring + ranking + visualizaciones comparativas |
| Salida esperada | Listados priorizados, gráficos reales vs predichos, tabla comparativa de modelos |
| Criterios de aceptación | Los pronósticos deben ser interpretables por la organización; el ranking debe estar segmentado por clase ABC. |

### 3.6 Variable objetivo del modelo

**Tabla 21.** Variable objetivo del modelo predictivo.

| Característica | Descripción |
|---|---|
| Nombre | `cantidad_total` |
| Tipo | Numérica continua (regresión, no clasificación) |
| Unidad | Unidades vendidas (puede ser entera o decimal según `unidad_inventario`) |
| Granularidad | Suma de unidades vendidas por SKU × centro × semana |
| Rango esperado | ≥ 0 (se aplica `np.clip(pred, 0, None)` a las predicciones) |
| Origen | Columna `cantidad_total` de la tabla `ventas_semanales` |

**Nota metodológica:** A diferencia del ejemplo PAE (que trabaja clasificación), este proyecto aborda un problema de **regresión sobre series temporales**. Por esa razón las métricas usadas son MAE, RMSE, MAPE y sMAPE, en lugar de accuracy, precision o recall.

### 3.7 Variables sugeridas para el modelo

**Tabla 22.** Variables sugeridas para el modelo predictivo.

| Tipo de variable | Variables |
|---|---|
| Identificadores | Item, centro_operacion |
| Categóricas de producto | Línea de producto N1, línea N2, proveedor |
| Temporales (calendario) | Mes, semana ISO, trimestre, día del año |
| Temporales (cíclicas) | Seno y coseno de mes, seno y coseno de semana |
| Festivos | Número de festivos de Colombia en la semana |
| Rezagos | Lags 1, 2, 4, 8, 13 y 52 semanas |
| Medias móviles | Media de 4 y 13 semanas previas, desviación móvil de 4 semanas |
| Tendencia | Diferencia respecto a la semana anterior, ratio vs. media del SKU |
| Estadísticas por SKU | Media, mediana, desviación, mínimo, máximo (solo sobre train) |
| Clasificación de rotación | Clase ABC y clase XYZ (codificadas numéricamente) |

### 3.8 Métricas para evaluar el modelo

**Tabla 23.** Métricas de evaluación del modelo predictivo.

| Métrica | Uso |
|---|---|
| MAE | Error absoluto promedio en unidades reales — métrica principal por su interpretabilidad |
| RMSE | Penaliza errores grandes; útil para detectar quiebres en SKUs críticos |
| MAPE | Error porcentual; permite comparar entre SKUs con escalas distintas (excluye y_true ≈ 0) |
| sMAPE | Variante simétrica robusta a ceros; complementa a MAPE en SKUs con demanda esporádica |
| Comparación con baseline | Diferencia entre MAE del modelo y MAE del baseline media móvil 4 semanas |

**La métrica principal de selección de modelo es el MAE**, porque está expresada en unidades vendidas (interpretable por la organización beneficiaria). Las métricas se reportan globalmente y segmentadas por clase ABC/XYZ.

### 3.9 Salidas esperadas del proyecto predictivo

**Tabla 24.** Salidas esperadas del análisis predictivo.

| Salida | Descripción |
|---|---|
| Dataset preparado | Tabla con features listas para modelado, dividida temporalmente |
| Modelos entrenados | Archivos `.pkl` de baseline, LightGBM, XGBoost y Prophet |
| Tabla `pronosticos` | Predicciones semanales por SKU para el horizonte de prueba |
| Tabla `metricas_modelos` | Métricas de cada modelo, globales y por segmento ABC/XYZ |
| Gráficos comparativos | Real vs predicho, residuales, importancia de features |
| Listado priorizado | SKUs con mayor riesgo de quiebre, exportable a Excel |
| Recomendaciones | Insumos analíticos para apoyar decisiones de aprovisionamiento |

---

## 4. Comparación entre los dos temas

**Tabla 25.** Comparación entre el enfoque descriptivo y el predictivo.

| Elemento | Tema 1 — Descriptivo | Tema 2 — Predictivo |
|---|---|---|
| Pregunta central | ¿Cuál es el patrón actual de rotación? | ¿Cuál será la demanda semanal futura? |
| Propósito | Caracterizar el portafolio actual | Anticipar la demanda |
| Técnica principal | Análisis de Pareto + coeficiente de variación | Regresión sobre series temporales (LightGBM, XGBoost, Prophet) |
| Variable objetivo | No aplica (es descriptivo) | `cantidad_total` (continua) |
| Métricas | Porcentajes acumulados, CV, conteo por segmento | MAE, RMSE, MAPE, sMAPE |
| Resultado principal | Clasificación ABC/XYZ + dashboard | Modelo entrenado + pronósticos semanales |
| Decisión que apoya | Organización de bodega | Aprovisionamiento |
| Usuario principal | Gerente de Operaciones | Gerente de Operaciones |
| Peso en el proyecto | Complementario | **Principal** |
| Entregable clave | Dashboard descriptivo en Tableau | Modelo predictivo + tabla de pronósticos |

---

## 5. Conclusión del anexo

Este anexo aplicó la metodología de requerimientos del programa al proyecto de ConstruNorte, articulando dos enfoques complementarios sobre el mismo dataset transaccional. El **enfoque descriptivo** (Tema 1) genera una caracterización de la rotación mediante clasificación ABC/XYZ y un dashboard interactivo, mientras que el **enfoque predictivo** (Tema 2), que constituye el énfasis principal del proyecto, construye un modelo de machine learning capaz de pronosticar la demanda semanal por producto.

Ambos enfoques producen **insumos analíticos** que la organización beneficiaria podrá utilizar para orientar decisiones de organización de bodega y aprovisionamiento, respectivamente. El equipo del proyecto se limita a la entrega de estos insumos; las decisiones operativas finales corresponden exclusivamente a ConstruNorte.

La articulación entre épica, funcionalidad, historias de usuario, requerimientos de datos, indicadores y salidas esperadas garantiza la trazabilidad entre la necesidad del negocio, los datos disponibles, las técnicas aplicadas y los productos finales del proyecto.