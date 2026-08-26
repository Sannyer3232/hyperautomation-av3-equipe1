"""
Pipeline Principal de Hyperautomation - Seleção de Fornecedores LG Electronics.
Orquestra as 6 etapas do fluxo ponta a ponta:
1. Coleta -> 2. Leitura -> 3. Validação -> 4. Consolidação -> 5. Ranking -> 6. Resultado
"""

import sys
from pathlib import Path

# Adiciona o diretório raiz ao sys.path para garantir importações relativas
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.config import (  # noqa: E402
    PROPOSTAS_DIR,
    CRITERIOS_PATH,
    OUTPUT_RANKING_PATH,
    TRIGGER_MODE,
    EMAIL_POLL_INTERVAL
)
from src.logger import logger, AuditLogger  # noqa: E402
from src.etapa1_coleta import coletar_propostas_e_status_web  # noqa: E402
from src.etapa2_leitura import ler_todas_propostas, ler_criterios  # noqa: E402
from src.etapa3_validacao import validar_todas_propostas  # noqa: E402
from src.etapa4_consolidacao import (  # noqa: E402
    consolidar_propostas,
    consolidar_propostas_validas
)
from src.etapa5_ranking import calcular_ranking_ponderado  # noqa: E402
from src.etapa6_resultado import gerar_resultado_final  # noqa: E402
from src.email_trigger import EmailTriggerService  # noqa: E402


def executar_pipeline_hyperautomation() -> int:
    """
    Função principal que orquestra todo o ciclo de vida do robô de seleção de fornecedores.
    """
    audit = AuditLogger()
    logger.info("=================================================================")
    logger.info("  INICIANDO PROCESSO DE HYPERAUTOMATION — SELEÇÃO DE FORNECEDORES")
    logger.info("=================================================================")

    try:
        # ETAPA 1: COLETA (Membro 1)
        arquivos_propostas, status_web = coletar_propostas_e_status_web(
            propostas_dir=PROPOSTAS_DIR,
            audit=audit
        )
        if not arquivos_propostas:
            logger.error("Nenhum arquivo de proposta encontrado. Abortando execução.")
            audit.registrar_erro("Coleta", "Nenhum arquivo encontrado no diretório de propostas.")
            audit.salvar_auditoria()
            return 1

        # ETAPA 2: LEITURA (Membro 1)
        propostas_brutas = ler_todas_propostas(
            arquivos=arquivos_propostas,
            audit=audit
        )
        df_criterios = ler_criterios(CRITERIOS_PATH)

        logger.info(
            f"[INTEGRAÇÃO E1+E2] Coleta e Leitura concluídas com sucesso. "
            f"{len(propostas_brutas)} propostas lidas de {len(arquivos_propostas)} arquivo(s)."
        )

        # ETAPA 3: VALIDAÇÃO (Membro 2)
        if validar_todas_propostas is None:
            logger.info("[PIPELINE] Etapas 1 e 2 concluídas com sucesso. Aguardando implementação da Etapa 3.")
            resumo_auditoria = audit.salvar_auditoria()
            logger.info("=================================================================")
            logger.info("  INTEGRAÇÃO ETAPA 1 (COLETA) + ETAPA 2 (LEITURA) HOMOLOGADA")
            logger.info(f"  Total Propostas Coletadas e Lidas: {len(propostas_brutas)}")
            logger.info(f"  Status Cadastrais Mapeados:        {len(status_web)}")
            logger.info(f"  Critérios Carregados:              {len(df_criterios)}")
            logger.info("=================================================================")
            return 0

        propostas_validas, propostas_rejeitadas = validar_todas_propostas(
            propostas=propostas_brutas,
            status_web=status_web,
            audit=audit
        )

        # ETAPA 4: CONSOLIDAÇÃO (Membro 2)
        if consolidar_propostas is None and consolidar_propostas_validas is None:
            logger.info("[PIPELINE] Etapas 1, 2 e 3 concluídas. Aguardando Etapa 4.")
            audit.salvar_auditoria()
            return 0

        funcao_consolidar = consolidar_propostas or consolidar_propostas_validas
        dados_consolidados = funcao_consolidar(propostas_validas)

        # ETAPA 5: RANKING (Membro 3)
        if calcular_ranking_ponderado is None:
            logger.info("[PIPELINE] Etapas 1-4 concluídas. Aguardando Etapa 5.")
            audit.salvar_auditoria()
            return 0

        df_ranking = calcular_ranking_ponderado(
            propostas=dados_consolidados,
            df_criterios=df_criterios,
            audit=audit
        )

        # ETAPA 6: RESULTADO (Membro 3)
        if gerar_resultado_final is None:
            logger.info("[PIPELINE] Etapas 1-5 concluídas. Aguardando Etapa 6.")
            audit.salvar_auditoria()
            return 0

        df_resultado = gerar_resultado_final(
            df_ranking=df_ranking,
            propostas_rejeitadas=propostas_rejeitadas,
            output_path=OUTPUT_RANKING_PATH,
            audit=audit
        )

        # PERSISTÊNCIA DE AUDITORIA E LOGS
        resumo_auditoria = audit.salvar_auditoria()

        logger.info("=================================================================")
        logger.info("  PROCESSO CONCLUÍDO COM SUCESSO!")
        logger.info(f"  Total Processadas: {resumo_auditoria['total_recebidas']}")
        logger.info(f"  Total Válidas:     {resumo_auditoria['total_validas']}")
        logger.info(f"  Total Rejeitadas:  {resumo_auditoria['total_rejeitadas']}")
        logger.info(f"  Arquivo Gerado:    {OUTPUT_RANKING_PATH}")
        logger.info("=================================================================")

        # Imprime o ranking final formatado no console
        print("\n--- QUADRO FINAL DE HOMOLOGAÇÃO DE FORNECEDORES ---")
        print(df_resultado.to_string(index=False))
        print("---------------------------------------------------\n")

        return 0

    except Exception as e:
        logger.critical(f"Falha não tratada durante a execução da pipeline: {e}", exc_info=True)
        audit.registrar_erro("Pipeline", str(e), e)
        audit.salvar_auditoria()
        return 1


def main() -> int:
    """Função principal com suporte a execução por diretório ou trigger de e-mail."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Robô de Hyperautomation - Processo de Seleção de Fornecedores LG"
    )
    parser.add_argument(
        "--email-trigger",
        "--watch-email",
        action="store_true",
        help="Inicia o monitoramento contínuo da caixa de e-mail (IMAP) para processar novos anexos."
    )
    parser.add_argument(
        "--email-check",
        action="store_true",
        help="Executa uma única verificação na caixa de e-mail e processa mensagens pendentes."
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=EMAIL_POLL_INTERVAL,
        help="Intervalo em segundos para checagem da caixa postal no modo contínuo."
    )

    args = parser.parse_args()

    if args.email_trigger or TRIGGER_MODE.lower() == "email":
        logger.info("[MAIN] Modo Trigger por E-mail ativado (monitoramento contínuo).")
        servico = EmailTriggerService()
        servico.iniciar_monitoramento(intervalo_segundos=args.interval)
        return 0

    if args.email_check:
        logger.info("[MAIN] Modo Trigger por E-mail ativado (verificação única).")
        servico = EmailTriggerService()
        total = servico.verificar_e_processar()
        logger.info(f"[MAIN] Total de e-mails processados: {total}")
        return 0

    # Modo padrão: execução por diretório local
    return executar_pipeline_hyperautomation()


if __name__ == "__main__":
    sys.exit(main())
