"""Router /api/pronosticos — top, sku/{item}, por-centro."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import pandas as pd
from fastapi import APIRouter, HTTPException

from api.config import (
    CENTROS_VALIDOS,
    FECHA_FIN_TRAIN,
    FECHA_FIN_VALID,
    MODELOS_VALIDOS,
)
from api.database import query
from api.schemas import (
    CentroPronostico,
    PronosticoItem,
    PronosticosPorCentroResponse,
    PronosticosTopResponse,
    PronosticoSKUResponse,
    SeriePunto,
    TopSKU,
)

router = APIRouter()


def _validar_fecha(fecha: str) -> None:
    try:
        datetime.strptime(fecha, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            400,
            detail={"code": "FECHA_INVALIDA", "message": f"Fecha '{fecha}' no es válida. Use formato YYYY-MM-DD."},
        )


def _validar_modelo(modelo: str) -> None:
    if modelo not in MODELOS_VALIDOS:
        raise HTTPException(
            400,
            detail={"code": "MODELO_INVALIDO", "message": f"Modelo '{modelo}' no válido. Opciones: {sorted(MODELOS_VALIDOS)}."},
        )


def _validar_centro(centro: Optional[str]) -> None:
    if centro and centro not in CENTROS_VALIDOS:
        raise HTTPException(
            400,
            detail={"code": "CENTRO_INVALIDO", "message": f"Centro '{centro}' no válido. Opciones: {sorted(CENTROS_VALIDOS)}."},
        )


def _asignar_split(fecha: pd.Timestamp) -> str:
    if fecha <= pd.Timestamp(FECHA_FIN_TRAIN):
        return "train"
    elif fecha <= pd.Timestamp(FECHA_FIN_VALID):
        return "valid"
    return "test_2026"


# ── GET /api/pronosticos/top ──────────────────────────────────────────────────

@router.get(
    "/top",
    response_model=PronosticosTopResponse,
    summary="Top N SKUs pronosticados para una semana",
    description=(
        "Retorna los SKUs con mayor demanda pronosticada para la semana indicada. "
        "Si no se especifica centro, agrega los 3 centros de operación."
    ),
    tags=["Pronósticos"],
)
def get_top_pronosticos(
    fecha: str = "2026-01-05",
    centro: Optional[str] = None,
    modelo: str = "lightgbm",
    limit: int = 20,
) -> PronosticosTopResponse:
    _validar_fecha(fecha)
    _validar_modelo(modelo)
    _validar_centro(centro)
    limit = max(1, min(limit, 200))

    centro_filter = "AND p.centro_operacion = :centro" if centro else ""
    params: dict = {"fecha": fecha, "modelo": modelo, "limit": limit}
    if centro:
        params["centro"] = centro

    if centro:
        sql = """
            SELECT p.item,
                   COALESCE(d.nombre_item, p.item) AS nombre_item,
                   d.nombre_linea_n1                AS linea,
                   p.centro_operacion,
                   p.cantidad_predicha,
                   p.cantidad_real,
                   c.clase_abc,
                   c.segmento_abc_xyz
            FROM pronosticos p
            LEFT JOIN dim_producto         d ON p.item = d.item
            LEFT JOIN clasificacion_abc_xyz c ON p.item = c.item
            WHERE p.fecha_inicio_semana = :fecha
              AND p.modelo              = :modelo
              AND p.centro_operacion    = :centro
            ORDER BY p.cantidad_predicha DESC
            LIMIT :limit
        """
    else:
        sql = """
            SELECT p.item,
                   COALESCE(MAX(d.nombre_item), p.item) AS nombre_item,
                   MAX(d.nombre_linea_n1)                AS linea,
                   'todos'                               AS centro_operacion,
                   SUM(p.cantidad_predicha)              AS cantidad_predicha,
                   SUM(p.cantidad_real)                  AS cantidad_real,
                   MAX(c.clase_abc)                      AS clase_abc,
                   MAX(c.segmento_abc_xyz)               AS segmento_abc_xyz
            FROM pronosticos p
            LEFT JOIN dim_producto         d ON p.item = d.item
            LEFT JOIN clasificacion_abc_xyz c ON p.item = c.item
            WHERE p.fecha_inicio_semana = :fecha
              AND p.modelo              = :modelo
            GROUP BY p.item
            ORDER BY cantidad_predicha DESC
            LIMIT :limit
        """

    df = query(sql, params)

    items = []
    for row in df.itertuples(index=False):
        real = float(row.cantidad_real) if row.cantidad_real is not None and pd.notna(row.cantidad_real) else None
        pred = float(row.cantidad_predicha)
        error = abs(real - pred) if real is not None else None
        items.append(
            PronosticoItem(
                item=str(row.item),
                nombre_item=str(row.nombre_item),
                linea=str(row.linea) if row.linea else None,
                centro_operacion=str(row.centro_operacion),
                cantidad_pronosticada=pred,
                cantidad_real=real,
                clase_abc=str(row.clase_abc) if row.clase_abc else None,
                segmento_abc_xyz=str(row.segmento_abc_xyz) if row.segmento_abc_xyz else None,
                error_absoluto=round(error, 4) if error is not None else None,
            )
        )

    return PronosticosTopResponse(
        fecha_semana=fecha,
        modelo=modelo,
        centro_filtro=centro,
        total=len(items),
        items=items,
    )


# ── GET /api/pronosticos/sku/{item} ───────────────────────────────────────────

@router.get(
    "/sku/{item}",
    response_model=PronosticoSKUResponse,
    summary="Serie histórica + predicciones de un SKU",
    description=(
        "Retorna la serie temporal completa (datos reales + predicciones) de un SKU. "
        "Si no se especifica centro, agrega los 3 centros sumando cantidades."
    ),
    tags=["Pronósticos"],
)
def get_sku_serie(
    item: str,
    centro: Optional[str] = None,
    modelo: str = "lightgbm",
    incluir_baseline: bool = True,
    desde: str = "2024-01-01",
    hasta: str = "2026-03-31",
) -> PronosticoSKUResponse:
    _validar_modelo(modelo)
    _validar_centro(centro)
    _validar_fecha(desde)
    _validar_fecha(hasta)

    # Verificar que el SKU existe
    meta_df = query(
        """
        SELECT d.nombre_item, d.nombre_linea_n1,
               c.clase_abc, c.segmento_abc_xyz
        FROM dim_producto d
        LEFT JOIN clasificacion_abc_xyz c ON d.item = c.item
        WHERE d.item = :item
        LIMIT 1
        """,
        {"item": item},
    )
    if meta_df.empty:
        raise HTTPException(
            404,
            detail={"code": "SKU_NOT_FOUND", "message": f"El SKU '{item}' no existe en la base de datos.", "details": None},
        )
    meta = meta_df.iloc[0]

    # Datos reales desde ventas_semanales
    if centro:
        reales_df = query(
            """
            SELECT fecha_inicio_semana, SUM(cantidad_total) AS cantidad_real
            FROM ventas_semanales
            WHERE item = :item
              AND centro_operacion = :centro
              AND fecha_inicio_semana BETWEEN :desde AND :hasta
            GROUP BY fecha_inicio_semana
            """,
            {"item": item, "centro": centro, "desde": desde, "hasta": hasta},
        )
    else:
        reales_df = query(
            """
            SELECT fecha_inicio_semana, SUM(cantidad_total) AS cantidad_real
            FROM ventas_semanales
            WHERE item = :item
              AND fecha_inicio_semana BETWEEN :desde AND :hasta
            GROUP BY fecha_inicio_semana
            """,
            {"item": item, "desde": desde, "hasta": hasta},
        )

    # Predicciones: modelo principal + baseline opcional
    modelos_lista = [modelo]
    if incluir_baseline and modelo != "baseline_ma4":
        modelos_lista.append("baseline_ma4")
    modelos_in = "','".join(modelos_lista)

    if centro:
        preds_df = query(
            f"""
            SELECT fecha_inicio_semana, modelo, SUM(cantidad_predicha) AS cantidad_predicha
            FROM pronosticos
            WHERE item = :item
              AND modelo IN ('{modelos_in}')
              AND centro_operacion = :centro
              AND fecha_inicio_semana BETWEEN :desde AND :hasta
            GROUP BY fecha_inicio_semana, modelo
            """,
            {"item": item, "centro": centro, "desde": desde, "hasta": hasta},
        )
    else:
        preds_df = query(
            f"""
            SELECT fecha_inicio_semana, modelo, SUM(cantidad_predicha) AS cantidad_predicha
            FROM pronosticos
            WHERE item = :item
              AND modelo IN ('{modelos_in}')
              AND fecha_inicio_semana BETWEEN :desde AND :hasta
            GROUP BY fecha_inicio_semana, modelo
            """,
            {"item": item, "desde": desde, "hasta": hasta},
        )

    # Pivot predicciones por modelo
    if not preds_df.empty:
        preds_df["fecha_inicio_semana"] = pd.to_datetime(preds_df["fecha_inicio_semana"])
        preds_pivot = preds_df.pivot(
            index="fecha_inicio_semana", columns="modelo", values="cantidad_predicha"
        )
    else:
        preds_pivot = pd.DataFrame()

    # Merge con reales
    if not reales_df.empty:
        reales_df["fecha_inicio_semana"] = pd.to_datetime(reales_df["fecha_inicio_semana"])
        base = reales_df.set_index("fecha_inicio_semana")
    else:
        base = pd.DataFrame(columns=["cantidad_real"])

    if not preds_pivot.empty:
        merged = base.join(preds_pivot, how="outer")
    else:
        merged = base.copy()

    merged = merged.sort_index()

    serie = []
    for fecha_ts, row in merged.iterrows():
        fecha_ts = pd.Timestamp(fecha_ts)
        real_val = row.get("cantidad_real")
        real = float(real_val) if real_val is not None and pd.notna(real_val) else None

        pred_principal = row.get(modelo)
        pred_base = row.get("baseline_ma4")

        serie.append(
            SeriePunto(
                fecha=fecha_ts.strftime("%Y-%m-%d"),
                cantidad_real=real,
                cantidad_predicha_principal=float(pred_principal) if pred_principal is not None and pd.notna(pred_principal) else None,
                cantidad_predicha_baseline=float(pred_base) if pred_base is not None and pd.notna(pred_base) else None,
                split=_asignar_split(fecha_ts),
            )
        )

    return PronosticoSKUResponse(
        item=item,
        nombre_item=str(meta["nombre_item"]) if meta["nombre_item"] else item,
        linea=str(meta["nombre_linea_n1"]) if meta["nombre_linea_n1"] else None,
        clase_abc=str(meta["clase_abc"]) if meta["clase_abc"] else None,
        segmento_abc_xyz=str(meta["segmento_abc_xyz"]) if meta["segmento_abc_xyz"] else None,
        centro=centro,
        modelo_principal=modelo,
        serie=serie,
    )


# ── GET /api/pronosticos/por-centro ──────────────────────────────────────────

@router.get(
    "/por-centro",
    response_model=PronosticosPorCentroResponse,
    summary="Predicciones agregadas por centro de operación",
    description="Retorna el total pronosticado por cada centro y sus top 5 SKUs.",
    tags=["Pronósticos"],
)
def get_por_centro(
    fecha: str = "2026-01-05",
    modelo: str = "lightgbm",
) -> PronosticosPorCentroResponse:
    _validar_fecha(fecha)
    _validar_modelo(modelo)

    # Totales por centro
    totales_df = query(
        """
        SELECT centro_operacion,
               SUM(cantidad_predicha)  AS total_pronosticado,
               SUM(cantidad_real)      AS total_real,
               COUNT(DISTINCT item)    AS num_skus_distintos
        FROM pronosticos
        WHERE fecha_inicio_semana = :fecha
          AND modelo               = :modelo
        GROUP BY centro_operacion
        ORDER BY centro_operacion
        """,
        {"fecha": fecha, "modelo": modelo},
    )

    # Top 5 por centro con window function
    top_df = query(
        """
        WITH ranked AS (
            SELECT p.item,
                   COALESCE(d.nombre_item, p.item) AS nombre_item,
                   p.centro_operacion,
                   p.cantidad_predicha,
                   ROW_NUMBER() OVER (
                       PARTITION BY p.centro_operacion
                       ORDER BY p.cantidad_predicha DESC
                   ) AS rn
            FROM pronosticos p
            LEFT JOIN dim_producto d ON p.item = d.item
            WHERE p.fecha_inicio_semana = :fecha
              AND p.modelo              = :modelo
        )
        SELECT item, nombre_item, centro_operacion, cantidad_predicha
        FROM ranked
        WHERE rn <= 5
        ORDER BY centro_operacion, cantidad_predicha DESC
        """,
        {"fecha": fecha, "modelo": modelo},
    )

    centros = []
    for row in totales_df.itertuples(index=False):
        centro = str(row.centro_operacion)
        real_val = row.total_real
        top_rows = top_df[top_df["centro_operacion"] == centro]
        top_skus = [
            TopSKU(
                item=str(r["item"]),
                nombre=str(r["nombre_item"]),
                cantidad=float(r["cantidad_predicha"]),
            )
            for _, r in top_rows.iterrows()
        ]
        centros.append(
            CentroPronostico(
                centro_operacion=centro,
                total_pronosticado=float(row.total_pronosticado),
                total_real=float(real_val) if real_val is not None and pd.notna(real_val) else None,
                num_skus_distintos=int(row.num_skus_distintos),
                top_skus=top_skus,
            )
        )

    return PronosticosPorCentroResponse(
        fecha_semana=fecha,
        modelo=modelo,
        centros=centros,
    )
