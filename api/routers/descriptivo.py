"""Router /api/descriptivo — gráficos descriptivos adicionales."""

from __future__ import annotations

from fastapi import APIRouter

from api.database import query
from api.schemas import (
    DiamantePunto,
    DiamantesResponse,
    EstacionalidadPunto,
    EstacionalidadResponse,
    LineaItem,
    LineasTopResponse,
    ParetoPunto,
    ParetoResponse,
    VentasCentro,
    VentasPorCentroResponse,
)

router = APIRouter()

MESES_ES: dict[str, str] = {
    "January": "Ene", "February": "Feb", "March": "Mar",
    "April": "Abr", "May": "May", "June": "Jun",
    "July": "Jul", "August": "Ago", "September": "Sep",
    "October": "Oct", "November": "Nov", "December": "Dic",
}


@router.get(
    "/lineas-top",
    response_model=LineasTopResponse,
    summary="Top 10 líneas de producto por valor total",
)
def get_lineas_top() -> LineasTopResponse:
    df = query(
        """
        SELECT nombre_linea_n1       AS linea,
               COUNT(*)              AS num_skus,
               SUM(valor_total)      AS valor_total
        FROM clasificacion_abc_xyz
        WHERE nombre_linea_n1 IS NOT NULL AND nombre_linea_n1 != ''
        GROUP BY nombre_linea_n1
        ORDER BY valor_total DESC
        LIMIT 10
        """
    )
    if df.empty:
        return LineasTopResponse(items=[], total_valor=0.0)

    total = float(df["valor_total"].sum())
    items = [
        LineaItem(
            linea=str(row.linea),
            num_skus=int(row.num_skus),
            valor_total=float(row.valor_total or 0),
            pct_valor=round(float(row.valor_total or 0) / total * 100, 2) if total else 0.0,
        )
        for row in df.itertuples(index=False)
    ]
    return LineasTopResponse(items=items, total_valor=round(total, 2))


@router.get(
    "/pareto",
    response_model=ParetoResponse,
    summary="Curva de Pareto: % SKUs vs % valor acumulado",
)
def get_pareto() -> ParetoResponse:
    df = query(
        """
        SELECT valor_total
        FROM clasificacion_abc_xyz
        ORDER BY valor_total DESC
        """
    )
    if df.empty:
        return ParetoResponse(
            total_skus=0, total_valor=0.0, puntos=[],
            corte_80_pct_skus=0.0, corte_80_num_skus=0,
        )

    n = len(df)
    total = float(df["valor_total"].sum())
    valores = df["valor_total"].astype(float).tolist()

    cumulative: list[float] = []
    acum = 0.0
    for v in valores:
        acum += v
        cumulative.append(acum)

    indices = sorted(set([0] + list(range(0, n, 5)) + [n - 1]))

    puntos = [
        ParetoPunto(
            pct_skus=round((i + 1) / n * 100, 2),
            pct_valor_acum=round(cumulative[i] / total * 100, 2) if total else 0.0,
        )
        for i in indices
    ]

    corte_idx = next(
        (i for i, v in enumerate(cumulative) if total > 0 and v / total >= 0.80),
        n - 1,
    )

    return ParetoResponse(
        total_skus=n,
        total_valor=round(total, 2),
        puntos=puntos,
        corte_80_pct_skus=round((corte_idx + 1) / n * 100, 2) if n else 0.0,
        corte_80_num_skus=corte_idx + 1,
    )


@router.get(
    "/diamantes",
    response_model=DiamantesResponse,
    summary="Valor comercial por segmento ABC×XYZ",
)
def get_diamantes() -> DiamantesResponse:
    df = query(
        """
        SELECT segmento_abc_xyz      AS segmento,
               COUNT(*)              AS num_skus,
               SUM(valor_total)      AS valor_total
        FROM clasificacion_abc_xyz
        WHERE segmento_abc_xyz IS NOT NULL
          AND LENGTH(segmento_abc_xyz) = 2
        GROUP BY segmento_abc_xyz
        ORDER BY valor_total DESC
        """
    )
    if df.empty:
        return DiamantesResponse(items=[], total_valor=0.0)

    total = float(df["valor_total"].sum())
    items = [
        DiamantePunto(
            segmento=str(row.segmento),
            num_skus=int(row.num_skus),
            valor_total=float(row.valor_total or 0),
            pct_valor=round(float(row.valor_total or 0) / total * 100, 2) if total else 0.0,
        )
        for row in df.itertuples(index=False)
    ]
    return DiamantesResponse(items=items, total_valor=round(total, 2))


@router.get(
    "/estacionalidad",
    response_model=EstacionalidadResponse,
    summary="Demanda mensual agregada — periodo 2024-2025",
)
def get_estacionalidad() -> EstacionalidadResponse:
    df = query(
        """
        SELECT YEAR(fecha_inicio_semana)      AS anio,
               MONTH(fecha_inicio_semana)     AS mes,
               MONTHNAME(fecha_inicio_semana) AS nombre_mes,
               SUM(cantidad_total)            AS cantidad_total_mes,
               AVG(cantidad_total)            AS cantidad_promedio_sku_semana
        FROM ventas_semanales
        WHERE fecha_inicio_semana BETWEEN '2024-01-01' AND '2025-12-31'
        GROUP BY YEAR(fecha_inicio_semana), MONTH(fecha_inicio_semana),
                 MONTHNAME(fecha_inicio_semana)
        ORDER BY anio, mes
        """
    )
    if df.empty:
        return EstacionalidadResponse(items=[])

    items = [
        EstacionalidadPunto(
            anio=int(row.anio),
            mes=int(row.mes),
            mes_label=(
                f"{MESES_ES.get(str(row.nombre_mes), str(row.nombre_mes)[:3])}"
                f" {str(row.anio)[2:]}"
            ),
            cantidad_total_mes=round(float(row.cantidad_total_mes or 0), 0),
            cantidad_promedio_sku_semana=round(float(row.cantidad_promedio_sku_semana or 0), 2),
        )
        for row in df.itertuples(index=False)
    ]
    return EstacionalidadResponse(items=items)


@router.get(
    "/ventas-por-centro",
    response_model=VentasPorCentroResponse,
    summary="Volumen histórico por centro de operación — 2024-2025",
)
def get_ventas_por_centro() -> VentasPorCentroResponse:
    df = query(
        """
        SELECT centro_operacion,
               SUM(cantidad_total)    AS cantidad_total,
               SUM(valor_bruto_total) AS valor_total
        FROM ventas_semanales
        WHERE fecha_inicio_semana BETWEEN '2024-01-01' AND '2025-12-31'
          AND centro_operacion IS NOT NULL
        GROUP BY centro_operacion
        ORDER BY cantidad_total DESC
        """
    )
    if df.empty:
        return VentasPorCentroResponse(items=[], total_cantidad=0.0, total_valor=0.0)

    total_q = float(df["cantidad_total"].sum())
    total_v = float(df["valor_total"].sum())
    items = [
        VentasCentro(
            centro_operacion=str(row.centro_operacion),
            cantidad_total=round(float(row.cantidad_total or 0), 0),
            valor_total=round(float(row.valor_total or 0), 2),
            pct_cantidad=round(float(row.cantidad_total or 0) / total_q * 100, 2) if total_q else 0.0,
        )
        for row in df.itertuples(index=False)
    ]
    return VentasPorCentroResponse(
        items=items,
        total_cantidad=round(total_q, 0),
        total_valor=round(total_v, 2),
    )
