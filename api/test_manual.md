# Test manual — ejemplos curl

Servidor corriendo en `http://localhost:8000`.

## 1. Top SKUs pronosticados

```bash
# Top 20 (todos los centros, semana 2026-01-05)
curl "http://localhost:8000/api/pronosticos/top?fecha=2026-01-05&limit=20"

# Top 10, solo centro 001
curl "http://localhost:8000/api/pronosticos/top?fecha=2026-01-05&centro=001&limit=10"

# Con XGBoost
curl "http://localhost:8000/api/pronosticos/top?fecha=2026-01-05&modelo=xgboost&limit=5"
```

## 2. Serie histórica de un SKU

```bash
# SKU 000041 (Cemento Gris), agregado los 3 centros
curl "http://localhost:8000/api/pronosticos/sku/000041"

# Solo centro 001, sin baseline
curl "http://localhost:8000/api/pronosticos/sku/000041?centro=001&incluir_baseline=false"

# SKU inexistente → 404
curl "http://localhost:8000/api/pronosticos/sku/999999"
```

## 3. Pronósticos por centro

```bash
curl "http://localhost:8000/api/pronosticos/por-centro?fecha=2026-01-05"
curl "http://localhost:8000/api/pronosticos/por-centro?fecha=2026-01-05&modelo=xgboost"
```

## 4. Comparación de métricas

```bash
# Global, test 2026
curl "http://localhost:8000/api/metricas/comparacion?split=test_2026&segmento=global"

# Solo clase A
curl "http://localhost:8000/api/metricas/comparacion?split=test_2026&segmento=abc_A"

# Top 50 A (incluye Prophet)
curl "http://localhost:8000/api/metricas/comparacion?split=test_2026&segmento=top50_clase_A"

# Validation
curl "http://localhost:8000/api/metricas/comparacion?split=valid&segmento=global"

# Segmento inválido → 400
curl "http://localhost:8000/api/metricas/comparacion?segmento=invalido"
```

## 5. Clasificación ABC × XYZ

```bash
curl "http://localhost:8000/api/clasificacion/resumen"
```

## 6. Insights — Crecimiento proyectado

```bash
curl "http://localhost:8000/api/insights/crecimiento?fecha_objetivo=2026-01-05&limit=15"

# Filtrar por volumen mínimo mayor (reduce ruido de SKUs casi sin venta)
curl "http://localhost:8000/api/insights/crecimiento?fecha_objetivo=2026-01-05&min_cantidad=500&limit=10"
```

## 7. Insights — Alertas

```bash
# Umbral 100% (SKUs que al menos duplican o reducen a la mitad)
curl "http://localhost:8000/api/insights/alertas?fecha_objetivo=2026-01-05&umbral_cambio_pct=100"

# Solo clase A
curl "http://localhost:8000/api/insights/alertas?fecha_objetivo=2026-01-05&solo_clase_a=true"
```

## Swagger UI

```
http://localhost:8000/docs
```
