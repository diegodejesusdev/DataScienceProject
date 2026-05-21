"""Router /api/insights — crecimiento proyectado y alertas de cambio."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
from fastapi import APIRouter, HTTPException

from api.database import query
from api.schemas import (
    Alerta,
    AlertasResponse,
    FiltrosAplicados,
    InsightCrecimientoItem,
    InsightCrecimientoResponse,
    ResumenSeveridad,
)

router = APIRouter()

CAP_PCT = 500.0  # Máximo porcentaje reportado; por encima se marca como extremo


def _validar_fecha(fecha: str) -> None:
    try:
        datetime.strptime(fecha, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            400,
            detail={"code": "FECHA_INVALIDA", "message": f"Fecha '{fecha}' no válida. Use YYYY-MM-DD."},
        )


def _tipo_cambio(pct: float) -> str:
    if pct > 50:
        return "crecimiento_alto"
    elif pct >= 10:
        return "crecimiento_moderado"
    elif pct >= -10:
        return "estable"
    elif pct >= -50:
        return "decrecimiento_moderado"
    return "decrecimiento_alto"


def _severidad(abs_pct: float) -> str:
    """Severidad basada en el porcentaje real (sin cap)."""
    if abs_pct > 200:
        return "alta"
    elif abs_pct > 100:
        return "media"
    return "baja"


def _accion(tipo_alerta: str) -> str:
    if tipo_alerta == "pico_proyectado":
        return "Revisar disponibilidad de stock; coordinar con proveedor."
    return "Verificar causas de baja demanda; revisar inventario actual."


def _cargar_base(fecha_objetivo: str) -> pd.DataFrame:
    """Carga predicciones de la semana objetivo vs promedio de las 4 previas."""

    actual_df = query(
        """
        SELECT p.item,
               p.centro_operacion,
               p.cantidad_predicha             AS pred_actual,
               COALESCE(d.nombre_item, p.item) AS nombre_item,
               d.nombre_linea_n1               AS linea,
               c.clase_abc
        FROM pronosticos p
        LEFT JOIN dim_producto          d ON p.item = d.item
        LEFT JOIN clasificacion_abc_xyz c ON p.item = c.item
        WHERE p.fecha_inicio_semana = :fecha
          AND p.modelo              = 'lightgbm'
        """,
        {"fecha": fecha_objetivo},
    )

    if actual_df.empty:
        return pd.DataFrame()

    previas_df = query(
        """
        SELECT item, centro_operacion, AVG(cantidad_predicha) AS avg_4
        FROM pronosticos
        WHERE fecha_inicio_semana <  :fecha
          AND fecha_inicio_semana >= DATE_SUB(:fecha, INTERVAL 28 DAY)
          AND modelo               = 'lightgbm'
        GROUP BY item, centro_operacion
        """,
        {"fecha": fecha_objetivo},
    )

    if previas_df.empty:
        return pd.DataFrame()

    df = actual_df.merge(previas_df, on=["item", "centro_operacion"], how="inner")
    df = df[df["avg_4"] > 0]
    df["crecimiento_unidades"] = df["pred_actual"] - df["avg_4"]
    df["crecimiento_pct_real"] = (df["crecimiento_unidades"] / df["avg_4"]) * 100
    return df


def _aplicar_filtros(
    df: pd.DataFrame,
    min_cantidad: float,
    min_promedio: float,
    solo_clase_ab: bool,
) -> pd.DataFrame:
    """Aplica los filtros de relevancia operativa."""
    df = df[df["pred_actual"] >= min_cantidad]
    df = df[df["avg_4"] >= min_promedio]
    if solo_clase_ab:
        df = df[df["clase_abc"].isin(["A", "B"])]
    return df


# ── GET /api/insights/crecimiento ─────────────────────────────────────────────

@router.get(
    "/crecimiento",
    response_model=InsightCrecimientoResponse,
    summary="SKUs con mayor crecimiento proyectado",
    description=(
        "Compara la predicción de la semana objetivo contra el promedio de las 4 semanas "
        "previas. Aplica filtros de relevancia operativa por defecto: excluye SKUs con "
        "bajo volumen histórico (avg_4 < min_promedio_historico) y capea el porcentaje "
        "reportado a 500% para evitar números no accionables."
    ),
    tags=["Insights"],
)
def get_crecimiento(
    fecha_objetivo: str = "2026-01-05",
    min_cantidad: float = 50,
    min_promedio_historico: float = 10,
    solo_clase_ab: bool = False,
    limit: int = 15,
) -> InsightCrecimientoResponse:
    _validar_fecha(fecha_objetivo)
    limit = max(1, min(limit, 100))

    filtros = FiltrosAplicados(
        min_cantidad_prediccion=min_cantidad,
        min_promedio_historico=min_promedio_historico,
        cap_crecimiento_pct=CAP_PCT,
        solo_clase_ab=solo_clase_ab,
    )

    df = _cargar_base(fecha_objetivo)
    if df.empty:
        return InsightCrecimientoResponse(
            fecha_objetivo=fecha_objetivo,
            filtros_aplicados=filtros,
            items=[],
        )

    df = _aplicar_filtros(df, min_cantidad, min_promedio_historico, solo_clase_ab)
    if df.empty:
        return InsightCrecimientoResponse(
            fecha_objetivo=fecha_objetivo,
            filtros_aplicados=filtros,
            items=[],
        )

    df = df.sort_values("crecimiento_pct_real", ascending=False).head(limit)

    items = []
    for row in df.itertuples(index=False):
        pct_real = float(row.crecimiento_pct_real)
        extremo = abs(pct_real) > CAP_PCT
        pct_reportado = max(-CAP_PCT, min(CAP_PCT, pct_real))

        items.append(
            InsightCrecimientoItem(
                item=str(row.item),
                nombre_item=str(row.nombre_item),
                linea=str(row.linea) if row.linea else None,
                centro_operacion=str(row.centro_operacion),
                prediccion_proxima_semana=round(float(row.pred_actual), 2),
                promedio_4_semanas_previas=round(float(row.avg_4), 2),
                crecimiento_unidades=round(float(row.crecimiento_unidades), 2),
                crecimiento_pct=round(pct_reportado, 2),
                crecimiento_extremo=extremo,
                clase_abc=str(row.clase_abc) if row.clase_abc else None,
                tipo_cambio=_tipo_cambio(pct_reportado),
            )
        )

    return InsightCrecimientoResponse(
        fecha_objetivo=fecha_objetivo,
        filtros_aplicados=filtros,
        items=items,
    )


# ── GET /api/insights/alertas ─────────────────────────────────────────────────

@router.get(
    "/alertas",
    response_model=AlertasResponse,
    summary="Alertas de cambios drásticos en la demanda proyectada",
    description=(
        "Identifica SKUs donde el modelo proyecta cambios que superan el umbral. "
        "Excluye por defecto SKUs con bajo volumen histórico (min_promedio_historico=10) "
        "para evitar alertas falsas por productos casi sin movimiento."
    ),
    tags=["Insights"],
)
def get_alertas(
    fecha_objetivo: str = "2026-01-05",
    umbral_cambio_pct: float = 100.0,
    min_promedio_historico: float = 10.0,
    solo_clase_a: bool = False,
    solo_clase_ab: bool = False,
) -> AlertasResponse:
    _validar_fecha(fecha_objetivo)
    umbral_cambio_pct = max(10.0, umbral_cambio_pct)

    filtros = FiltrosAplicados(
        min_cantidad_prediccion=0,
        min_promedio_historico=min_promedio_historico,
        cap_crecimiento_pct=CAP_PCT,
        solo_clase_ab=solo_clase_ab or solo_clase_a,
    )

    df = _cargar_base(fecha_objetivo)
    if df.empty:
        return AlertasResponse(
            fecha_objetivo=fecha_objetivo,
            umbral=umbral_cambio_pct,
            filtros_aplicados=filtros,
            alertas=[],
            total_alertas=0,
            resumen_severidad=ResumenSeveridad(alta=0, media=0, baja=0),
        )

    # Filtros de relevancia
    df = df[df["avg_4"] >= min_promedio_historico]
    if solo_clase_a:
        df = df[df["clase_abc"] == "A"]
    elif solo_clase_ab:
        df = df[df["clase_abc"].isin(["A", "B"])]

    # Filtrar por umbral (usando pct real para no perder alertas por el cap)
    df = df[df["crecimiento_pct_real"].abs() >= umbral_cambio_pct]

    if df.empty:
        return AlertasResponse(
            fecha_objetivo=fecha_objetivo,
            umbral=umbral_cambio_pct,
            filtros_aplicados=filtros,
            alertas=[],
            total_alertas=0,
            resumen_severidad=ResumenSeveridad(alta=0, media=0, baja=0),
        )

    df = df.sort_values("crecimiento_pct_real", ascending=False)

    alertas: list[Alerta] = []
    conteo_severidad = {"alta": 0, "media": 0, "baja": 0}

    for row in df.itertuples(index=False):
        pct_real = float(row.crecimiento_pct_real)
        abs_pct = abs(pct_real)
        tipo = "pico_proyectado" if pct_real > 0 else "caida_proyectada"
        sev = _severidad(abs_pct)
        conteo_severidad[sev] += 1

        # Porcentaje legible para el mensaje (cap para no asustar)
        pct_display = min(abs_pct, CAP_PCT)
        sufijo = "+" if abs_pct > CAP_PCT else ""
        if pct_real > 0:
            mensaje = f"Se proyecta un crecimiento del {pct_display:.0f}%{sufijo} vs promedio reciente."
        else:
            mensaje = f"Se proyecta una caída del {pct_display:.0f}%{sufijo} vs promedio reciente."

        alertas.append(
            Alerta(
                item=str(row.item),
                nombre_item=str(row.nombre_item),
                centro_operacion=str(row.centro_operacion),
                clase_abc=str(row.clase_abc) if row.clase_abc else None,
                tipo_alerta=tipo,
                severidad=sev,
                mensaje=mensaje,
                prediccion_actual=round(float(row.pred_actual), 2),
                promedio_historico=round(float(row.avg_4), 2),
                crecimiento_pct_real=round(pct_real, 2),
                accion_sugerida=_accion(tipo),
            )
        )

    return AlertasResponse(
        fecha_objetivo=fecha_objetivo,
        umbral=umbral_cambio_pct,
        filtros_aplicados=filtros,
        alertas=alertas,
        total_alertas=len(alertas),
        resumen_severidad=ResumenSeveridad(**conteo_severidad),
    )
