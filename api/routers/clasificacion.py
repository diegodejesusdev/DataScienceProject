"""Router /api/clasificacion — resumen ABC×XYZ."""

from __future__ import annotations

from fastapi import APIRouter

from api.database import query
from api.schemas import (
    ClasificacionResumenResponse,
    DistribucionABCItem,
    SegmentoMatriz,
    SKUEstrella,
    SkusEstrella,
)

router = APIRouter()


@router.get(
    "/resumen",
    response_model=ClasificacionResumenResponse,
    summary="Matriz ABC × XYZ con KPIs descriptivos",
    description=(
        "Retorna el resumen completo de la clasificación ABC/XYZ: "
        "distribución por clase, matriz de segmentos y top SKUs estrella."
    ),
    tags=["Clasificación"],
)
def get_clasificacion_resumen() -> ClasificacionResumenResponse:

    # Totales globales
    totales_df = query(
        "SELECT COUNT(*) AS total_skus, SUM(valor_total) AS valor_total FROM clasificacion_abc_xyz"
    )
    total_skus = int(totales_df["total_skus"].iloc[0])
    valor_total_global = float(totales_df["valor_total"].iloc[0] or 0)

    # Distribución por clase ABC
    abc_df = query(
        """
        SELECT clase_abc,
               COUNT(*)         AS num_skus,
               SUM(valor_total) AS valor_total_clase
        FROM clasificacion_abc_xyz
        GROUP BY clase_abc
        ORDER BY clase_abc
        """
    )

    distribucion_abc: dict[str, DistribucionABCItem] = {}
    for row in abc_df.itertuples(index=False):
        clase = str(row.clase_abc)
        num = int(row.num_skus)
        val = float(row.valor_total_clase or 0)
        distribucion_abc[clase] = DistribucionABCItem(
            num_skus=num,
            porcentaje_skus=round(num / total_skus * 100, 2) if total_skus else 0,
            valor_total=val,
            porcentaje_valor=round(val / valor_total_global * 100, 2) if valor_total_global else 0,
        )

    # Matriz de segmentos ABC × XYZ
    seg_df = query(
        """
        SELECT LEFT(segmento_abc_xyz, 1)  AS clase_abc,
               RIGHT(segmento_abc_xyz, 1) AS clase_xyz,
               COUNT(*)                   AS num_skus,
               SUM(valor_total)           AS valor_total
        FROM clasificacion_abc_xyz
        WHERE segmento_abc_xyz IS NOT NULL
          AND LENGTH(segmento_abc_xyz) = 2
        GROUP BY LEFT(segmento_abc_xyz, 1), RIGHT(segmento_abc_xyz, 1)
        ORDER BY clase_abc, clase_xyz
        """
    )

    matriz_segmentos = [
        SegmentoMatriz(
            clase_abc=str(row.clase_abc),
            clase_xyz=str(row.clase_xyz),
            num_skus=int(row.num_skus),
            valor_total=float(row.valor_total or 0),
        )
        for row in seg_df.itertuples(index=False)
    ]

    # Top 5 SKUs estrella (clase A, segmento AX o AY, por valor)
    estrella_df = query(
        """
        SELECT item, nombre_item, valor_total
        FROM clasificacion_abc_xyz
        WHERE clase_abc = 'A'
          AND segmento_abc_xyz IN ('AX', 'AY')
        ORDER BY valor_total DESC
        LIMIT 5
        """
    )

    skus_estrella_items = [
        SKUEstrella(
            item=str(row.item),
            nombre=str(row.nombre_item),
            valor_total=float(row.valor_total or 0),
        )
        for row in estrella_df.itertuples(index=False)
    ]

    return ClasificacionResumenResponse(
        total_skus_activos=total_skus,
        valor_total_periodo=valor_total_global,
        distribucion_abc=distribucion_abc,
        matriz_segmentos=matriz_segmentos,
        skus_estrella=SkusEstrella(
            definicion="Top 5 SKUs clase A con segmento AX o AY (mayor valor y demanda estable)",
            items=skus_estrella_items,
        ),
    )
