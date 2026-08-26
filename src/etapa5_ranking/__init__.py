"""
Módulo de Cálculo de Ranking e Scoring MCDA (Etapa 5).
Responsável: Membro 3
"""

from .ranking import (
    calcular_ranking_ponderado,
    calculate_ranking,
    normalize_status,
    normalize_inverse_value,
    normalize_direct_value,
    get_extrema,
    calculate_individual_score,
    extrair_pesos_criterios,
    fill_spreadsheet
)

__all__ = [
    "calcular_ranking_ponderado",
    "calculate_ranking",
    "normalize_status",
    "normalize_inverse_value",
    "normalize_direct_value",
    "get_extrema",
    "calculate_individual_score",
    "extrair_pesos_criterios",
    "fill_spreadsheet"
]
