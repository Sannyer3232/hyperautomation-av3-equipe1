"""
Módulo de Validação e Regras de Negócio (Etapa 3).
Responsável: Membro 2
"""

try:
    from .validator import (
        obter_codigo_fornecedor,
        validar_proposta_individual,
        validar_todas_propostas,
        CAMPOS_OBRIGATORIOS
    )
    __all__ = [
        "obter_codigo_fornecedor",
        "validar_proposta_individual",
        "validar_todas_propostas",
        "CAMPOS_OBRIGATORIOS"
    ]
except ImportError:
    obter_codigo_fornecedor = None  # type: ignore
    validar_proposta_individual = None  # type: ignore
    validar_todas_propostas = None  # type: ignore
    CAMPOS_OBRIGATORIOS = []  # type: ignore
    __all__ = []
