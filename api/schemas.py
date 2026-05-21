"""Pydantic v2 models para todos los responses de la API."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


# ── /api/pronosticos/top ──────────────────────────────────────────────────────

class PronosticoItem(BaseModel):
    item: str
    nombre_item: str
    linea: Optional[str] = None
    centro_operacion: str
    cantidad_pronosticada: float
    cantidad_real: Optional[float] = None
    clase_abc: Optional[str] = None
    segmento_abc_xyz: Optional[str] = None
    error_absoluto: Optional[float] = None


class PronosticosTopResponse(BaseModel):
    fecha_semana: str
    modelo: str
    centro_filtro: Optional[str] = None
    total: int
    items: list[PronosticoItem]


# ── /api/pronosticos/sku/{item} ───────────────────────────────────────────────

class SeriePunto(BaseModel):
    fecha: str
    cantidad_real: Optional[float] = None
    cantidad_predicha_principal: Optional[float] = None
    cantidad_predicha_baseline: Optional[float] = None
    split: str


class PronosticoSKUResponse(BaseModel):
    item: str
    nombre_item: str
    linea: Optional[str] = None
    clase_abc: Optional[str] = None
    segmento_abc_xyz: Optional[str] = None
    centro: Optional[str] = None
    modelo_principal: str
    serie: list[SeriePunto]


# ── /api/pronosticos/por-centro ───────────────────────────────────────────────

class TopSKU(BaseModel):
    item: str
    nombre: str
    cantidad: float


class CentroPronostico(BaseModel):
    centro_operacion: str
    total_pronosticado: float
    total_real: Optional[float] = None
    num_skus_distintos: int
    top_skus: list[TopSKU]


class PronosticosPorCentroResponse(BaseModel):
    fecha_semana: str
    modelo: str
    centros: list[CentroPronostico]


# ── /api/metricas/comparacion ─────────────────────────────────────────────────

class MetricasModelo(BaseModel):
    modelo: str
    nombre_amigable: str
    mae: float
    rmse: float
    mape: float
    smape: float
    n_obs: int
    mejora_vs_baseline_pct: Optional[float] = None


class MetricasComparacionResponse(BaseModel):
    split: str
    segmento: str
    modelos: list[MetricasModelo]
    modelo_recomendado: str


# ── /api/clasificacion/resumen ────────────────────────────────────────────────

class DistribucionABCItem(BaseModel):
    num_skus: int
    porcentaje_skus: float
    valor_total: float
    porcentaje_valor: float


class SegmentoMatriz(BaseModel):
    clase_abc: str
    clase_xyz: str
    num_skus: int
    valor_total: float


class SKUEstrella(BaseModel):
    item: str
    nombre: str
    valor_total: float


class SkusEstrella(BaseModel):
    definicion: str
    items: list[SKUEstrella]


class ClasificacionResumenResponse(BaseModel):
    total_skus_activos: int
    valor_total_periodo: float
    distribucion_abc: dict[str, DistribucionABCItem]
    matriz_segmentos: list[SegmentoMatriz]
    skus_estrella: SkusEstrella


# ── /api/insights/crecimiento ─────────────────────────────────────────────────

class FiltrosAplicados(BaseModel):
    min_cantidad_prediccion: float
    min_promedio_historico: float
    cap_crecimiento_pct: float
    solo_clase_ab: bool


class InsightCrecimientoItem(BaseModel):
    item: str
    nombre_item: str
    linea: Optional[str] = None
    centro_operacion: str
    prediccion_proxima_semana: float
    promedio_4_semanas_previas: float
    crecimiento_unidades: float
    crecimiento_pct: float
    crecimiento_extremo: bool
    clase_abc: Optional[str] = None
    tipo_cambio: str


class InsightCrecimientoResponse(BaseModel):
    fecha_objetivo: str
    filtros_aplicados: FiltrosAplicados
    items: list[InsightCrecimientoItem]


# ── /api/insights/alertas ─────────────────────────────────────────────────────

class Alerta(BaseModel):
    item: str
    nombre_item: str
    centro_operacion: str
    clase_abc: Optional[str] = None
    tipo_alerta: str
    severidad: str
    mensaje: str
    prediccion_actual: float
    promedio_historico: float
    crecimiento_pct_real: float
    accion_sugerida: str


class ResumenSeveridad(BaseModel):
    alta: int
    media: int
    baja: int


class AlertasResponse(BaseModel):
    fecha_objetivo: str
    umbral: float
    filtros_aplicados: FiltrosAplicados
    alertas: list[Alerta]
    total_alertas: int
    resumen_severidad: ResumenSeveridad
