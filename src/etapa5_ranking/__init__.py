"""
Módulo de Cálculo de Ranking e Scoring MCDA (Etapa 5).
Responsável: Membro 3
"""

try:
    from .ranker import calcular_ranking_ponderado
    __all__ = ["calcular_ranking_ponderado"]
except ImportError:
    calcular_ranking_ponderado = None  # type: ignore
    __all__ = []
