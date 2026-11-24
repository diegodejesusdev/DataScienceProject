# ConstruNorte — Análisis Predictivo de Rotación de Inventarios

> Proyecto académico del **Diplomado en Ingeniería y Ciencia de Datos Aplicada** — **Corporación Universitaria Comfacauca (Unicomfacauca)**, 2026.

Sistema analítico predictivo que pronostica la demanda y caracteriza la rotación de los productos comercializados por **CONSTRUNORTE COMERCIALIZADORA S.A.S.** durante el periodo enero 2024 – marzo 2026, con el fin de generar insumos analíticos que respalden decisiones de aprovisionamiento y organización de bodega.

![Python](https://img.shields.io/badge/Python_3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![LightGBM](https://img.shields.io/badge/LightGBM-02569B?style=flat-square)
![XGBoost](https://img.shields.io/badge/XGBoost-189FDD?style=flat-square)
![Prophet](https://img.shields.io/badge/Prophet-0668E1?style=flat-square&logo=meta&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL_8-4479A1?style=flat-square&logo=mysql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)
![Tableau](https://img.shields.io/badge/Tableau-E97627?style=flat-square&logo=tableau&logoColor=white)

---

## Resultados

- **Datos:** ventas transaccionales de enero 2024 a marzo 2026 (118 semanas), agregadas a demanda **semanal por SKU × centro de operación**. Se modelaron **2.310 SKUs activos** (de 4.282) en **3 centros**.
- **Partición temporal:** entrenamiento (91 semanas), validación (13) y prueba con datos de 2026 (13).
- **Clasificación ABC/XYZ** de 2.380 SKUs para segmentar el inventario por valor y por variabilidad de la demanda.

Comparación en el conjunto de prueba 2026, sobre los 2.310 SKUs:

| Modelo | MAE | RMSE | Mejora en MAE vs baseline |
|---|---|---|---|
| Baseline (media móvil 4 semanas) | 32.50 | 389.01 | — |
| **LightGBM** | **6.77** | **144.97** | **+79.18 %** |
| XGBoost | 13.25 | 258.42 | +59.23 % |

- **Modelo recomendado: LightGBM.** Gana en validación y en prueba, no se degrada con datos nuevos (MAE 8.85 → 6.77) y cubre todos los SKUs con un solo modelo.
- **Prophet** se evaluó solo en los 50 SKUs clase A más importantes y no superó al baseline de forma relevante (+4.6 % en MAE); se usa para descomponer tendencia y estacionalidad, no para producción.
- Los pronósticos de los 4 modelos (394.855 filas) y sus métricas quedan en MySQL y los consume la API.

---

## Equipo

| Rol | Nombre |
|---|---|
| Investigador | Diego Andrés De Jesús Montenegro |
| Investigador | Luis David Andrade Díaz |
| Tutor | Ing. Francisco Javier Obando |

---

## Stack tecnológico

| Capa | Herramienta | Dónde corre |
|---|---|---|
| Contenedorización | Docker + Docker Compose | Host |
| Base de datos | MySQL 8.0 | Contenedor `construnorte_mysql` |
| Admin BD (web) | Adminer | Contenedor `construnorte_adminer` |
| Análisis y modelado | Jupyter Lab + Python 3.11 | Contenedor `construnorte_jupyter` |
| ETL visual (ingesta inicial) | Apache Hop | Nativo en Mac |
| Modelos ML | LightGBM, XGBoost, Prophet | Contenedor Jupyter |
| API REST + Dashboard web | FastAPI + HTML/CSS/JS | Nativo (`.venv`) |
| Dashboard analítico | Tableau Desktop | Nativo en Mac |
| Control de versiones | Git + GitHub | Host |

---

## Instalación y arranque

### Requisitos previos

- macOS, Linux o Windows con WSL2.
- **Docker Desktop** instalado y corriendo.
- **Git** instalado.
- Python 3.11 disponible en el host (para la API REST).
- (Opcional) Apache Hop y Tableau Desktop para reproducir ETL visual y dashboard.

### Paso 1 — Clonar el repositorio

```bash
git clone https://github.com/diegodejesusdev/DataScienceProject.git
cd DataScienceProject
```

### Paso 2 — Configurar variables de entorno

```bash
cp .env.example .env
```

Edita `.env` y reemplaza los valores `cambiar_*` por contraseñas reales.

### Paso 3 — Levantar el ambiente de análisis

```bash
docker compose up -d --build
```

La primera vez tarda 3–5 minutos (construye la imagen de Jupyter con todas las librerías).

### Paso 4 — Verificar

```bash
docker compose ps
```

Los tres servicios deben aparecer como `running` o `healthy`.

### Paso 5 — Acceder a las herramientas

| Herramienta | URL |
|---|---|
| Jupyter Lab | `http://localhost:8888/?token=<JUPYTER_TOKEN>` |
| Adminer (BD) | `http://localhost:8080` — servidor: `mysql` (no `localhost`) |

### Paso 6 — Levantar la API REST y el dashboard web

```bash
# Instalar dependencias (solo la primera vez)
.venv/bin/pip install -r requirements_api.txt

# Iniciar servidor
.venv/bin/uvicorn api.main:app --reload --port 8000
```

| Recurso | URL |
|---|---|
| Dashboard web | `http://localhost:8000/` |
| Swagger UI | `http://localhost:8000/docs` |
| ReDoc | `http://localhost:8000/redoc` |

---

## Estructura del proyecto

```
DataScienceProject/
├── CLAUDE.md                       # Instrucciones para Claude Code
├── README.md                       # Este archivo
├── docker-compose.yml              # Orquestación Docker (MySQL + Adminer + Jupyter)
├── .env.example                    # Plantilla de variables (sin secretos)
├── .gitignore
├── requirements_api.txt            # Dependencias de la API REST
├── docker/
│   └── jupyter/
│       ├── Dockerfile              # Imagen custom de Jupyter
│       └── requirements.txt        # Librerías Python del contenedor
├── db/
│   └── init/
│       └── 01_schema.sql           # Schema MySQL autoejecutado al levantar
├── data/
│   ├── raw/                        # CSV original (gitignored)
│   └── processed/                  # Datasets intermedios y modelos (gitignored)
├── notebooks/                      # Flujo CRISP-DM completo
│   ├── 01_perfil_inicial.ipynb     # Comprensión inicial del dataset
│   ├── 02_eda.ipynb                # Análisis exploratorio de datos
│   ├── 03_preparacion.ipynb        # Limpieza, ETL y feature engineering
│   ├── 04_abc_xyz.ipynb            # Clasificación ABC/XYZ de SKUs
│   ├── 05_baseline.ipynb           # Modelo baseline (media móvil 4 semanas)
│   ├── 06_lightgbm.ipynb           # Modelo LightGBM
│   ├── 07_xgboost.ipynb            # Modelo XGBoost
│   ├── 08_prophet.ipynb            # Modelo Prophet (top SKUs)
│   └── 09_evaluacion_final.ipynb   # Comparación y evaluación final
├── src/                            # Módulos Python reutilizables
│   ├── db.py                       # Conexión SQLAlchemy a MySQL
│   ├── etl.py                      # Pipeline ETL programático
│   ├── features.py                 # Feature engineering (lags, calendario)
│   ├── abc_xyz.py                  # Clasificación ABC/XYZ
│   ├── models.py                   # Entrenamiento de modelos
│   └── evaluation.py               # Métricas MAE/RMSE/MAPE/sMAPE
├── api/                            # API REST + dashboard web
│   ├── main.py                     # FastAPI app (routers + static)
│   ├── config.py                   # Variables de entorno
│   ├── database.py                 # Engine SQLAlchemy + helper query()
│   ├── schemas.py                  # Modelos Pydantic v2 de respuesta
│   ├── routers/
│   │   ├── pronosticos.py          # /api/pronosticos/*
│   │   ├── clasificacion.py        # /api/clasificacion/*
│   │   ├── metricas.py             # /api/metricas/*
│   │   ├── insights.py             # /api/insights/*
│   │   └── descriptivo.py          # /api/descriptivo/*
│   └── static/                     # Frontend (HTML + CSS + JS)
│       ├── index.html
│       ├── app.js
│       ├── styles.css
│       └── colors.js
├── hop/
│   └── ingesta_csv.hpl             # Flujo de ingesta CSV → MySQL (Apache Hop)
├── reports/                        # Excel y figuras generados por los notebooks (no versionados)
└── docs/                           # Documentación técnica y de diseño
```

---

## Flujo CRISP-DM implementado

| Fase | Notebooks | Resultado en MySQL |
|---|---|---|
| **1. Comprensión** | `01_perfil_inicial`, `02_eda` | — |
| **2. Preparación** | `03_preparacion`, `04_abc_xyz` | `ventas_semanales`, `clasificacion_abc_xyz` |
| **3. Modelado** | `05_baseline`, `06_lightgbm`, `07_xgboost`, `08_prophet` | `pronosticos` |
| **4. Evaluación** | `09_evaluacion_final` | `metricas_modelos` |

---

## API REST — Endpoints principales

14 endpoints `GET`, agrupados en 5 routers:

| Grupo | Endpoints | Descripción |
|---|---|---|
| Pronósticos | `/api/pronosticos/top`, `/sku/{item}`, `/por-centro` | Predicciones semanales por SKU y por centro |
| Clasificación | `/api/clasificacion/resumen` | Resumen de la matriz ABC/XYZ |
| Métricas | `/api/metricas/comparacion` | MAE, RMSE, MAPE y sMAPE por modelo |
| Insights | `/api/insights/crecimiento`, `/alertas` | Crecimiento proyectado y alertas de cambio en la demanda |
| Descriptivo | `/api/descriptivo/lineas-top`, `/pareto`, `/diamantes`, `/estacionalidad`, `/ventas-por-centro`, `/lineas-por-centro`, `/top-skus-por-centro` | Series históricas, Pareto, estacionalidad y ventas por centro |

La raíz `/` sirve el dashboard web (HTML + CSS + JS) que consume estos endpoints.

Documentación interactiva completa en `http://localhost:8000/docs`.

---

## Comandos útiles

```bash
# Levantar todo el ambiente Docker
docker compose up -d

# Apagar (mantiene datos)
docker compose down

# Apagar y BORRAR la base de datos
docker compose down -v

# Ver logs
docker compose logs -f mysql
docker compose logs -f jupyter

# Reconstruir Jupyter tras cambiar requirements.txt
docker compose build jupyter && docker compose up -d jupyter

# Entrar a MySQL por consola
docker exec -it construnorte_mysql mysql -u construnorte_user -p construnorte

# Backup de la base
docker exec construnorte_mysql mysqldump -u root -p construnorte > backup.sql
```

---

## Privacidad y datos personales

El dataset contiene información protegida por la **Ley 1581 de 2012** de Colombia:

- Las columnas personales (`Cliente`, `Nombre Cliente`, `Cedula Vendedor`, etc.) se eliminan en la primera fase del ETL, antes de almacenar datos en MySQL.
- El repositorio público **no contiene** el dataset original ni datos personales.
- El equipo cuenta con carta de autorización firmada por CONSTRUNORTE COMERCIALIZADORA S.A.S.

---

## Licencia

Proyecto académico — uso restringido. © 2026 Unicomfacauca.
