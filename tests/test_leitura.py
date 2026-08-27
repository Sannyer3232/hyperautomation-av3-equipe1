"""
Testes Unitários para a Etapa 2: Leitura e Extração de Propostas e Critérios.
Responsável: Membro 1 (Sannyer)
"""

import pandas as pd
from pathlib import Path
from unittest.mock import patch

from src.config import (
    PROPOSTAS_DIR,
    CRITERIOS_PATH,
    MODELO_RANKING_PATH
)
from src.logger import AuditLogger
from src.etapa2_leitura.reader import (
    ler_proposta,
    ler_todas_propostas,
    ler_criterios,
    ler_modelo_ranking,
    normalizar_nome_coluna
)


class TestNormalizacaoColunas:
    """Testes de normalização e tolerância para nomes de cabeçalhos."""

    def test_normalizacao_fornecedor(self):
        assert normalizar_nome_coluna("fornecedor") == "Fornecedor"
        assert normalizar_nome_coluna(" EMPRESA ") == "Fornecedor"
        assert normalizar_nome_coluna("supplier") == "Fornecedor"

    def test_normalizacao_custo(self):
        assert normalizar_nome_coluna("custo") == "Custo"
        assert normalizar_nome_coluna("preco") == "Custo"
        assert normalizar_nome_coluna("preco_unitario") == "Custo"
        assert normalizar_nome_coluna("valor") == "Custo"
        assert normalizar_nome_coluna("Price") == "Custo"

    def test_normalizacao_prazo(self):
        assert normalizar_nome_coluna("prazo_dias") == "Prazo_Dias"
        assert normalizar_nome_coluna("Prazo") == "Prazo_Dias"
        assert normalizar_nome_coluna("lead_time") == "Prazo_Dias"
        assert normalizar_nome_coluna("lead time") == "Prazo_Dias"

    def test_normalizacao_capacidade_e_qualidade(self):
        assert normalizar_nome_coluna("capacidade") == "Capacidade"
        assert normalizar_nome_coluna("capacidade_mensal") == "Capacidade"
        assert normalizar_nome_coluna("qualidade") == "Qualidade"
        assert normalizar_nome_coluna("score_qualidade") == "Qualidade"

    def test_coluna_desconhecida(self):
        assert normalizar_nome_coluna("Observacoes_Extras") == "Observacoes_Extras"


class TestLeituraPropostaIndividual:
    """Testes de leitura para arquivos individuais nos formatos XLSX e CSV."""

    def test_ler_proposta_excel_fornecedor_a(self):
        arq = PROPOSTAS_DIR / "proposta_fornecedor_A.xlsx"
        registros = ler_proposta(arq)
        assert len(registros) == 1
        reg = registros[0]
        assert reg["Fornecedor"] == "Fornecedor A"
        assert reg["Produto"] == "Produto 01"
        assert float(reg["Custo"]) == 100.0
        assert int(reg["Prazo_Dias"]) == 5
        assert int(reg["Capacidade"]) == 500
        assert int(reg["Qualidade"]) == 95
        assert reg["_arquivo"] == "proposta_fornecedor_A.xlsx"

    def test_ler_proposta_csv_fornecedor_b(self):
        arq = PROPOSTAS_DIR / "proposta_fornecedor_B.csv"
        registros = ler_proposta(arq)
        assert len(registros) == 1
        reg = registros[0]
        assert reg["Fornecedor"] == "Fornecedor B"
        assert reg["Produto"] == "Produto 01"
        assert float(reg["Custo"]) == 90.0
        assert int(reg["Prazo_Dias"]) == 8
        assert int(reg["Capacidade"]) == 700
        assert int(reg["Qualidade"]) == 90
        assert reg["_arquivo"] == "proposta_fornecedor_B.csv"

    def test_ler_proposta_invalida_fornecedor_d(self):
        # Lê os dados do Fornecedor D mesmo sendo negativos (para serem avaliados na Etapa 3)
        arq = PROPOSTAS_DIR / "proposta_invalida_fornecedor_D.xlsx"
        registros = ler_proposta(arq)
        assert len(registros) == 1
        reg = registros[0]
        assert reg["Fornecedor"] == "Fornecedor D"
        assert float(reg["Custo"]) == -50.0
        assert int(reg["Prazo_Dias"]) == -2
        assert int(reg["Capacidade"]) == -100
        assert int(reg["Qualidade"]) == 85

    def test_ler_proposta_csv_delimitador_virgula(self, tmp_path):
        csv_file = tmp_path / "proposta_virgula.csv"
        csv_file.write_text(
            "Fornecedor,Produto,Custo,Prazo_Dias,Capacidade,Qualidade\nFornecedor X,Item 1,120,6,600,92\n",
            encoding="utf-8"
        )
        registros = ler_proposta(csv_file)
        assert len(registros) == 1
        assert registros[0]["Fornecedor"] == "Fornecedor X"
        assert float(registros[0]["Custo"]) == 120.0

    def test_ler_proposta_arquivo_inexistente(self):
        registros = ler_proposta("caminho_inexistente.xlsx")
        assert registros == []

    def test_ler_proposta_formato_nao_suportado(self, tmp_path):
        pdf_file = tmp_path / "proposta.pdf"
        pdf_file.write_text("conteudo binario simulado", encoding="utf-8")
        registros = ler_proposta(pdf_file)
        assert registros == []

    def test_ler_proposta_arquivo_vazio(self, tmp_path):
        vazio_csv = tmp_path / "vazio.csv"
        vazio_csv.write_text("", encoding="utf-8")
        registros = ler_proposta(vazio_csv)
        assert registros == []

    def test_ler_proposta_excel_sem_linhas(self, tmp_path):
        vazio_xlsx = tmp_path / "vazio_linhas.xlsx"
        df_vazio = pd.DataFrame(columns=["Fornecedor", "Produto", "Custo", "Prazo_Dias", "Capacidade", "Qualidade"])
        df_vazio.to_excel(vazio_xlsx, index=False)
        registros = ler_proposta(vazio_xlsx)
        assert registros == []

    def test_ler_proposta_arquivo_corrompido(self, tmp_path):
        corrompido_xlsx = tmp_path / "corrompido.xlsx"
        corrompido_xlsx.write_text("arquivo corrompido que nao e zip/excel", encoding="utf-8")
        registros = ler_proposta(corrompido_xlsx)
        assert registros == []


class TestLeituraTodasPropostas:
    """Testes de processamento em lote com rastreabilidade."""

    def test_ler_todas_propostas_conjunto_real(self):
        audit = AuditLogger()
        arquivos = [
            PROPOSTAS_DIR / "proposta_fornecedor_A.xlsx",
            PROPOSTAS_DIR / "proposta_fornecedor_B.csv",
            PROPOSTAS_DIR / "proposta_fornecedor_C.xlsx",
            PROPOSTAS_DIR / "proposta_invalida_fornecedor_D.xlsx"
        ]
        todas = ler_todas_propostas(arquivos, audit=audit)
        assert len(todas) == 4
        fornecedores = [p["Fornecedor"] for p in todas]
        assert "Fornecedor A" in fornecedores
        assert "Fornecedor B" in fornecedores
        assert "Fornecedor C" in fornecedores
        assert "Fornecedor D" in fornecedores

    def test_ler_todas_propostas_lista_vazia(self):
        audit = AuditLogger()
        todas = ler_todas_propostas([], audit=audit)
        assert todas == []
        assert len(audit.erros) == 1
        assert audit.erros[0]["etapa"] == "Leitura"

    def test_ler_todas_propostas_com_arquivo_invalido(self, tmp_path):
        audit = AuditLogger()
        arq_valido = PROPOSTAS_DIR / "proposta_fornecedor_A.xlsx"
        arq_invalido = tmp_path / "vazio.csv"
        arq_invalido.write_text("", encoding="utf-8")

        todas = ler_todas_propostas([arq_valido, arq_invalido], audit=audit)
        assert len(todas) == 1
        assert todas[0]["Fornecedor"] == "Fornecedor A"
        assert len(audit.erros) == 1

    def test_ler_todas_propostas_com_excecao_lancada(self):
        audit = AuditLogger()
        with patch("src.etapa2_leitura.reader.ler_proposta", side_effect=RuntimeError("Erro inesperado de IO")):
            todas = ler_todas_propostas(["arquivo_qualquer.xlsx"], audit=audit)
            assert todas == []
            assert len(audit.erros) == 1
            assert "Erro inesperado de IO" in audit.erros[0]["mensagem"]


class TestLeituraCriterios:
    """Testes para o carregador de critérios de ranking e fallback."""

    def test_ler_criterios_arquivo_real(self):
        df_criterios = ler_criterios(CRITERIOS_PATH)
        assert not df_criterios.empty
        assert "Criterio" in df_criterios.columns
        assert "Direcao" in df_criterios.columns
        assert "Peso" in df_criterios.columns
        assert len(df_criterios) == 4

        # Validar soma dos pesos = 1.0 (100%)
        soma_pesos = df_criterios["Peso"].sum()
        assert abs(soma_pesos - 1.0) < 1e-4

    def test_ler_criterios_fallback_arquivo_inexistente(self):
        caminho_inexistente = Path("criterios_nao_existe_123.xlsx")
        df_criterios = ler_criterios(caminho_inexistente)
        assert not df_criterios.empty
        assert len(df_criterios) == 4
        assert abs(df_criterios["Peso"].sum() - 1.0) < 1e-4

    def test_ler_criterios_fallback_arquivo_invalido(self, tmp_path):
        arq_corrompido = tmp_path / "criterios_corrompido.xlsx"
        arq_corrompido.write_text("nao e excel", encoding="utf-8")
        df_criterios = ler_criterios(arq_corrompido)
        assert not df_criterios.empty
        assert "Criterio" in df_criterios.columns
        assert abs(df_criterios["Peso"].sum() - 1.0) < 1e-4

    def test_ler_criterios_estrutura_divergente(self, tmp_path):
        arq_divergente = tmp_path / "divergente.xlsx"
        df_inv = pd.DataFrame({"Nome": ["A"], "Valor": [10]})
        df_inv.to_excel(arq_divergente, index=False)

        df_criterios = ler_criterios(arq_divergente)
        assert not df_criterios.empty
        assert "Criterio" in df_criterios.columns
        assert "Peso" in df_criterios.columns


class TestLeituraModeloRanking:
    """Testes para carregamento do template modelo_ranking.xlsx."""

    def test_ler_modelo_ranking_arquivo_real(self):
        df_modelo = ler_modelo_ranking(MODELO_RANKING_PATH)
        assert "Posicao" in df_modelo.columns
        assert "Fornecedor" in df_modelo.columns
        assert "Nota_Final" in df_modelo.columns
        assert "Status" in df_modelo.columns
        assert "Observacao" in df_modelo.columns

    def test_ler_modelo_ranking_fallback_inexistente(self):
        caminho_inexistente = Path("modelo_nao_existe.xlsx")
        df_modelo = ler_modelo_ranking(caminho_inexistente)
        assert "Posicao" in df_modelo.columns
        assert "Fornecedor" in df_modelo.columns
        assert "Nota_Final" in df_modelo.columns
        assert "Status" in df_modelo.columns
        assert "Observacao" in df_modelo.columns

    def test_ler_modelo_ranking_fallback_corrompido(self, tmp_path):
        arq_corrompido = tmp_path / "modelo_corrompido.xlsx"
        arq_corrompido.write_text("corrompido", encoding="utf-8")
        df_modelo = ler_modelo_ranking(arq_corrompido)
        assert "Posicao" in df_modelo.columns
        assert "Fornecedor" in df_modelo.columns
