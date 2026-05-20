# ConstruNorte API

API REST del sistema de pronóstico de demanda de inventarios.

## Requisitos

- Python 3.11 con `.venv` activo (ya existe en la raíz del proyecto).
- Docker corriendo con el contenedor MySQL (`docker compose up -d`).
- Archivo `.env` en la raíz del proyecto con credenciales de MySQL.

## Instalación

```bash
# Desde la raíz del proyecto
.venv/bin/pip install -r requirements_api.txt
```

## Ejecución

```bash
# Desde la raíz del proyecto
.venv/bin/uvicorn api.main:app --reload --port 8000
```

## URLs

| URL | Descripción |
|---|---|
| `http://localhost:8000/` | Frontend (Fase 3) |
| `http://localhost:8000/docs` | Swagger UI interactivo |
| `http://localhost:8000/redoc` | ReDoc |
| `http://localhost:8000/api/...` | Endpoints REST |

## Estructura

```
api/
├── main.py          # FastAPI app + CORS + routers
├── config.py        # Variables de entorno
├── database.py      # Engine SQLAlchemy + helper query()
├── schemas.py       # Pydantic v2 models de response
├── routers/
│   ├── pronosticos.py   # /api/pronosticos/*
│   ├── clasificacion.py # /api/clasificacion/*
│   ├── metricas.py      # /api/metricas/*
│   └── insights.py      # /api/insights/*
└── static/          # Frontend (HTML/JS/CSS)
```
