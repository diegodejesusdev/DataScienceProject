# CLAUDE.md — Proyecto ConstruNorte

Este archivo le dice a Claude Code todo lo que necesita saber para trabajar en este proyecto. **Lee este archivo completo antes de hacer cualquier cambio.**

> **Estado:** Proyecto finalizado y entregado el 28 de mayo de 2026. Cualquier trabajo futuro es mantenimiento o consulta de referencia.

---

## 1. Contexto del proyecto

**Título:** Análisis predictivo de la rotación de inventarios mediante machine learning aplicado a las ventas históricas de CONSTRUNORTE COMERCIALIZADORA S.A.S., periodo 2024–2025.

**Equipo:** Diego Andrés De Jesús Montenegro y Luis David Andrade Díaz.
**Institución:** Corporación Universitaria Comfacauca — Unicomfacauca.
**Programa:** Diplomado en Ingeniería y Ciencia de Datos Aplicada.
**Tutor:** Ing. Francisco Javier Obando.
**Entrega:** 28 de mayo de 2026 (completado).

### Pregunta de investigación

> ¿Cómo puede un modelo de machine learning, entrenado con datos transaccionales de CONSTRUNORTE COMERCIALIZADORA S.A.S. del período 2024–2025, pronosticar la demanda futura por producto e identificar patrones de rotación que contribuyan a la toma de decisiones sobre aprovisionamiento y organización de bodega?

### Objetivo general

Desarrollar un modelo de machine learning para pronosticar la demanda futura por producto en CONSTRUNORTE COMERCIALIZADORA S.A.S., mediante la aplicación de la metodología CRISP-DM sobre datos transaccionales del período 2024–2025, con el fin de generar insumos analíticos sobre demanda y rotación que apoyen las decisiones de aprovisionamiento y organización de bodega.

### Objetivos específicos

- **OE1.** Comprender el contexto comercial, logístico y de inventario de CONSTRUNORTE COMERCIALIZADORA S.A.S., así como los datos transaccionales disponibles del período 2024–2025, mediante la identificación de fuentes de información, y la realización de un análisis exploratorio de datos —EDA— que permita reconocer patrones iniciales de venta y rotación de productos.
- **OE2.** Preparar los datos transaccionales mediante procesos de limpieza, depuración, transformación y construcción de variables, con el fin de generar un conjunto de datos adecuado para el análisis y modelado predictivo.
- **OE3.** Construir modelos de machine learning para pronosticar la demanda futura por producto, evaluando su desempeño mediante métricas de precisión que permitan seleccionar el modelo más adecuado para apoyar decisiones de aprovisionamiento.
- **OE4.** Evaluar los resultados del pronóstico y los patrones de rotación de productos mediante indicadores, tablas y visualizaciones, con el fin de generar insumos analíticos que orienten la organización de bodega y la toma de decisiones logísticas.

### Periodo de análisis

| Bloque | Filas | Tratamiento |
|---|---|---|
| 2022 | 22.611 | Descartado (anterior a facturación electrónica, descontinuo) |
| 2024–2025 | 543.808 | **Periodo principal de modelado** |
| 2026-01 a 2026-03 | 75.213 | **Test extendido** ("futuro real", no visto en entrenamiento) |
| 2026-04 (parcial) | 18.950 | Descartado (mes incompleto) |

**Partición temporal:**

```
Train:        2024-01-01 → 2025-09-30   (21 meses)
Validation:   2025-10-01 → 2025-12-31   ( 3 meses)
Test 2026:    2026-01-01 → 2026-03-31   ( 3 meses, out-of-sample real)
```

### Estructura en dos temas

| Tema | Enfoque | Entregable |
|---|---|---|
| **Tema 1** | Descriptivo | Clasificación ABC/XYZ + dashboard de rotación |
| **Tema 2** | Predictivo | Modelos de forecasting + pronósticos semanales |

**Enfoque principal: predictivo (Tema 2).** El descriptivo (Tema 1) es complementario.

### Alcance del equipo

Este equipo **entrega insumos analíticos** (predicciones, clasificaciones, métricas, visualizaciones). La organización ConstruNorte decide qué hacer con esa información.

- ✅ "para apoyar decisiones de aprovisionamiento" / "para orientar la organización de bodega"
- ❌ NO "para reorganizar la bodega" / "para hacer pedidos" / "para decidir compras"

---

## 2. Stack tecnológico

| Capa | Herramienta | Dónde corre |
|---|---|---|
| Contenedorización | Docker + Docker Compose | Host (Mac) |
| Base de datos | MySQL 8.0 | Contenedor `construnorte_mysql` |
| Admin BD (GUI web) | Adminer | Contenedor `construnorte_adminer` |
| Ambiente análisis | Jupyter Lab + Python 3.11 | Contenedor `construnorte_jupyter` |
| Ingesta inicial del CSV | Apache Hop | Nativo en Mac |
| ETL principal, modelado | Python (Jupyter) | Contenedor Jupyter |
| API REST | FastAPI + Uvicorn | Nativo (`.venv`) |
| Dashboard web | HTML + CSS + JS (servido por FastAPI) | Nativo (`.venv`) |
| Dashboard analítico | Tableau Desktop | Nativo en Mac |
| Control de versiones | Git + GitHub | Host |

**Librerías Python clave:** pandas, numpy, sqlalchemy, pymysql, scikit-learn, lightgbm, xgboost, prophet, matplotlib, seaborn, plotly, holidays, fastapi, uvicorn, pydantic.

**Modelos ML entrenados y comparados:**

1. **Baseline** (media móvil 4 semanas) — sirve de piso de comparación.
2. **LightGBM Regressor** — modelo principal global; modelo guardado en `data/processed/lightgbm_model.txt`.
3. **XGBoost Regressor** — modelo de comparación; guardado en `data/processed/xgboost_model.json`.
4. **Prophet** — comparación en SKUs individuales del top.

---

## 3. Estructura del repositorio

```
DataScienceProject/
├── CLAUDE.md                       # Este archivo
├── README.md                       # Instrucciones públicas
├── docker-compose.yml              # Orquestación Docker (MySQL + Adminer + Jupyter)
├── .env                            # (gitignored) credenciales locales
├── .env.example                    # Plantilla pública sin contraseñas
├── .gitignore
├── requirements_api.txt            # Dependencias de la API REST
├── .claude/
│   └── skills/                     # Skills especializadas para Claude Code
├── docker/
│   └── jupyter/
│       ├── Dockerfile
│       └── requirements.txt        # Librerías del contenedor Jupyter
├── db/
│   └── init/
│       └── 01_schema.sql           # Schema MySQL (autoejecutado al levantar)
├── data/
│   ├── raw/                        # CSV original (gitignored)
│   └── processed/                  # Datasets intermedios y modelos (gitignored)
│       ├── dataset_modelable.parquet
│       ├── lightgbm_model.txt
│       └── xgboost_model.json
├── notebooks/
│   ├── 01_perfil_inicial.ipynb     # Comprensión del dataset
│   ├── 02_eda.ipynb                # Análisis exploratorio
│   ├── 03_preparacion.ipynb        # Limpieza, ETL y feature engineering
│   ├── 04_abc_xyz.ipynb            # Clasificación ABC/XYZ
│   ├── 05_baseline.ipynb           # Modelo baseline
│   ├── 06_lightgbm.ipynb           # LightGBM
│   ├── 07_xgboost.ipynb            # XGBoost
│   ├── 08_prophet.ipynb            # Prophet
│   └── 09_evaluacion_final.ipynb   # Comparación y evaluación final
├── src/                            # Módulos Python reutilizables
│   ├── db.py                       # Conexión SQLAlchemy a MySQL
│   ├── etl.py                      # Pipeline ETL
│   ├── features.py                 # Feature engineering
│   ├── abc_xyz.py                  # Clasificación ABC/XYZ
│   ├── models.py                   # Entrenamiento de modelos
│   └── evaluation.py               # Métricas MAE/RMSE/MAPE/sMAPE
├── api/                            # API REST + dashboard web
│   ├── main.py                     # FastAPI app principal
│   ├── config.py                   # Variables de entorno
│   ├── database.py                 # Engine SQLAlchemy + helper query()
│   ├── schemas.py                  # Modelos Pydantic v2
│   ├── routers/
│   │   ├── pronosticos.py          # /api/pronosticos/*
│   │   ├── clasificacion.py        # /api/clasificacion/*
│   │   ├── metricas.py             # /api/metricas/*
│   │   ├── insights.py             # /api/insights/*
│   │   └── descriptivo.py          # /api/descriptivo/*
│   └── static/                     # Frontend (index.html, app.js, styles.css, colors.js)
├── hop/
│   └── ingesta_csv.hpl             # Flujo de ingesta CSV → MySQL (Apache Hop)
├── reports/
│   ├── clasificacion_abc_xyz.xlsx
│   ├── evaluacion_final.xlsx
│   └── figures/                    # Figuras generadas por los notebooks
├── dashboard/                      # Workbook de Tableau
└── docs/                           # Documentación técnica del proyecto
```

---

## 4. Dataset

**Fuente:** CSV transaccional de ConstruNorte (~660K filas, 33 columnas, periodo 2022–2026).

**Granularidad de la fila cruda:** una línea de remisión/venta por SKU.

**Variables que se RETIENEN:**
- `Fecha`, `Item`, `Nombre Item`, `Referencia Item`, `Codigo Barra Item`
- `Unidad Inventario 1 Item`, `Proveedor Codigo Item`, `Proveedor Nombre Item`
- `Nombre Linea N1`, `Nombre Linea N2`, `Centro de Operacion`, `Tipo de Documento`
- `Cantidad 1`, `Precio Uni`, `Valor Bruto`, `Valor Costo`, `Peso`

**Variables que se ELIMINAN (datos personales — Ley 1581 de 2012):**
- `Cliente`, `Nombre Cliente`, `Direccion Cliente`, `Nit Cliente`
- `Ciudad Cliente`, `Ciudad Descripcion Cliente`, `Nombre Criterio Cliente 1`
- `Vendedor`, `Nombre Vendedor`, `Cedula Vendedor`
- `Documento Remision`, `Documento Ventas`, `Documento Pedido`

Los `df.drop()` correspondientes se ejecutan en la fase de preparación, antes de almacenar en MySQL.

---

## 5. Convenciones de código

### Python
- PEP 8. UTF-8. Type hints en funciones públicas. Docstrings Google style.
- Variables de dominio en español (`cantidad`, `valor_bruto`), técnicas en inglés (`train`, `predict`).
- Constantes en `UPPER_SNAKE_CASE`. Imports: stdlib → third-party → local.
- `logging` en módulos `src/`; `print()` solo en notebooks.

### SQL
- Tablas y columnas en `snake_case` en español.
- PK: `id`. FK: `<tabla>_id`. Fechas: `DATE`. Timestamps: `TIMESTAMP`.
- Toda tabla tiene `created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`.

### Git
- Commits en español, imperativo: `"feat: agregar limpieza de outliers"`.
- Prefijos: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`, `test:`, `wip:`.
- NO commitear: `data/raw/`, `data/processed/`, `.env`, notebooks con outputs pesados.

---

## 6. Comandos esenciales

### Docker
```bash
docker compose up -d              # Levantar los 3 servicios
docker compose down               # Apagar (mantiene datos)
docker compose down -v            # Apagar y BORRAR datos
docker compose ps                 # Ver estado
docker compose logs -f mysql      # Ver logs
docker compose build jupyter      # Rebuild tras cambiar requirements.txt
```

### MySQL
```bash
docker exec -it construnorte_mysql mysql -u construnorte_user -p construnorte
docker exec construnorte_mysql mysqldump -u root -p construnorte > backup.sql
```

### Jupyter
- `http://localhost:8888/?token=<JUPYTER_TOKEN>`
- Adminer: `http://localhost:8080` (servidor: `mysql`)

### API REST
```bash
.venv/bin/pip install -r requirements_api.txt   # solo primera vez
.venv/bin/uvicorn api.main:app --reload --port 8000
```
- Dashboard web: `http://localhost:8000/`
- Swagger: `http://localhost:8000/docs`

---

## 7. Reglas que Claude Code debe seguir SIEMPRE

1. **NUNCA hagas split aleatorio de los datos.** Siempre partición temporal manual o `TimeSeriesSplit`.
2. **NUNCA pongas credenciales en el código.** Todo va en `.env`.
3. **NUNCA subas el dataset original a Git.** `data/raw/` y `data/processed/` están en `.gitignore`.
4. **NUNCA proceses datos personales.** Si la variable está en la lista de ELIMINAR, no debe llegar a MySQL.
5. **SIEMPRE agrega a granularidad SEMANAL por SKU antes de modelar.** `(item, año, semana, centro_operacion) → cantidad_total`.
6. **SIEMPRE reporta MAE, RMSE y MAPE juntos.** Si hay ceros en el target, usa sMAPE como alternativa.
7. **SIEMPRE compara contra el baseline** (media móvil 4 semanas).
8. **NO instales librerías nuevas** sin actualizar `docker/jupyter/requirements.txt` o `requirements_api.txt` según corresponda.

---

## 8. Skills disponibles

| Skill | Cuándo leerla |
|---|---|
| `project-conventions/` | Antes de crear cualquier archivo nuevo |
| `mysql-operations/` | Antes de tocar tablas o cargar datos |
| `etl-pipeline/` | Antes de procesar el CSV o cargar a MySQL |
| `feature-engineering/` | Antes de generar features |
| `abc-xyz-classification/` | Antes de calcular ABC/XYZ |
| `time-series-modeling/` | Antes de entrenar modelos |
| `evaluation-metrics/` | Antes de calcular o reportar métricas |
| `notebook-style/` | Antes de crear o modificar notebooks |
| `requirements-style/` | Antes de redactar requerimientos en `docs/` |

---

## 9. Privacidad y seguridad

- Dataset protegido por la **Ley 1581 de 2012** de Colombia.
- Carta de autorización firmada por ConstruNorte (Anexo C del informe).
- Los archivos crudos viven solo en equipos del equipo, protegidos por contraseña.
- El repositorio público en GitHub **nunca** contiene el dataset original.
