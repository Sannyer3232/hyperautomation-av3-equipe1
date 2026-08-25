"""
Módulo de Validação de Propostas (Etapa 3).
Responsável: Membro 2
"""

import logging
from typing import Any

from src.logger import AuditLogger


logger = logging.getLogger("Hyperautomation")


# Campos obrigatórios da proposta
CAMPOS_OBRIGATORIOS = [
    "Fornecedor",
    "Produto",
    "Custo",
    "Prazo_Dias",
    "Capacidade",
    "Qualidade",
]


def obter_codigo_fornecedor(fornecedor: str) -> str:
    """
    Extrai o código do fornecedor a partir do nome.

    Exemplos:
        Fornecedor A -> A
        Fornecedor B -> B
        Fornecedor C -> C
    """

    if not fornecedor:
        return ""

    return fornecedor.strip().split()[-1].upper()


def validar_proposta_individual(
    proposta: dict[str, Any]
) -> tuple[bool, str]:
    """
    Valida os dados comerciais de uma proposta.

    São verificadas:
        - presença dos campos obrigatórios;
        - fornecedor;
        - produto;
        - custo;
        - prazo;
        - capacidade;
        - qualidade.

    A verificação do status do fornecedor no sistema web
    é realizada posteriormente em validar_todas_propostas().

    Args:
        proposta: Dicionário contendo os dados da proposta.

    Returns:
        Tupla contendo:
            bool: True se a proposta for válida.
            str: mensagem da validação.
    """

    fornecedor = proposta.get(
        "Fornecedor",
        "Fornecedor não identificado"
    )

    logger.info(
        "[VALIDAÇÃO] Iniciando validação | "
        f"Fornecedor: {fornecedor}"
    )

    erros = []

    # =========================================================
    # 1. CAMPOS OBRIGATÓRIOS
    # =========================================================

    campos_faltantes = [
        campo
        for campo in CAMPOS_OBRIGATORIOS
        if campo not in proposta
    ]

    if campos_faltantes:
        erros.append(
            "Campos obrigatórios ausentes: "
            + ", ".join(campos_faltantes)
        )

    # =========================================================
    # 2. FORNECEDOR
    # =========================================================

    if "Fornecedor" in proposta:
        if not str(proposta["Fornecedor"]).strip():
            erros.append(
                "Fornecedor não informado."
            )

    # =========================================================
    # 3. PRODUTO
    # =========================================================

    if "Produto" in proposta:
        if not str(proposta["Produto"]).strip():
            erros.append(
                "Produto não informado."
            )

    # =========================================================
    # 4. CUSTO
    # =========================================================

    if "Custo" in proposta:
        try:
            custo = float(proposta["Custo"])

            if custo <= 0:
                erros.append(
                    "Custo deve ser maior que zero."
                )

        except (TypeError, ValueError):
            erros.append(
                "Custo deve ser numérico."
            )

    # =========================================================
    # 5. PRAZO
    # =========================================================

    if "Prazo_Dias" in proposta:
        try:
            prazo = float(proposta["Prazo_Dias"])

            if prazo <= 0:
                erros.append(
                    "Prazo_Dias deve ser maior que zero."
                )

        except (TypeError, ValueError):
            erros.append(
                "Prazo_Dias deve ser numérico."
            )

    # =========================================================
    # 6. CAPACIDADE
    # =========================================================

    if "Capacidade" in proposta:
        try:
            capacidade = float(proposta["Capacidade"])

            if capacidade <= 0:
                erros.append(
                    "Capacidade deve ser maior que zero."
                )

        except (TypeError, ValueError):
            erros.append(
                "Capacidade deve ser numérica."
            )

    # =========================================================
    # 7. QUALIDADE
    # =========================================================

    if "Qualidade" in proposta:
        try:
            qualidade = float(proposta["Qualidade"])

            if not 0 <= qualidade <= 100:
                erros.append(
                    "Qualidade deve estar entre 0 e 100."
                )

        except (TypeError, ValueError):
            erros.append(
                "Qualidade deve ser numérica."
            )

    # =========================================================
    # RESULTADO
    # =========================================================

    if erros:
        observacao = "; ".join(erros)

        logger.warning(
            "[VALIDAÇÃO] Proposta rejeitada | "
            f"Fornecedor: {fornecedor} | "
            f"Motivo: {observacao}"
        )

        return False, observacao

    logger.info(
        "[VALIDAÇÃO] Dados comerciais válidos | "
        f"Fornecedor: {fornecedor}"
    )

    return True, "Proposta válida."


def validar_todas_propostas(
    propostas: list[dict[str, Any]],
    status_web: dict[str, str],
    audit: AuditLogger
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Valida todas as propostas recebidas.

    Além da validação dos dados comerciais, verifica se o
    fornecedor está ativo no sistema web.

    Args:
        propostas:
            Lista de propostas provenientes da Etapa 2.

        status_web:
            Dicionário contendo o status dos fornecedores.

            Exemplo:
                {
                    "A": "Ativo",
                    "B": "Ativo",
                    "C": "Ativo",
                    "D": "Bloqueado"
                }

        audit:
            Instância do AuditLogger utilizada para auditoria.

    Returns:
        Tupla contendo:
            propostas_validas:
                Lista de propostas aprovadas.

            propostas_rejeitadas:
                Lista de propostas rejeitadas.
    """

    logger.info(
        "[VALIDAÇÃO] Iniciando Etapa 3 | "
        f"Total de propostas recebidas: {len(propostas)}"
    )

    propostas_validas = []
    propostas_rejeitadas = []

    for proposta in propostas:

        fornecedor = proposta.get(
            "Fornecedor",
            "Fornecedor não identificado"
        )

        try:

            # -------------------------------------------------
            # Validação dos dados comerciais
            # -------------------------------------------------

            valida, observacao = validar_proposta_individual(
                proposta
            )

            erros = []

            if not valida:
                erros.append(observacao)

            # -------------------------------------------------
            # Verificação do status no sistema web
            # -------------------------------------------------

            codigo_fornecedor = obter_codigo_fornecedor(
                fornecedor
            )

            status_fornecedor = status_web.get(
                codigo_fornecedor
            )

            logger.info(
                "[VALIDAÇÃO] Status Web | "
                f"Fornecedor: {fornecedor} | "
                f"Status: {status_fornecedor or 'Não encontrado'}"
            )

            if status_fornecedor != "Ativo":

                erros.append(
                    "Fornecedor não está habilitado no "
                    "sistema web. "
                    f"Status: {status_fornecedor or 'Não encontrado'}."
                )

            # -------------------------------------------------
            # Montagem do resultado
            # -------------------------------------------------

            resultado = proposta.copy()

            if erros:

                observacao_final = "; ".join(erros)

                resultado["Status"] = "REJEITADO"
                resultado["Observacao"] = observacao_final

                propostas_rejeitadas.append(resultado)

                logger.warning(
                    "[VALIDAÇÃO] PROPOSTA REJEITADA | "
                    f"Fornecedor: {fornecedor} | "
                    f"Motivo: {observacao_final}"
                )

                audit.registrar_proposta_rejeitada(
                    fornecedor=fornecedor,
                    motivo=observacao_final,
                    dados=resultado
                )

            else:

                resultado["Status"] = "VALIDO"
                resultado["Observacao"] = "Proposta válida."

                propostas_validas.append(resultado)

                logger.info(
                    "[VALIDAÇÃO] PROPOSTA APROVADA | "
                    f"Fornecedor: {fornecedor}"
                )

                audit.registrar_proposta_valida(
                    fornecedor=fornecedor,
                    dados=resultado
                )

        except Exception as exc:

            mensagem = (
                "Erro inesperado durante a validação."
            )

            logger.exception(
                "[VALIDAÇÃO] Erro inesperado | "
                f"Fornecedor: {fornecedor}"
            )

            resultado = proposta.copy()
            resultado["Status"] = "REJEITADO"
            resultado["Observacao"] = mensagem

            propostas_rejeitadas.append(resultado)

            audit.registrar_erro(
                etapa="Validação",
                mensagem=(
                    f"{mensagem} Fornecedor: {fornecedor}"
                ),
                excecao=exc
            )

    # =========================================================
    # RESUMO
    # =========================================================

    logger.info(
        "[VALIDAÇÃO] Etapa 3 concluída | "
        f"Válidas: {len(propostas_validas)} | "
        f"Rejeitadas: {len(propostas_rejeitadas)}"
    )

    return propostas_validas, propostas_rejeitadas

