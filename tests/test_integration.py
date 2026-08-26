"""
Testes de Integração e Regressão para as Etapas 1 (Coleta) e 2 (Leitura).
Responsável: Membro 1 (Sannyer)
"""

import json

from src.config import (
    PROPOSTAS_DIR,
    WEB_PANEL_LOCAL_PATH,
    CRITERIOS_PATH,
    MODELO_RANKING_PATH,
    LOGS_DIR
)
from src.logger import AuditLogger
from src.etapa1_coleta import coletar_propostas_e_status_web
from src.etapa2_leitura import (
    ler_todas_propostas,
    ler_criterios,
    ler_modelo_ranking
)
from src.main import executar_pipeline_hyperautomation


class TestIntegracaoEtapa1EEtapa2:
    """Testes integrados validando a interoperabilidade entre Coleta e Leitura."""

    def test_fluxo_integrado_coleta_e_leitura_dados_reais(self):
        audit = AuditLogger()

        # 1. Executa Etapa 1 (Coleta)
        arquivos, status_web = coletar_propostas_e_status_web(
            propostas_dir=PROPOSTAS_DIR,
            local_path=WEB_PANEL_LOCAL_PATH,
            audit=audit
        )

        assert len(arquivos) == 4
        assert len(status_web) > 0
        assert status_web.get("Fornecedor A") == "Ativo"
        assert status_web.get("Fornecedor D") == "Bloqueado"

        # 2. Executa Etapa 2 (Leitura)
        propostas_brutas = ler_todas_propostas(arquivos=arquivos, audit=audit)
        df_criterios = ler_criterios(CRITERIOS_PATH)
        df_modelo = ler_modelo_ranking(MODELO_RANKING_PATH)

        # Validações dos dados lidos
        assert len(propostas_brutas) == 4
        fornecedores_lidos = {p["Fornecedor"] for p in propostas_brutas}
        assert fornecedores_lidos == {"Fornecedor A", "Fornecedor B", "Fornecedor C", "Fornecedor D"}

        # Validação de tipos e campos obrigatórios
        for p in propostas_brutas:
            assert "Fornecedor" in p
            assert "Produto" in p
            assert "Custo" in p
            assert "Prazo_Dias" in p
            assert "Capacidade" in p
            assert "Qualidade" in p
            assert "_arquivo" in p

        # Validação dos critérios
        assert len(df_criterios) == 4
        assert abs(df_criterios["Peso"].sum() - 1.0) < 1e-4

        # Validação do modelo de ranking
        assert list(df_modelo.columns) == ["Posicao", "Fornecedor", "Nota_Final", "Status", "Observacao"]

        # Validação da auditoria SOX
        resumo = audit.salvar_auditoria()
        assert resumo["total_recebidas"] == 4
        assert len(resumo["propostas_recebidas"]) == 4

        # Confirma existência física do arquivo de auditoria
        audit_file = LOGS_DIR / "auditoria.json"
        assert audit_file.exists()
        conteudo_audit = json.loads(audit_file.read_text(encoding="utf-8"))
        assert conteudo_audit["total_recebidas"] == 4

    def test_fluxo_integrado_etapa1_ate_etapa4(self):
        from src.etapa3_validacao import validar_todas_propostas
        from src.etapa4_consolidacao import consolidar_propostas

        audit = AuditLogger()

        # Etapa 1: Coleta
        arquivos, status_web = coletar_propostas_e_status_web(
            propostas_dir=PROPOSTAS_DIR,
            local_path=WEB_PANEL_LOCAL_PATH,
            audit=audit
        )
        assert len(arquivos) == 4

        # Etapa 2: Leitura
        propostas_brutas = ler_todas_propostas(arquivos=arquivos, audit=audit)
        assert len(propostas_brutas) == 4

        # Etapa 3: Validação
        validas, rejeitadas = validar_todas_propostas(
            propostas=propostas_brutas,
            status_web=status_web,
            audit=audit
        )
        # Fornecedores A, B, C são válidos; D tem valores negativos/inválidos e status bloqueado
        assert len(validas) == 3
        assert len(rejeitadas) == 1

        fornecedores_validos = {p["Fornecedor"] for p in validas}
        assert fornecedores_validos == {"Fornecedor A", "Fornecedor B", "Fornecedor C"}
        assert rejeitadas[0]["Fornecedor"] == "Fornecedor D"

        # Etapa 4: Consolidação
        dados_consolidados = consolidar_propostas(validas)
        assert len(dados_consolidados) == 3
        for item in dados_consolidados:
            assert item["Status"] == "VALIDO"
            assert "Observacao" in item

    def test_execucao_orquestrador_main(self):
        # Execução completa da pipeline principal via main
        codigo_retorno = executar_pipeline_hyperautomation()
        assert codigo_retorno == 0
