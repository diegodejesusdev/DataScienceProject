# 08 — Diseño de la API REST

**Documento técnico para la implementación de la API del proyecto ConstruNorte.**

**Audiencia:** Claude Code, equipo del proyecto.
**Versión:** 1.0 — mayo 2026.
**Autores:** Diego Andrés De Jesús Montenegro y Luis David Andrade Díaz.

---

## 1. Propósito

Construir una API REST sencilla que exponga los resultados del trabajo analítico (notebooks 01-09) a través de endpoints HTTP, para uso durante la sustentación del proyecto y como entregable funcional para ConstruNorte.

**No es objetivo:**
- No es un sistema de producción.
- No requiere autenticación, autorización ni control de usuarios.
- No requiere caché distribuido ni alta concurrencia.
- No requiere despliegue en la nube (corre localmente).

**Sí es objetivo:**
- API REST con endpoints documentados (Swagger UI nativo de FastAPI).
- Conexión a la base MySQL existente del proyecto.
- Lectura únicamente (no se escribe en MySQL desde la API).
- Frontend mini de una sola página que consume la API.

---

## 2. Stack técnico

| Componente | Tecnología | Razón |
|---|---|---|
| Backend | **FastAPI** | Velocidad de desarrollo, Swagger UI automático, type hints nativos |
| ORM/DB | **SQLAlchemy + PyMySQL** | Ya se usan en `src/db.py` del proyecto |
| Servidor | **Uvicorn** | Recomendado por FastAPI, ASGI |
| Validación | **Pydantic v2** | Schemas tipados, integrado con FastAPI |
| Frontend | **HTML + Tailwind CSS (CDN) + Alpine.js (CDN)** | Sin build tools, ligero, profesional |
| Visualización | **Chart.js (CDN)** | Gráficos interactivos sencillos |

Toda dependencia debe ser instalable vía `pip` en el `.venv` existente del proyecto.

---

## 3. Estructura de archivos

```
DataScienceProject/
├── api/                          # ← NUEVO directorio
│   ├── __init__.py
│   ├── main.py                   # FastAPI app + CORS + montaje de routers
│   ├── config.py                 # Configuración (lee .env)
│   ├── database.py               # Engine SQLAlchemy reusable
│   ├── schemas.py                # Pydantic models para responses
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── pronosticos.py        # /api/pronosticos/*
│   │   ├── clasificacion.py      # /api/clasificacion/*
│   │   ├── metricas.py           # /api/metricas/*
│   │   └── insights.py           # /api/insights/*
│   └── static/                   # Frontend
│       ├── index.html
│       ├── styles.css            # (opcional, mayoría con Tailwind)
│       └── app.js
├── requirements_api.txt          # ← NUEVO, deps adicionales
└── (resto del repo intacto)
```

**Reglas:**
- No modificar archivos existentes del repo (etl.py, models.py, db.py, notebooks).
- Reutilizar `.env` y `src/db.py` para conexión a MySQL.
- Toda configuración de URLs y credenciales debe venir de `.env` (no hardcoded).

---

## 4. Endpoints — Especificación detallada

### 4.1 `GET /api/pronosticos/top`

**Propósito:** Top N SKUs pronosticados para una semana específica.

**Query parameters:**
| Parámetro | Tipo | Default | Descripción |
|---|---|---|---|
| `fecha` | str (YYYY-MM-DD) | `2026-01-05` | Fecha de inicio de la semana ISO |
| `centro` | str | `null` (todos) | Filtrar por centro: "001", "002", "003" |
| `modelo` | str | `"lightgbm"` | Modelo a consultar |
| `limit` | int | 20 | Número de SKUs a retornar |

**Response shape:**
```json
{
  "fecha_semana": "2026-01-05",
  "modelo": "lightgbm",
  "centro_filtro": null,
  "total": 20,
  "items": [
    {
      "item": "000041",
      "nombre_item": "CEMENTO GRIS *50 KL T1 ARGOS",
      "linea": "CEMENTOS",
      "centro_operacion": "001",
      "cantidad_pronosticada": 3250.5,
      "cantidad_real": 3180.0,
      "clase_abc": "A",
      "segmento_abc_xyz": "AX",
      "error_absoluto": 70.5
    }
  ]
}
```

**Comportamiento:**
- Si `cantidad_real` no existe (predicción futura), retornar `null`.
- Si no hay datos para la fecha, retornar `items: []` con `total: 0`.

---

### 4.2 `GET /api/pronosticos/sku/{item}`

**Propósito:** Serie histórica + predicciones de un SKU específico para visualización.

**Path parameters:**
- `item` (str, obligatorio): código del SKU.

**Query parameters:**
| Parámetro | Tipo | Default | Descripción |
|---|---|---|---|
| `centro` | str | `null` (agrega los 3) | Filtrar por centro |
| `modelo` | str | `"lightgbm"` | Modelo principal a graficar |
| `incluir_baseline` | bool | `true` | Incluir predicciones del baseline |
| `desde` | str | `2024-01-01` | Fecha desde |
| `hasta` | str | `2026-03-31` | Fecha hasta |

**Response shape:**
```json
{
  "item": "000041",
  "nombre_item": "CEMENTO GRIS *50 KL T1 ARGOS",
  "linea": "CEMENTOS",
  "clase_abc": "A",
  "segmento_abc_xyz": "AX",
  "centro": null,
  "serie": [
    {
      "fecha": "2024-01-01",
      "cantidad_real": 150.0,
      "cantidad_predicha_lightgbm": null,
      "cantidad_predicha_baseline": null,
      "split": "train"
    },
    {
      "fecha": "2025-10-06",
      "cantidad_real": 200.0,
      "cantidad_predicha_lightgbm": 195.5,
      "cantidad_predicha_baseline": 180.0,
      "split": "valid"
    }
  ]
}
```

**Comportamiento:**
- Si `centro` es `null`, agregar los 3 centros sumando cantidades.
- Si `incluir_baseline` es `false`, omitir esa columna.
- Validar que el SKU exista en `dim_producto`; si no, retornar 404.

---

### 4.3 `GET /api/metricas/comparacion`

**Propósito:** Tabla comparativa de los 4 modelos (lo que mostraste en el notebook 09).

**Query parameters:**
| Parámetro | Tipo | Default | Descripción |
|---|---|---|---|
| `split` | str | `"test_2026"` | "valid" o "test_2026" |
| `segmento` | str | `"global"` | "global", "abc_A", "abc_B", "abc_C", "top50_clase_A" |

**Response shape:**
```json
{
  "split": "test_2026",
  "segmento": "global",
  "modelos": [
    {
      "modelo": "baseline_ma4",
      "nombre_amigable": "Baseline (MA-4)",
      "mae": 32.50,
      "rmse": 389.01,
      "mape": 170.62,
      "smape": 147.72,
      "n_obs": 66572,
      "mejora_vs_baseline_pct": null
    },
    {
      "modelo": "lightgbm",
      "nombre_amigable": "LightGBM",
      "mae": 6.77,
      "rmse": 144.97,
      "mape": 28.76,
      "smape": 142.46,
      "n_obs": 66572,
      "mejora_vs_baseline_pct": 79.18
    }
  ],
  "modelo_recomendado": "lightgbm"
}
```

**Comportamiento:**
- Calcular `mejora_vs_baseline_pct` para todos los modelos excepto el baseline.
- Si un modelo no tiene datos para ese segmento (ej: prophet no aplica en `abc_C`), omitirlo del array.

---

### 4.4 `GET /api/clasificacion/resumen`

**Propósito:** Matriz ABC × XYZ con KPIs descriptivos.

**Sin parámetros.**

**Response shape:**
```json
{
  "total_skus_activos": 2310,
  "valor_total_periodo": 101437328945.50,
  "distribucion_abc": {
    "A": {"num_skus": 97, "porcentaje_skus": 4.20, "valor_total": 80450123.0, "porcentaje_valor": 79.32},
    "B": {"num_skus": 365, "porcentaje_skus": 15.80, "valor_total": 15240567.0, "porcentaje_valor": 15.03},
    "C": {"num_skus": 1918, "porcentaje_skus": 83.03, "valor_total": 5746638.0, "porcentaje_valor": 5.66}
  },
  "matriz_segmentos": [
    {"clase_abc": "A", "clase_xyz": "X", "num_skus": 4, "valor_total": 30197000000},
    {"clase_abc": "A", "clase_xyz": "Y", "num_skus": 47, "valor_total": 52802000000},
    {"clase_abc": "A", "clase_xyz": "Z", "num_skus": 46, "valor_total": 17916000000}
  ],
  "skus_estrella": {
    "definicion": "Top 5 SKUs por valor con clase A y XYZ X/Y",
    "items": [
      {"item": "000041", "nombre": "CEMENTO GRIS...", "valor_total": 28196379716}
    ]
  }
}
```

---

### 4.5 `GET /api/insights/crecimiento`

**Propósito:** SKUs con mayor crecimiento proyectado (semana próxima vs promedio últimas 4 semanas).

**Query parameters:**
| Parámetro | Tipo | Default | Descripción |
|---|---|---|---|
| `fecha_objetivo` | str | `"2026-01-05"` | Semana a evaluar |
| `min_cantidad` | float | 50 | Predicción mínima (unidades) |
| `min_promedio_historico` | float | **50** | Promedio histórico mínimo — elimina SKUs intermitentes |
| `solo_clase_ab` | bool | `false` | Filtrar solo clases A y B |
| `limit` | int | 15 | Top N a retornar |

**Filtros de relevancia operativa (defaults):**
- `pred_actual >= 50 unidades` — excluye predicciones de bajo volumen
- `avg_4 >= 50 unidades` — excluye SKUs con promedio histórico insignificante
- Cap visual de **1.000%** — porcentajes mayores se reportan como `crecimiento_extremo: true`; el valor real siempre está en `crecimiento_pct_real`

**Response shape:**
```json
{
  "fecha_objetivo": "2026-01-05",
  "filtros_aplicados": {
    "min_cantidad_prediccion": 50,
    "min_promedio_historico": 50,
    "cap_crecimiento_pct": 1000,
    "solo_clase_ab": false
  },
  "items": [
    {
      "item": "000XXX",
      "nombre_item": "UNION PVC PRES 3/4",
      "linea": "TUBERIA",
      "centro_operacion": "001",
      "prediccion_proxima_semana": 748.0,
      "promedio_4_semanas_previas": 20.0,
      "crecimiento_unidades": 728.0,
      "crecimiento_pct": 1000.0,
      "crecimiento_pct_real": 3640.0,
      "crecimiento_extremo": true,
      "clase_abc": "B",
      "tipo_cambio": "crecimiento_alto"
    }
  ]
}
```

**Comportamiento:**
- Ordenado por `crecimiento_pct_real` descendente (valor real sin cap).
- `crecimiento_pct`: valor capeado al máximo visual (1.000%) — para mostrar en barras/gráficos.
- `crecimiento_pct_real`: valor real calculado — puede superar el cap.
- `crecimiento_extremo: true` cuando el valor real supera el cap visual.
- `tipo_cambio`: `"crecimiento_alto"` (>50%), `"crecimiento_moderado"` (10–50%), `"estable"` (<10%), `"decrecimiento_moderado"`, `"decrecimiento_alto"` — basado en el valor real.

---

### 4.6 `GET /api/pronosticos/por-centro`

**Propósito:** Predicciones agregadas por centro de operación.

**Query parameters:**
| Parámetro | Tipo | Default | Descripción |
|---|---|---|---|
| `fecha` | str | `"2026-01-05"` | Semana objetivo |
| `modelo` | str | `"lightgbm"` | Modelo |

**Response shape:**
```json
{
  "fecha_semana": "2026-01-05",
  "modelo": "lightgbm",
  "centros": [
    {
      "centro_operacion": "001",
      "total_pronosticado": 45230.5,
      "total_real": 44120.0,
      "num_skus_distintos": 1850,
      "top_skus": [
        {"item": "000041", "nombre": "CEMENTO...", "cantidad": 3250},
        {"item": "000291", "nombre": "VARILLA...", "cantidad": 1890}
      ]
    },
    {
      "centro_operacion": "002",
      "total_pronosticado": 32100.0,
      "total_real": null,
      "num_skus_distintos": 1620,
      "top_skus": [...]
    }
  ]
}
```

---

### 4.7 `GET /api/insights/alertas`

**Propósito:** SKUs donde el modelo proyecta cambios drásticos que requieren atención.

**Query parameters:**
| Parámetro | Tipo | Default | Descripción |
|---|---|---|---|
| `fecha_objetivo` | str | `"2026-01-05"` | Semana evaluada |
| `umbral_cambio_pct` | float | 100 | Umbral de cambio (%) para activar alerta (mín. 10) |
| `min_promedio_historico` | float | **50** | Promedio histórico mínimo — evita falsas alarmas |
| `solo_clase_ab` | bool | `false` | Limitar a SKUs clase A y B |
| `solo_clase_a` | bool | `false` | Limitar solo a SKUs clase A |

**Filtros de relevancia operativa:**
- `avg_4 >= 50 unidades` (default) — excluye SKUs casi sin movimiento
- Cap visual **1.000%** en el campo `mensaje`; el valor real siempre está en `crecimiento_pct_real`

**Severidad** (basada en porcentaje real):
- `alta`: cambio > 200%
- `media`: cambio 100–200%
- `baja`: cambio < 100%

**Response shape:**
```json
{
  "fecha_objetivo": "2026-01-05",
  "umbral": 100,
  "filtros_aplicados": {
    "min_cantidad_prediccion": 0,
    "min_promedio_historico": 50,
    "cap_crecimiento_pct": 1000,
    "solo_clase_ab": false
  },
  "alertas": [
    {
      "item": "000XXX",
      "nombre_item": "PRODUCTO X",
      "centro_operacion": "001",
      "clase_abc": "A",
      "tipo_alerta": "pico_proyectado",
      "severidad": "alta",
      "mensaje": "Se proyecta un crecimiento del 250% vs promedio reciente.",
      "prediccion_actual": 5000.0,
      "promedio_historico": 1400.0,
      "crecimiento_pct_real": 257.14,
      "accion_sugerida": "Revisar disponibilidad de stock; coordinar con proveedor."
    }
  ],
  "total_alertas": 12,
  "resumen_severidad": { "alta": 3, "media": 5, "baja": 4 }
}
```

**Tipos de alerta:**
- `pico_proyectado`: crecimiento real > umbral.
- `caida_proyectada`: decrecimiento real > umbral (en valor absoluto).

---

## 5. Manejo de errores

Toda respuesta de error debe seguir este formato:

```json
{
  "error": {
    "code": "SKU_NOT_FOUND",
    "message": "El SKU '999999' no existe en la base de datos",
    "details": null
  }
}
```

Códigos HTTP estándar:
- `400` — Parámetros inválidos (fecha mal formada, modelo desconocido).
- `404` — SKU/recurso no encontrado.
- `500` — Error interno (conexión a DB, etc.).

---

## 6. Conexión a base de datos

- Reutilizar el patrón de `src/db.py` existente.
- Credenciales desde `.env` (NUNCA hardcoded).
- Pool de conexiones SQLAlchemy con `pool_pre_ping=True`.
- Todas las queries son **SELECT** únicamente (la API es read-only).

---

## 7. Documentación automática

FastAPI genera documentación interactiva automáticamente:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

Cada endpoint debe tener:
- Descripción clara en `summary` y `description`.
- Ejemplos de response en los Pydantic models.
- Tags para agrupar endpoints en la UI de Swagger.

---

## 8. CORS

Habilitar CORS para permitir que el frontend local consulte la API:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Solo en desarrollo
    allow_methods=["GET"],
    allow_headers=["*"],
)
```

---

## 9. Ejecución

```bash
# Instalar dependencias
.venv/bin/pip install -r requirements_api.txt

# Levantar servidor
.venv/bin/uvicorn api.main:app --reload --port 8000

# Acceder:
#   http://localhost:8000/         → Frontend
#   http://localhost:8000/docs     → Swagger UI
#   http://localhost:8000/api/...  → Endpoints
```

---

## 10. Testing

No se requieren tests automatizados (proyecto académico, alcance acotado). Pero **sí** debe haber un archivo `api/test_manual.md` con ejemplos de curl para validar cada endpoint:

```bash
# Ejemplo:
curl "http://localhost:8000/api/pronosticos/top?fecha=2026-01-05&limit=10"
curl "http://localhost:8000/api/pronosticos/sku/000041"
curl "http://localhost:8000/api/metricas/comparacion?split=test_2026"
```

---

## 11. Criterios de aceptación

La API se considera completa cuando:

- [ ] Los 7 endpoints responden correctamente.
- [ ] Swagger UI muestra todos los endpoints con ejemplos.
- [ ] El frontend mini consume todos los endpoints.
- [ ] No hay credenciales hardcoded.
- [ ] Manejo de errores funcional (404 para SKU inexistente, etc.).
- [ ] README de instalación y ejecución en `api/README.md`.
- [ ] El servidor levanta sin errores con `uvicorn api.main:app`.
