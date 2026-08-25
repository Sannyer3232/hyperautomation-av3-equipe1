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

from src.config import (
    PROPOSTAS_DIR,
    CRITERIOS_PATH,
    OUTPUT_RANKING_PATH
)
from src.logger import logger, AuditLogger
from src.etapa1_coleta import coletar_propostas_e_status_web
from src.etapa2_leitura import ler_todas_propostas, ler_criterios
from src.etapa3_validacao import validar_todas_propostas
from src.etapa4_consolidacao import consolidar_propostas
from src.etapa5_ranking import calcular_ranking_ponderado
from src.etapa6_resultado import gerar_resultado_final


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

        # ETAPA 3: VALIDAÇÃO (Membro 2)
        propostas_validas, propostas_rejeitadas = validar_todas_propostas(
            propostas=propostas_brutas,
            status_web=status_web,
            audit=audit
        )

        # ETAPA 4: CONSOLIDAÇÃO (Membro 2)
        dados_consolidados = consolidar_propostas(propostas_validas)

        # ETAPA 5: RANKING (Membro 3)
        df_ranking = calcular_ranking_ponderado(
            propostas=dados_consolidados,
            df_criterios=df_criterios,
            audit=audit
        )

        # ETAPA 6: RESULTADO (Membro 3)
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


if __name__ == "__main__":
    sys.exit(executar_pipeline_hyperautomation())
