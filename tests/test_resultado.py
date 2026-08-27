"""
Testes Unitários para a Etapa 6 - Geração de Resultados e Relatórios.
Responsável: Membro 3
"""

from unittest.mock import patch, MagicMock
import pytest
import pandas as pd
from src.logger import AuditLogger
from src.etapa6_resultado import (
    load_ranking_data,
    generate_html_report,
    gerar_resultado_final
)


class TestLoadRankingData:
    """Testes para leitura de dados da planilha de ranking."""

    def test_load_ranking_data_file_not_found(self):
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(FileNotFoundError):
                load_ranking_data("arquivo_inexistente.xlsx")

    @patch("openpyxl.load_workbook")
    @patch("pathlib.Path.exists", return_value=True)
    def test_load_ranking_data_success(self, mock_exists, mock_load_wb):
        mock_rows = [
            (1, "Fornecedor Alpha", 0.95, "ATIVO", "Ótimo prazo"),
            (2, "Fornecedor Beta", 0.80, "BLOQUEADO", "Restrição de Compliance"),
            (None, None, None, None, None),  # Linha totalmente vazia
            (3, "Fornecedor Gamma", None, "ATIVO", None)  # Nota None
        ]

        mock_ws = MagicMock()
        mock_ws.iter_rows.return_value = mock_rows

        mock_wb = MagicMock()
        mock_wb.active = mock_ws
        mock_load_wb.return_value = mock_wb

        result = load_ranking_data()

        assert len(result) == 3  # Linha vazia ignorada
        assert result[0]["fornecedor"] == "Fornecedor Alpha"
        assert result[0]["nota_final"] == 0.95
        assert result[0]["status"] == "ATIVO"

        # Bloqueado deve ter nota '-'
        assert result[1]["fornecedor"] == "Fornecedor Beta"
        assert result[1]["nota_final"] == "-"
        assert result[1]["status"] == "BLOQUEADO"

        # Fornecedor sem nota deve ter '-'
        assert result[2]["nota_final"] == "-"
        assert result[2]["observacao"] == "Sem observações"


class TestGenerateHtmlReport:
    """Testes para geração do template HTML Jinja2."""

    @patch("jinja2.Environment.get_template")
    @patch("builtins.open", new_callable=MagicMock)
    def test_generate_html_report_metrics(self, mock_open, mock_get_template):
        sample_data = [
            {"posicao": 1, "fornecedor": "Fornecedor A", "nota_final": 0.98, "status": "ATIVO", "observacao": ""},
            {"posicao": 2, "fornecedor": "Fornecedor B", "nota_final": 0.85, "status": "ATIVO", "observacao": ""},
            {"posicao": "-", "fornecedor": "Fornecedor C", "nota_final": "-", "status": "BLOQUEADO", "observacao": ""},
            {"posicao": "-", "fornecedor": "Fornecedor D", "nota_final": "-", "status": "REJEITADO", "observacao": ""}
        ]

        mock_template = MagicMock()
        mock_get_template.return_value = mock_template

        generate_html_report(sample_data, output_file="relatorio_teste.html")

        mock_template.render.assert_called_once()
        render_kwargs = mock_template.render.call_args.kwargs

        assert render_kwargs["total_suppliers"] == 4
        assert render_kwargs["approved_count"] == 2
        assert render_kwargs["blocked_count"] == 2
        assert render_kwargs["best_supplier"]["fornecedor"] == "Fornecedor A"

    @patch("jinja2.Environment.get_template")
    @patch("builtins.open", new_callable=MagicMock)
    def test_generate_html_report_no_active_suppliers(self, mock_open, mock_get_template):
        sample_data = [
            {"posicao": "-", "fornecedor": "Fornecedor A", "nota_final": "-", "status": "BLOQUEADO", "observacao": ""},
            {"posicao": "-", "fornecedor": "Fornecedor B", "nota_final": "-", "status": "BLOCKED", "observacao": ""}
        ]

        mock_template = MagicMock()
        mock_get_template.return_value = mock_template

        generate_html_report(sample_data, output_file="relatorio_teste.html")

        render_kwargs = mock_template.render.call_args.kwargs
        assert render_kwargs["approved_count"] == 0
        assert render_kwargs["blocked_count"] == 2
        assert render_kwargs["best_supplier"] is None


class TestGerarResultadoFinalIntegrado:
    """Testes integrados da função gerar_resultado_final."""

    def test_gerar_resultado_final_completo(self, tmp_path):
        audit = AuditLogger()
        df_ranking = pd.DataFrame([
            {
                "Posicao": 1, "Fornecedor": "Fornecedor B", "Nota_Final": 0.85,
                "Status": "ATIVO", "Observacao": "Proposta válida."
            },
            {
                "Posicao": 2, "Fornecedor": "Fornecedor A", "Nota_Final": 0.72,
                "Status": "ATIVO", "Observacao": "Proposta válida."
            },
        ])
        propostas_rejeitadas = [
            {
                "Fornecedor": "Fornecedor D",
                "Observacao": "Custo deve ser maior que zero.",
                "Status": "REJEITADO"
            }
        ]
        out_excel = tmp_path / "ranking_teste.xlsx"

        df_resultado = gerar_resultado_final(
            df_ranking=df_ranking,
            propostas_rejeitadas=propostas_rejeitadas,
            output_path=out_excel,
            audit=audit
        )

        assert len(df_resultado) == 3
        assert list(df_resultado["Fornecedor"]) == ["Fornecedor B", "Fornecedor A", "Fornecedor D"]
        assert df_resultado.iloc[0]["Status"] == "ATIVO"
        assert df_resultado.iloc[2]["Status"] == "BLOQUEADO"
        assert out_excel.exists()

        # Verifica persistência do arquivo HTML
        out_html = tmp_path / "relatorio_ranking.html"
        assert out_html.exists()
