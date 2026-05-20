"""Router /api/metricas — comparación de los 4 modelos."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.config import NOMBRES_MODELO, SEGMENTOS_VALIDOS, SPLITS_VALIDOS
from api.database import query
from api.schemas import MetricasComparacionResponse, MetricasModelo

router = APIRouter()

MODELO_RECOMENDADO = "lightgbm"


@router.get(
    "/comparacion",
    response_model=MetricasComparacionResponse,
    summary="Tabla comparativa de métricas por modelo",
    description=(
        "Retorna MAE, RMSE, MAPE y sMAPE de todos los modelos disponibles "
        "para el split y segmento solicitados. Calcula la mejora porcentual "
        "sobre el baseline cuando este está disponible en el mismo segmento."
    ),
    tags=["Métricas"],
)
def get_comparacion(
    split: str = "test_2026",
    segmento: str = "global",
) -> MetricasComparacionResponse:

    if split not in SPLITS_VALIDOS:
        raise HTTPException(
            400,
            detail={"code": "SPLIT_INVALIDO", "message": f"Split '{split}' no válido. Opciones: {sorted(SPLITS_VALIDOS)}."},
        )
    if segmento not in SEGMENTOS_VALIDOS:
        raise HTTPException(
            400,
            detail={"code": "SEGMENTO_INVALIDO", "message": f"Segmento '{segmento}' no válido. Opciones: {sorted(SEGMENTOS_VALIDOS)}."},
        )

    df = query(
        """
        SELECT modelo, mae, rmse, mape, smape, n_obs
        FROM metricas_modelos
        WHERE split    = :split
          AND segmento = :segmento
        ORDER BY mae ASC
        """,
        {"split": split, "segmento": segmento},
    )

    if df.empty:
        raise HTTPException(
            404,
            detail={
                "code": "SIN_DATOS",
                "message": f"No hay métricas para split='{split}' y segmento='{segmento}'.",
                "details": None,
            },
        )

    # MAE del baseline para calcular mejora (solo si está en el resultado)
    baseline_mae: float | None = None
    if "baseline_ma4" in df["modelo"].values:
        baseline_mae = float(df.loc[df["modelo"] == "baseline_ma4", "mae"].iloc[0])

    modelos = []
    for row in df.itertuples(index=False):
        modelo_key = str(row.modelo)
        mejora = None
        if baseline_mae is not None and modelo_key != "baseline_ma4":
            mejora = round((baseline_mae - float(row.mae)) / baseline_mae * 100, 2)

        modelos.append(
            MetricasModelo(
                modelo=modelo_key,
                nombre_amigable=NOMBRES_MODELO.get(modelo_key, modelo_key),
                mae=round(float(row.mae), 4),
                rmse=round(float(row.rmse), 4),
                mape=round(float(row.mape), 4),
                smape=round(float(row.smape), 4),
                n_obs=int(row.n_obs),
                mejora_vs_baseline_pct=mejora,
            )
        )

    return MetricasComparacionResponse(
        split=split,
        segmento=segmento,
        modelos=modelos,
        modelo_recomendado=MODELO_RECOMENDADO,
    )
