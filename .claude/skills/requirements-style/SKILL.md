---
name: requirements-style
description: Como redactar epicas, historias de usuario y requerimientos de datos siguiendo la metodologia del programa (Diplomado Unicomfacauca). Leeme antes de redactar o modificar el anexo de requerimientos o cualquier seccion equivalente en el informe.
---

# Estilo de redaccion de requerimientos

## Pirámide conceptual del programa

Cada nivel debe poder rastrearse hasta el siguiente. Si una HU no tiene RD asociado, sobra. Si un RD no responde a una HU, sobra.

---

## Formato de épica
**Roles válidos en este proyecto:**
- Gerente de Operaciones (representa a ConstruNorte, usuario final del insumo).
- Analista de Datos (representa al equipo del proyecto, usuario técnico).

⚠️ **NO usar como rol:**
- Jefe de bodega, jefe de compras (el equipo no asesora directamente esa operación).
- Anything que implique que el equipo decide compras u organiza la bodega.

---

## Formato de historia de usuario
Cada HU lleva una tabla con estos campos:

| Campo | Descripción |
|---|---|
| ID | HU-NN |
| Nombre | corto y descriptivo |
| Rol | quien necesita |
| Descripción | la frase "Como... quiero... para..." |
| Variables o dimensiones | qué datos se usan |
| Métricas | qué se calcula |
| Filtro o contexto | restricciones |
| Fuente de datos | tabla o sistema |
| Salida esperada | qué se entrega |

---

## Formato de requerimiento de datos

Cada RD lleva una tabla con estos campos exactos:

| Campo | Obligatorio |
|---|---|
| ID | RD-NN |
| Nombre del requerimiento | ✓ |
| Descripción | ✓ |
| Historia de usuario asociada | ✓ |
| Tipo de requerimiento | ✓ (analítico, ciencia de datos, ingeniería de datos, visualización, etc.) |
| Variables o dimensiones involucradas | ✓ |
| Métricas requeridas | ✓ |
| Nivel de granularidad | ✓ |
| Filtros o criterios | ✓ |
| Fuente de datos | ✓ |
| Transformaciones requeridas | ✓ |
| Técnica o método sugerido | ✓ |
| Salida esperada | ✓ |
| Criterios de aceptación | ✓ |

---

## Reglas de lenguaje (alcance del equipo)

El equipo **entrega insumos analíticos**, no toma decisiones operativas. Esto se refleja en cómo se redactan los "para..." de las épicas y HU.

### Lenguaje correcto (✅)

- "para disponer de información que oriente las decisiones de aprovisionamiento"
- "para identificar productos con alto riesgo de quiebre de stock"
- "para sustentar técnicamente la selección del modelo"
- "para generar un insumo analítico que apoye las decisiones..."
- "para visualizar..."
- "para caracterizar..."
- "para evaluar el desempeño del modelo..."

### Lenguaje incorrecto (❌)

- "para reorganizar la bodega" — el equipo no la reorganiza
- "para comprar X cantidad de productos" — el equipo no compra
- "para decidir qué proveedor priorizar" — el equipo no decide compras
- "para automatizar el aprovisionamiento" — fuera de alcance
- "para mejorar el inventario" — vago y ejecutivo, no analítico

Si tienes duda: cambia "para [verbo ejecutivo]" por "para disponer de información que oriente [verbo ejecutivo]".

---

## Estructura del anexo

El anexo de requerimientos sigue exactamente esta estructura, tomada del ejemplo PAE provisto por el programa:
---

## Convenciones de numeración

- **Historias de usuario:** numeración continua entre Tema 1 y Tema 2.
  - HU-01, HU-02, HU-03 → Tema 1
  - HU-04, HU-05, HU-06 → Tema 2

- **Requerimientos de datos:** numeración continua.
  - RD-01, RD-02, RD-03 → Tema 1
  - RD-04, RD-05, RD-06 → Tema 2

- **Tablas:** numeración global continua (Tabla 1, Tabla 2, ... Tabla N).

---

## Adaptación al proyecto ConstruNorte

| Elemento del ejemplo PAE | Equivalente en ConstruNorte |
|---|---|
| "Estado nutricional" | "Patrón de rotación" |
| "Estudiantes" | "Productos (SKUs)" |
| "Municipio" | "Centro de operación / bodega" |
| "Bajo peso, normal, sobrepeso, obesidad" | "Clase A, B, C (ABC) / X, Y, Z (XYZ)" |
| Variable objetivo binaria/multiclase | Variable objetivo continua (cantidad_total) — regresión |
| Métricas: accuracy, precision, recall | Métricas: MAE, RMSE, MAPE, sMAPE |

⚠️ Aclarar siempre cuando se redacte: "A diferencia del ejemplo PAE (clasificación), este proyecto es regresión sobre series temporales."

---

## Reglas no negociables

1. **Toda HU debe tener al menos un RD asociado.**
2. **Todo RD debe responder a al menos una HU.**
3. **El "para..." nunca describe una acción ejecutiva** que el equipo no hace.
4. **Numeración continua entre Temas 1 y 2.**
5. **El rol "Analista de Datos"** se usa para HUs técnicas (evaluación de modelo, exploración).
6. **El rol "Gerente de Operaciones"** se usa para HUs de negocio (visualizar, consultar, identificar).
7. **Tablas numeradas siempre.** Cada tabla debe referenciarse en el texto (`En la Tabla X se presenta...`).