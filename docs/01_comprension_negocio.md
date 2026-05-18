# 01 — Comprensión del negocio

> Fase 1 de CRISP-DM. Documenta el contexto de la organización, el problema identificado, los objetivos y las preguntas que orientan el proyecto.

---

## 1. Organización beneficiaria

**CONSTRUNORTE COMERCIALIZADORA S.A.S.** es una empresa colombiana dedicada a la comercialización de materiales de construcción, ferretería y suministros para obra. Opera mediante tres bodegas o centros de operación identificados con los códigos `001`, `002` y `003`, atendiendo tanto clientes corporativos (constructoras, empresas) como consumidores individuales.

## 2. Contexto del problema

ConstruNorte registra cada transacción de venta en su sistema transaccional. Sin embargo, esta información se utiliza principalmente con fines contables y operativos, sin que exista un análisis sistemático que permita:

- Caracterizar la rotación real de cada uno de los productos comercializados.
- Anticipar la demanda futura por producto y por bodega.
- Identificar patrones de comportamiento de las ventas a lo largo del tiempo.

Como consecuencia, las decisiones de aprovisionamiento y de organización de bodega se basan principalmente en la experiencia del personal, lo cual puede generar:

- **Quiebres de stock** en productos de alta rotación o demanda creciente.
- **Sobreinventario** en productos de baja rotación o demanda errática.
- **Uso ineficiente del espacio físico** en bodega, al no priorizar la accesibilidad de los productos más movidos.

## 3. Necesidad identificada

ConstruNorte requiere **insumos analíticos basados en datos** que orienten dos tipos de decisiones:

| Tipo de decisión | Pregunta de negocio que responde |
|---|---|
| **Aprovisionamiento** | ¿Cuánto se espera vender de cada producto en las próximas semanas? ¿Qué productos requieren mayor anticipación de compra? ¿Cuáles tienen alto riesgo de agotarse? |
| **Organización de bodega** | ¿Qué productos se mueven más rápido y deberían ubicarse en zonas de fácil acceso? ¿Qué productos tienen baja rotación y ocupan espacio sin generar movimiento? |

## 4. Pregunta de investigación

> ¿Cómo puede un modelo de machine learning, entrenado con datos transaccionales de CONSTRUNORTE COMERCIALIZADORA S.A.S. del período 2024–2025, pronosticar la demanda futura por producto e identificar patrones de rotación que contribuyan a la toma de decisiones sobre aprovisionamiento y organización de bodega?

## 5. Objetivos del proyecto

### Objetivo general

Desarrollar un modelo de machine learning para pronosticar la demanda futura por producto en CONSTRUNORTE COMERCIALIZADORA S.A.S., mediante la aplicación de la metodología CRISP-DM sobre datos transaccionales del período 2024–2025, con el fin de generar insumos analíticos sobre demanda y rotación que apoyen las decisiones de aprovisionamiento y organización de bodega.

### Objetivos específicos

- **OE1.** Comprender el contexto comercial, logístico y de inventario de CONSTRUNORTE COMERCIALIZADORA S.A.S., así como los datos transaccionales disponibles del período 2024–2025, mediante la identificación de fuentes de información y la realización de un análisis exploratorio de datos —EDA— que permita reconocer patrones iniciales de venta y rotación de productos.
- **OE2.** Preparar los datos transaccionales mediante procesos de limpieza, depuración, transformación y construcción de variables, con el fin de generar un conjunto de datos adecuado para el análisis y modelado predictivo.
- **OE3.** Construir modelos de machine learning para pronosticar la demanda futura por producto, evaluando su desempeño mediante métricas de precisión que permitan seleccionar el modelo más adecuado para apoyar decisiones de aprovisionamiento.
- **OE4.** Evaluar los resultados del pronóstico y los patrones de rotación de productos mediante indicadores, tablas y visualizaciones, con el fin de generar insumos analíticos que orienten la organización de bodega y la toma de decisiones logísticas.

## 6. Alcance del proyecto

### Lo que el proyecto SÍ incluye

- Análisis exploratorio de datos transaccionales del periodo 2024-2025.
- Clasificación ABC/XYZ de los SKUs comercializados.
- Modelo predictivo de demanda a nivel SKU × centro de operación × semana.
- Dashboard descriptivo de rotación (Tableau).
- Métricas de evaluación del modelo (MAE, RMSE, MAPE, sMAPE) globales y segmentadas.
- Insumos analíticos y recomendaciones para las áreas de aprovisionamiento y bodega.

### Lo que el proyecto NO incluye

- Ejecución de decisiones operativas (compras, reordenamiento físico de bodega).
- Integración en tiempo real con el ERP de ConstruNorte.
- Análisis financiero, rentabilidad o costos asociados a la operación.
- Análisis del comportamiento de clientes o segmentación comercial.
- Datos de proveedores más allá de los identificadores presentes en las transacciones.

### Delimitación temporal

Aunque el dataset original contiene registros parciales de 2022 y de los primeros meses de 2026, el análisis se restringe estrictamente al período **enero 2024 – diciembre 2025**, por las razones documentadas en `docs/05_decisiones_tecnicas.md`.

## 7. Aclaración sobre el rol del equipo

Este proyecto se desarrolla en el marco del Diplomado en Ingeniería y Ciencia de Datos Aplicada (Unicomfacauca). El equipo de trabajo cumple un rol estrictamente analítico: **construye y entrega insumos basados en datos**, no toma decisiones operativas en ConstruNorte. Toda recomendación incluida en los entregables tiene carácter orientativo. Las decisiones finales sobre compras, organización física de bodega o cualquier otra acción operativa son responsabilidad exclusiva de la organización beneficiaria.

## 8. Criterios de éxito

| Tipo | Criterio | Cómo se mide |
|---|---|---|
| Académico | Aprobación del proyecto final con calificación mínima 3.5/5.0 | Rúbrica oficial del diplomado |
| Académico | Cumplimiento de los 4 objetivos específicos | Capítulo por objetivo en el informe final |
| Técnico | El modelo predictivo supera al baseline (media móvil 4 semanas) | Comparación de MAE en validación |
| Técnico | El modelo permite segmentar resultados por clase ABC/XYZ | Métricas reportadas por segmento |
| De negocio | Los entregables son interpretables por personal no técnico | Dashboard navegable + informe ejecutivo |
| Ético | Cumplimiento de la Ley 1581 de 2012 | Anonimización en la ingesta, carta de autorización |