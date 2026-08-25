"""
Módulo de Consolidação de Propostas Válidas (Etapa 4).
Responsável: Membro 2
"""

try:
    from .consolidator import consolidar_propostas_validas
    __all__ = ["consolidar_propostas_validas"]
except ImportError:
    consolidar_propostas_validas = None  # type: ignore
    __all__ = []
