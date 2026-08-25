"""
Módulo de Validação e Regras de Negócio (Etapa 3).
Responsável: Membro 2
"""

try:
    from .validator import (
        validar_proposta_individual,
        validar_todas_propostas
    )
    __all__ = [
        "validar_proposta_individual",
        "validar_todas_propostas"
    ]
except ImportError:
    validar_proposta_individual = None  # type: ignore
    validar_todas_propostas = None  # type: ignore
    __all__ = []
