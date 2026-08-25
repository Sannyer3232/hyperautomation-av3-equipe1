"""
Módulo de Leitura e Extração de Propostas e Critérios (Etapa 2).
Responsável: Membro 1 (Sannyer)
"""

from .reader import (
    ler_proposta,
    ler_todas_propostas,
    ler_criterios,
    ler_modelo_ranking,
    normalizar_nome_coluna
)

__all__ = [
    "ler_proposta",
    "ler_todas_propostas",
    "ler_criterios",
    "ler_modelo_ranking",
    "normalizar_nome_coluna"
]
