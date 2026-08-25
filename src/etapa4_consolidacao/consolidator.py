"""
Módulo de Consolidação de Propostas (Etapa 4).
Responsável: Membro 2

Recebe as propostas válidas da Etapa 3 e prepara os dados
para envio à Etapa 5 - Ranking.
"""

import logging
from typing import Any


logger = logging.getLogger("Hyperautomation")


CAMPOS_CONSOLIDADOS = [
    "Fornecedor",
    "Produto",
    "Custo",
    "Prazo_Dias",
    "Capacidade",
    "Qualidade",
    "Status",
    "Observacao",
]


def consolidar_propostas(
    propostas_validas: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """
    Consolida as propostas válidas para envio à Etapa 5.

    A consolidação mantém os dados em formato list[dict],
    acrescentando/garantindo os campos de validação:

        - Status
        - Observacao

    Args:
        propostas_validas:
            Lista de propostas aprovadas pela Etapa 3.

    Returns:
        Lista de dicionários contendo as propostas consolidadas.
    """

    logger.info(
        "[CONSOLIDAÇÃO] Iniciando Etapa 4 | "
        f"Propostas recebidas: {len(propostas_validas)}"
    )

    if not propostas_validas:
        logger.warning(
            "[CONSOLIDAÇÃO] Nenhuma proposta válida recebida."
        )

        return []

    propostas_consolidadas = []

    for proposta in propostas_validas:

        fornecedor = proposta.get(
            "Fornecedor",
            "Fornecedor não identificado"
        )

        try:
            proposta_consolidada = {}

            # Mantém somente os campos definidos
            # no contrato da consolidação.
            for campo in CAMPOS_CONSOLIDADOS:
                proposta_consolidada[campo] = proposta.get(campo)

            # Garantia dos dados de validação
            if not proposta_consolidada["Status"]:
                proposta_consolidada["Status"] = "VALIDO"

            if not proposta_consolidada["Observacao"]:
                proposta_consolidada["Observacao"] = (
                    "Proposta válida."
                )

            propostas_consolidadas.append(
                proposta_consolidada
            )

            logger.info(
                "[CONSOLIDAÇÃO] Proposta consolidada | "
                f"Fornecedor: {fornecedor}"
            )

        except Exception as exc:

            logger.exception(
                "[CONSOLIDAÇÃO] Erro ao consolidar proposta | "
                f"Fornecedor: {fornecedor}"
            )

            raise RuntimeError(
                "Falha ao consolidar a proposta "
                f"do fornecedor {fornecedor}."
            ) from exc

    logger.info(
        "[CONSOLIDAÇÃO] Etapa 4 concluída | "
        f"Total consolidado: {len(propostas_consolidadas)}"
    )

    return propostas_consolidadas
