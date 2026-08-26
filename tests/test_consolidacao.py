"""
Testes Unitários para a Etapa 4 - Consolidação de Propostas Válidas.
Responsável: Membro 2
"""

from src.etapa4_consolidacao import (
    consolidar_propostas,
    consolidar_propostas_validas,
)


class TestConsolidacaoPropostas:
    """Testes para a consolidação de dados da Etapa 4."""

    def test_consolidar_propostas_validas(self):
        propostas_validas = [
            {
                "Fornecedor": "Fornecedor A",
                "Produto": "Compressor",
                "Custo": 120.0,
                "Prazo_Dias": 15,
                "Capacidade": 1000,
                "Qualidade": 95.0,
                "Status": "VALIDO",
                "Observacao": "Proposta válida.",
                "campo_extra_ignorado": "teste",
            },
            {
                "Fornecedor": "Fornecedor B",
                "Produto": "Compressor",
                "Custo": 110.0,
                "Prazo_Dias": 10,
                "Capacidade": 1200,
                "Qualidade": 90.0,
                "Status": "VALIDO",
                "Observacao": "Proposta válida.",
            },
        ]

        resultado = consolidar_propostas(propostas_validas)

        assert len(resultado) == 2
        for item in resultado:
            assert "Fornecedor" in item
            assert "Produto" in item
            assert "Custo" in item
            assert "Prazo_Dias" in item
            assert "Capacidade" in item
            assert "Qualidade" in item
            assert "Status" in item
            assert "Observacao" in item
            assert "campo_extra_ignorado" not in item
            assert item["Status"] == "VALIDO"

    def test_consolidar_propostas_alias(self):
        # Garante compatibilidade do alias consolidar_propostas_validas
        propostas = [
            {
                "Fornecedor": "Fornecedor C",
                "Produto": "Compressor",
                "Custo": 115.0,
                "Prazo_Dias": 12,
                "Capacidade": 1100,
                "Qualidade": 92.0,
                "Status": "VALIDO",
                "Observacao": "Proposta válida.",
            }
        ]
        res1 = consolidar_propostas(propostas)
        res2 = consolidar_propostas_validas(propostas)
        assert res1 == res2

    def test_consolidar_lista_vazia(self):
        resultado = consolidar_propostas([])
        assert resultado == []

    def test_consolidar_preenche_status_e_observacao_padrao(self):
        propostas = [
            {
                "Fornecedor": "Fornecedor A",
                "Produto": "Compressor",
                "Custo": 120.0,
                "Prazo_Dias": 15,
                "Capacidade": 1000,
                "Qualidade": 95.0,
                "Status": None,
                "Observacao": None,
            }
        ]
        resultado = consolidar_propostas(propostas)
        assert resultado[0]["Status"] == "VALIDO"
        assert resultado[0]["Observacao"] == "Proposta válida."
