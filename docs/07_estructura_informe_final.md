# 07 — Estructura del Informe Técnico Final

> Plantilla obligatoria del informe técnico del proyecto integrador, según la rúbrica oficial del diplomado.

---

## Capítulos exigidos

La rúbrica del diplomado establece la siguiente estructura **obligatoria** para el informe técnico final.

### 1. Portada

Datos institucionales, título del proyecto, integrantes del equipo, tutor, ciudad y fecha (Popayán, mayo 2026).

### 2. Capítulo 1 — Introducción

- **2.1 Resumen**: máximo una página con problema, objetivos, metodología, resultados clave y conclusiones.
- **2.2 Introducción**: contextualización general.
- **2.3 Planteamiento del problema o necesidad**: redacción tomada de `docs/01_comprension_negocio.md`.
- **2.4 Pregunta analítica / de investigación**.
- **2.5 Objetivos**:
  - 2.5.1 Objetivo general
  - 2.5.2 Objetivos específicos (OE1, OE2, OE3, OE4)
- **2.6 Metodología**: CRISP-DM aplicada al proyecto.

### 3. Capítulo 2 — Marco teórico

- **3.1 Contexto**: conceptos relacionados con el proyecto (forecasting de demanda, rotación de inventarios, ABC/XYZ, machine learning supervisado para series temporales, métricas de evaluación, ETL).
- **3.2 Antecedentes**: al menos **5 estudios previos o similares** sobre forecasting de demanda en retail, ferretería o materiales de construcción.
- **3.3 Herramientas usadas**: MySQL, Apache Hop, Python, Jupyter, LightGBM, XGBoost, Prophet, Tableau, Docker, Git.

### 4. Capítulo 3 — Desarrollo del Objetivo Específico 1

Comprensión del negocio y de los datos:
- Caracterización de ConstruNorte.
- Identificación de fuentes y dataset.
- EDA inicial: distribuciones, tipos de documento, rango de fechas, calidad de datos.
- Hallazgos del perfil inicial.

### 5. Capítulo 4 — Desarrollo del Objetivo Específico 2

Preparación de los datos:
- Pipeline ETL (Apache Hop + Python).
- Decisiones de limpieza y filtrado documentadas en `docs/05_decisiones_tecnicas.md`.
- Cumplimiento de Ley 1581 (anonimización en ingesta).
- Feature engineering (lags, medias móviles, calendario, festivos).
- Construcción del dataset modelable.

### 6. Capítulo 5 — Desarrollo del Objetivo Específico 3

Modelado predictivo:
- Partición temporal (no aleatoria).
- Entrenamiento del baseline (media móvil 4 semanas).
- Entrenamiento de LightGBM, XGBoost.
- Entrenamiento de Prophet para top 50 SKUs clase A.
- Hiperparámetros y decisiones técnicas.
- Métricas obtenidas y comparación entre modelos.
- Selección del modelo definitivo.

### 7. Capítulo 6 — Desarrollo del Objetivo Específico 4

Evaluación de resultados e insumos para la organización:
- Clasificación ABC/XYZ aplicada al portafolio.
- Análisis del modelo seleccionado por segmento ABC/XYZ.
- Visualizaciones del dashboard descriptivo.
- Generación de pronósticos finales.
- Ranking de SKUs prioritarios por demanda esperada.
- Lectura de los hallazgos en lenguaje de negocio.

### 8. Capítulo 7 — Conclusiones

- Cumplimiento de cada objetivo específico.
- Respuesta consolidada a la pregunta de investigación.
- Valor de los insumos para la organización beneficiaria.

### 9. Capítulo 8 — Lecciones aprendidas y trabajo futuro

- Limitaciones identificadas durante el proyecto.
- Buenas prácticas que el equipo destaca.
- Trabajo futuro recomendado: integración en tiempo real, ampliación del horizonte, modelo jerárquico, segmentación de clientes (cuando se firme nuevo acuerdo de tratamiento de datos personales).

### 10. Referencias y anexos

- Referencias bibliográficas en formato IEEE (mínimo las 5 del marco teórico).
- Anexo A: Requerimientos de datos (Tema 1 y Tema 2). Ver `docs/06_requerimientos_datos.md`.
- Anexo B: Diagrama de arquitectura técnica.
- Anexo C: Carta de autorización firmada por ConstruNorte.
- Anexo D: Diccionario de datos. Ver `docs/02_diccionario_datos.md`.

---

## Alineación con la rúbrica oficial

| Capítulo del informe | Criterio que cubre | Peso en rúbrica |
|---|---|---|
| Cap. 1 (Introducción) | Definición del problema y objetivos | 5% |
| Caps. 3, 4, 5 (OE1, OE2, OE3) | Desarrollo técnico y aplicación de metodologías | 30% |
| Caps. 5, 6 (OE3, OE4) | Calidad del análisis y resultados | 20% |
| Cap. 6 + Dashboard | Visualización, interpretación y comunicación | 20% |
| Sustentación oral | Presentación y sustentación final | 25% |

## Recomendaciones de redacción

- Usar **prosa técnica formal**; evitar primera persona.
- Cada capítulo debe arrancar con un párrafo introductorio que resuma su contenido.
- Las tablas deben numerarse y referenciarse en el texto (Tabla X, Figura Y).
- Citas en formato IEEE numeradas: `[1]`, `[2]`, etc.
- Toda decisión técnica importante debe estar justificada en el cuerpo del texto, con referencia al anexo correspondiente.
- Las gráficas deben tener título, leyenda, ejes etiquetados y, cuando aplique, escala y unidades.
- El informe se redacta en español de Colombia, formal pero claro.
- Antes de entregar, leer el documento completo para verificar coherencia entre capítulos.

## Recordatorios críticos

- El equipo **entrega insumos analíticos**, no toma decisiones operativas. Esto debe reflejarse en toda la redacción.
- El periodo de análisis es **estricto 2024-2025**. Datos de 2022 y 2026 se descartan (justificación en Cap. 4).
- Los datos personales se anonimizaron en la fase de ingesta (cumplimiento de Ley 1581 — citar en Cap. 4).
- El modelo predictivo es de **regresión sobre series temporales**, no de clasificación. Métricas: MAE, RMSE, MAPE, sMAPE.
- Toda predicción supera `np.clip(0, None)` para evitar valores negativos sin sentido físico.
- Partición temporal estricta. **No** usar split aleatorio.