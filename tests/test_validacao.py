"""
Testes Unitários para a Etapa 3 - Validação de Propostas Comerciais e Status Cadastral.
Responsável: Membro 2
"""

import pytest
from src.logger import AuditLogger
from src.etapa3_validacao import (
    obter_codigo_fornecedor,
    validar_proposta_individual,
    validar_todas_propostas,
)


class TestExtracaoCodigoFornecedor:
    """Testes para a função obter_codigo_fornecedor."""

    def test_extrair_codigo_padrao(self):
        assert obter_codigo_fornecedor("Fornecedor A") == "A"
        assert obter_codigo_fornecedor("Fornecedor B") == "B"
        assert obter_codigo_fornecedor("Fornecedor Alpha") == "ALPHA"

    def test_extrair_codigo_vazio(self):
        assert obter_codigo_fornecedor("") == ""
        assert obter_codigo_fornecedor(None) == ""

    def test_extrair_codigo_apenas_letra(self):
        assert obter_codigo_fornecedor("C") == "C"


class TestValidacaoPropostaIndividual:
    """Testes para validação de dados comerciais individuais."""

    @pytest.fixture
    def proposta_valida(self):
        return {
            "Fornecedor": "Fornecedor A",
            "Produto": "Compressor",
            "Custo": 120.50,
            "Prazo_Dias": 15,
            "Capacidade": 1000,
            "Qualidade": 95.0,
        }

    def test_proposta_valida_sucesso(self, proposta_valida):
        valida, msg = validar_proposta_individual(proposta_valida)
        assert valida is True
        assert "válida" in msg.lower()

    def test_proposta_campos_obrigatorios_ausentes(self):
        proposta = {"Fornecedor": "Fornecedor A", "Custo": 100}
        valida, msg = validar_proposta_individual(proposta)
        assert valida is False
        assert "obrigatórios ausentes" in msg

    def test_proposta_fornecedor_vazio(self, proposta_valida):
        proposta_valida["Fornecedor"] = "   "
        valida, msg = validar_proposta_individual(proposta_valida)
        assert valida is False
        assert "Fornecedor não informado" in msg

    def test_proposta_produto_vazio(self, proposta_valida):
        proposta_valida["Produto"] = ""
        valida, msg = validar_proposta_individual(proposta_valida)
        assert valida is False
        assert "Produto não informado" in msg

    def test_proposta_custo_negativo_ou_zero(self, proposta_valida):
        proposta_valida["Custo"] = 0
        valida, msg = validar_proposta_individual(proposta_valida)
        assert valida is False
        assert "Custo deve ser maior que zero" in msg

        proposta_valida["Custo"] = -50.0
        valida, msg = validar_proposta_individual(proposta_valida)
        assert valida is False
        assert "Custo deve ser maior que zero" in msg

    def test_proposta_custo_nao_numerico(self, proposta_valida):
        proposta_valida["Custo"] = "invalido"
        valida, msg = validar_proposta_individual(proposta_valida)
        assert valida is False
        assert "Custo deve ser numérico" in msg

    def test_proposta_prazo_negativo_ou_zero(self, proposta_valida):
        proposta_valida["Prazo_Dias"] = 0
        valida, msg = validar_proposta_individual(proposta_valida)
        assert valida is False
        assert "Prazo_Dias deve ser maior que zero" in msg

        proposta_valida["Prazo_Dias"] = -5
        valida, msg = validar_proposta_individual(proposta_valida)
        assert valida is False
        assert "Prazo_Dias deve ser maior que zero" in msg

    def test_proposta_prazo_nao_numerico(self, proposta_valida):
        proposta_valida["Prazo_Dias"] = "abc"
        valida, msg = validar_proposta_individual(proposta_valida)
        assert valida is False
        assert "Prazo_Dias deve ser numérico" in msg

    def test_proposta_capacidade_negativa_ou_zero(self, proposta_valida):
        proposta_valida["Capacidade"] = -10
        valida, msg = validar_proposta_individual(proposta_valida)
        assert valida is False
        assert "Capacidade deve ser maior que zero" in msg

    def test_proposta_capacidade_nao_numerica(self, proposta_valida):
        proposta_valida["Capacidade"] = "xyz"
        valida, msg = validar_proposta_individual(proposta_valida)
        assert valida is False
        assert "Capacidade deve ser numérica" in msg

    def test_proposta_qualidade_fora_do_range(self, proposta_valida):
        proposta_valida["Qualidade"] = 105
        valida, msg = validar_proposta_individual(proposta_valida)
        assert valida is False
        assert "Qualidade deve estar entre 0 e 100" in msg

        proposta_valida["Qualidade"] = -1
        valida, msg = validar_proposta_individual(proposta_valida)
        assert valida is False
        assert "Qualidade deve estar entre 0 e 100" in msg

    def test_proposta_qualidade_nao_numerica(self, proposta_valida):
        proposta_valida["Qualidade"] = "alta"
        valida, msg = validar_proposta_individual(proposta_valida)
        assert valida is False
        assert "Qualidade deve ser numérica" in msg


class TestValidacaoTodasPropostas:
    """Testes integrados da validação de lote com verificação de status web."""

    def test_validar_lote_misto(self):
        audit = AuditLogger()
        propostas = [
            {
                "Fornecedor": "Fornecedor A",
                "Produto": "Compressor",
                "Custo": 120.0,
                "Prazo_Dias": 15,
                "Capacidade": 1000,
                "Qualidade": 95.0,
            },
            {
                "Fornecedor": "Fornecedor B",
                "Produto": "Compressor",
                "Custo": 110.0,
                "Prazo_Dias": 10,
                "Capacidade": 1200,
                "Qualidade": 90.0,
            },
            {
                "Fornecedor": "Fornecedor D",
                "Produto": "Compressor",
                "Custo": -50.0,
                "Prazo_Dias": 0,
                "Capacidade": 0,
                "Qualidade": 120.0,
            },
        ]
        status_web = {
            "A": "Ativo",
            "B": "Ativo",
            "D": "Bloqueado",
        }

        validas, rejeitadas = validar_todas_propostas(propostas, status_web, audit)

        assert len(validas) == 2
        assert len(rejeitadas) == 1

        fornecedores_validos = [p["Fornecedor"] for p in validas]
        assert "Fornecedor A" in fornecedores_validos
        assert "Fornecedor B" in fornecedores_validos
        assert validas[0]["Status"] == "VALIDO"

        rejeitada_d = rejeitadas[0]
        assert rejeitada_d["Fornecedor"] == "Fornecedor D"
        assert rejeitada_d["Status"] == "REJEITADO"
        assert "não está habilitado" in rejeitada_d["Observacao"]

        # Verifica persistência na auditoria
        assert len(audit.propostas_validas) == 2
        assert len(audit.propostas_rejeitadas) == 1

    def test_fornecedor_valido_comercialmente_mas_bloqueado_web(self):
        audit = AuditLogger()
        propostas = [
            {
                "Fornecedor": "Fornecedor C",
                "Produto": "Compressor",
                "Custo": 100.0,
                "Prazo_Dias": 12,
                "Capacidade": 900,
                "Qualidade": 88.0,
            }
        ]
        status_web = {"C": "Bloqueado"}

        validas, rejeitadas = validar_todas_propostas(propostas, status_web, audit)
        assert len(validas) == 0
        assert len(rejeitadas) == 1
        assert "não está habilitado" in rejeitadas[0]["Observacao"]

    def test_fornecedor_nao_encontrado_no_status_web(self):
        audit = AuditLogger()
        propostas = [
            {
                "Fornecedor": "Fornecedor X",
                "Produto": "Compressor",
                "Custo": 100.0,
                "Prazo_Dias": 12,
                "Capacidade": 900,
                "Qualidade": 88.0,
            }
        ]
        status_web = {"A": "Ativo"}

        validas, rejeitadas = validar_todas_propostas(propostas, status_web, audit)
        assert len(validas) == 0
        assert len(rejeitadas) == 1
        assert "não está habilitado" in rejeitadas[0]["Observacao"]
