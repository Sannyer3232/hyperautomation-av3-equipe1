"""
Testes Unitários para a Etapa 5 - Ranking Ponderado MCDA.
Responsável: Membro 3
"""

import pandas as pd
from src.logger import AuditLogger
from src.etapa5_ranking import (
    normalize_status,
    normalize_inverse_value,
    normalize_direct_value,
    get_extrema,
    calculate_individual_score,
    calculate_ranking,
    calcular_ranking_ponderado,
    extrair_pesos_criterios,
)


class TestNormalizacoesERegrasMatematicas:
    """Testes para funções de normalização e scoring Min-Max."""

    def test_normalize_status(self):
        assert normalize_status("ativo") == "ATIVO"
        assert normalize_status(" BLOQUEADO ") == "BLOQUEADO"
        assert normalize_status("inativo") == "BLOQUEADO"
        assert normalize_status("blocked") == "BLOQUEADO"
        assert normalize_status("rejeitado") == "BLOQUEADO"
        assert normalize_status(None) == "ATIVO"
        assert normalize_status("") == "ATIVO"

    def test_normalize_inverse_value(self):
        # Menor valor deve receber score 1.0 (melhor custo/menor prazo)
        assert normalize_inverse_value(100, 100, 200) == 1.0
        # Maior valor deve receber score 0.0 (pior custo/maior prazo)
        assert normalize_inverse_value(200, 100, 200) == 0.0
        # Valor intermediário proporcional
        assert normalize_inverse_value(150, 100, 200) == 0.5
        # Trata caso de min_val == max_val sem divisão por zero
        assert normalize_inverse_value(100, 100, 100) == 1.0

    def test_normalize_direct_value(self):
        # Maior valor deve receber score 1.0 (maior capacidade/maior qualidade)
        assert normalize_direct_value(200, 100, 200) == 1.0
        # Menor valor deve receber score 0.0
        assert normalize_direct_value(100, 100, 200) == 0.0
        # Valor intermediário proporcional
        assert normalize_direct_value(150, 100, 200) == 0.5
        # Trata caso de min_val == max_val sem divisão por zero
        assert normalize_direct_value(100, 100, 100) == 1.0

    def test_get_extrema(self):
        suppliers = [
            {"custo": 100, "prazo_dias": 5, "capacidade": 500, "qualidade": 95},
            {"custo": 120, "prazo_dias": 3, "capacidade": 300, "qualidade": 98},
        ]
        extrema = get_extrema(suppliers)
        assert extrema is not None
        assert extrema["custo"] == (100, 120)
        assert extrema["prazo"] == (3, 5)
        assert extrema["capacidade"] == (300, 500)
        assert extrema["qualidade"] == (95, 98)

    def test_get_extrema_lista_vazia(self):
        assert get_extrema([]) is None


class TestCalculoScoreERanking:
    """Testes para o cálculo de notas individuais e ordenação do ranking."""

    def test_calculate_individual_score(self):
        weights = {"custo": 0.4, "prazo": 0.25, "capacidade": 0.2, "qualidade": 0.15}
        extrema = {
            "custo": (100.0, 200.0),
            "prazo": (2.0, 10.0),
            "capacidade": (500.0, 1000.0),
            "qualidade": (80.0, 100.0),
        }
        # Fornecedor com os melhores valores em tudo (Custo 100, Prazo 2, Capacidade 1000, Qualidade 100)
        best_supplier = {"custo": 100, "prazo_dias": 2, "capacidade": 1000, "qualidade": 100}
        score, parciais = calculate_individual_score(best_supplier, weights, extrema)
        assert abs(score - 1.0) < 1e-4
        assert parciais["score_custo"] == 1.0
        assert parciais["score_prazo"] == 1.0
        assert parciais["score_capacidade"] == 1.0
        assert parciais["score_qualidade"] == 1.0

    def test_calculate_ranking_com_bloqueados(self):
        suppliers = [
            {
                "fornecedor": "A", "custo": 100, "prazo_dias": 5,
                "capacidade": 500, "qualidade": 95, "status": "ativo"
            },
            {
                "fornecedor": "B", "custo": 80, "prazo_dias": 2,
                "capacidade": 600, "qualidade": 90, "status": "BLOQUEADO"
            },
            {
                "fornecedor": "C", "custo": 120, "prazo_dias": 3,
                "capacidade": 300, "qualidade": 98, "status": "ativo"
            },
        ]

        ranking = calculate_ranking(suppliers)

        assert len(ranking) == 3
        # Ativos devem vir primeiro
        assert ranking[0]["status_normalizado"] == "ATIVO"
        assert ranking[1]["status_normalizado"] == "ATIVO"
        assert ranking[2]["status_normalizado"] == "BLOQUEADO"

        # Bloqueados devem ter score None
        assert ranking[2]["score"] is None

        # Ordenação decrescente de nota
        assert ranking[0]["score"] >= ranking[1]["score"]

    def test_extrair_pesos_criterios(self):
        df_criterios = pd.DataFrame([
            {"Criterio": "Custo", "Peso": 0.40},
            {"Criterio": "Prazo", "Peso": 0.30},
            {"Criterio": "Capacidade", "Peso": 0.20},
            {"Criterio": "Qualidade", "Peso": 0.10},
        ])
        pesos = extrair_pesos_criterios(df_criterios)
        assert pesos["custo"] == 0.40
        assert pesos["prazo"] == 0.30
        assert pesos["capacidade"] == 0.20
        assert pesos["qualidade"] == 0.10


class TestCalcularRankingPonderadoIntegrado:
    """Testes integrados da função calcular_ranking_ponderado."""

    def test_calcular_ranking_ponderado_sucesso(self):
        audit = AuditLogger()
        propostas_consolidadas = [
            {
                "Fornecedor": "Fornecedor A",
                "Produto": "Compressor",
                "Custo": 120.0,
                "Prazo_Dias": 15,
                "Capacidade": 1000,
                "Qualidade": 95.0,
                "Status": "VALIDO",
                "Observacao": "Proposta válida.",
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
            {
                "Fornecedor": "Fornecedor C",
                "Produto": "Compressor",
                "Custo": 130.0,
                "Prazo_Dias": 18,
                "Capacidade": 800,
                "Qualidade": 98.0,
                "Status": "VALIDO",
                "Observacao": "Proposta válida.",
            },
        ]

        df_ranking = calcular_ranking_ponderado(
            propostas=propostas_consolidadas,
            audit=audit
        )

        assert len(df_ranking) == 3
        assert list(df_ranking.columns) == ["Posicao", "Fornecedor", "Nota_Final", "Status", "Observacao"]
        assert list(df_ranking["Posicao"]) == [1, 2, 3]
        # Todos possuem nota válida
        assert df_ranking["Nota_Final"].notna().all()
        # Primeiro lugar tem maior nota
        assert df_ranking.iloc[0]["Nota_Final"] >= df_ranking.iloc[1]["Nota_Final"]
        assert df_ranking.iloc[1]["Nota_Final"] >= df_ranking.iloc[2]["Nota_Final"]

        # Auditoria registrada
        assert len(audit.calculos_realizados) == 3
        assert len(audit.ranking_final) == 3
