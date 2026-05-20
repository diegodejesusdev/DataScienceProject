"""Router /api/insights — crecimiento proyectado y alertas de cambio."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
from fastapi import APIRouter, HTTPException

from api.database import query
from api.schemas import (
    Alerta,
    AlertasResponse,
    InsightCrecimientoItem,
    InsightCrecimientoResponse,
    ResumenSeveridad,
)

router = APIRouter()


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
    if abs_pct > 200:
        return "alta"
    elif abs_pct > 100:
        return "media"
    return "baja"


def _accion(tipo_alerta: str) -> str:
    if tipo_alerta == "pico_proyectado":
        return "Revisar disponibilidad de stock; coordinar con proveedor."
    return "Verificar causas de baja demanda; revisar inventario actual."


def _cargar_crecimiento(fecha_objetivo: str) -> pd.DataFrame:
    """Carga predicciones de la semana objetivo y promedio de las 4 previas."""

    actual_df = query(
        """
        SELECT p.item,
               p.centro_operacion,
               p.cantidad_predicha           AS pred_actual,
               COALESCE(d.nombre_item, p.item) AS nombre_item,
               d.nombre_linea_n1              AS linea,
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
    df = df[df["avg_4"] > 0]  # Evitar división por cero
    df["crecimiento_unidades"] = df["pred_actual"] - df["avg_4"]
    df["crecimiento_pct"] = (df["crecimiento_unidades"] / df["avg_4"]) * 100
    return df


# ── GET /api/insights/crecimiento ─────────────────────────────────────────────

@router.get(
    "/crecimiento",
    response_model=InsightCrecimientoResponse,
    summary="SKUs con mayor crecimiento proyectado",
    description=(
        "Compara la predicción de la semana objetivo contra el promedio "
        "de las 4 semanas previas y retorna los N SKUs con mayor variación."
    ),
    tags=["Insights"],
)
def get_crecimiento(
    fecha_objetivo: str = "2026-01-05",
    min_cantidad: float = 50,
    limit: int = 15,
) -> InsightCrecimientoResponse:
    _validar_fecha(fecha_objetivo)
    limit = max(1, min(limit, 100))

    df = _cargar_crecimiento(fecha_objetivo)

    if df.empty:
        return InsightCrecimientoResponse(fecha_objetivo=fecha_objetivo, items=[])

    df = df[df["pred_actual"] >= min_cantidad]
    df = df.sort_values("crecimiento_pct", ascending=False).head(limit)

    items = [
        InsightCrecimientoItem(
            item=str(row.item),
            nombre_item=str(row.nombre_item),
            linea=str(row.linea) if row.linea else None,
            centro_operacion=str(row.centro_operacion),
            prediccion_proxima_semana=round(float(row.pred_actual), 2),
            promedio_4_semanas_previas=round(float(row.avg_4), 2),
            crecimiento_unidades=round(float(row.crecimiento_unidades), 2),
            crecimiento_pct=round(float(row.crecimiento_pct), 2),
            clase_abc=str(row.clase_abc) if row.clase_abc else None,
            tipo_cambio=_tipo_cambio(float(row.crecimiento_pct)),
        )
        for row in df.itertuples(index=False)
    ]

    return InsightCrecimientoResponse(fecha_objetivo=fecha_objetivo, items=items)


# ── GET /api/insights/alertas ─────────────────────────────────────────────────

@router.get(
    "/alertas",
    response_model=AlertasResponse,
    summary="Alertas de cambios drásticos en la demanda proyectada",
    description=(
        "Identifica SKUs donde el modelo proyecta cambios que superan el umbral "
        "indicado respecto al promedio histórico de las 4 semanas previas."
    ),
    tags=["Insights"],
)
def get_alertas(
    fecha_objetivo: str = "2026-01-05",
    umbral_cambio_pct: float = 100.0,
    solo_clase_a: bool = False,
) -> AlertasResponse:
    _validar_fecha(fecha_objetivo)
    umbral_cambio_pct = max(10.0, umbral_cambio_pct)

    df = _cargar_crecimiento(fecha_objetivo)

    if df.empty:
        return AlertasResponse(
            fecha_objetivo=fecha_objetivo,
            umbral=umbral_cambio_pct,
            alertas=[],
            total_alertas=0,
            resumen_severidad=ResumenSeveridad(alta=0, media=0, baja=0),
        )

    # Filtrar por umbral
    df = df[df["crecimiento_pct"].abs() >= umbral_cambio_pct]

    if solo_clase_a:
        df = df[df["clase_abc"] == "A"]

    if df.empty:
        return AlertasResponse(
            fecha_objetivo=fecha_objetivo,
            umbral=umbral_cambio_pct,
            alertas=[],
            total_alertas=0,
            resumen_severidad=ResumenSeveridad(alta=0, media=0, baja=0),
        )

    # Ordenar: picos primero (mayor impacto positivo), luego caídas
    df = df.sort_values("crecimiento_pct", ascending=False)

    alertas: list[Alerta] = []
    conteo_severidad = {"alta": 0, "media": 0, "baja": 0}

    for row in df.itertuples(index=False):
        pct = float(row.crecimiento_pct)
        abs_pct = abs(pct)
        tipo = "pico_proyectado" if pct > 0 else "caida_proyectada"
        sev = _severidad(abs_pct)
        conteo_severidad[sev] += 1

        if pct > 0:
            mensaje = f"Se proyecta un crecimiento del {abs_pct:.0f}% vs promedio reciente."
        else:
            mensaje = f"Se proyecta una caída del {abs_pct:.0f}% vs promedio reciente."

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
                accion_sugerida=_accion(tipo),
            )
        )

    return AlertasResponse(
        fecha_objetivo=fecha_objetivo,
        umbral=umbral_cambio_pct,
        alertas=alertas,
        total_alertas=len(alertas),
        resumen_severidad=ResumenSeveridad(**conteo_severidad),
    )
