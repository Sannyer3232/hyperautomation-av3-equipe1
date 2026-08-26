import os
import pytest
from unittest.mock import patch, MagicMock
from result import load_ranking_data, generate_html_report  # Altere 'report' para o nome do seu arquivo Python sem o .py


# ==========================================
# TESTES DE NAVEGAÇÃO E LEITURA (load_ranking_data)
# ==========================================

def test_load_ranking_data_file_not_found():
    """Garante que raise FileNotFoundError ocorre quando a planilha não é encontrada."""
    with patch("os.path.exists", return_value=False):
        with pytest.raises(FileNotFoundError):
            load_ranking_data("arquivo_inexistente.xlsx")


@patch("openpyxl.load_workbook")
@patch("os.path.exists", return_value=True)
def test_load_ranking_data_success(mock_exists, mock_load_wb):
    """Testa a leitura da planilha tratando valores ativos, bloqueados e linhas vazias."""
    # Simula linhas do Excel: (posicao, fornecedor, nota_final, status, observacao)
    mock_rows = [
        (1, "Fornecedor Alpha", 9.5, "ATIVO", "Ótimo prazo"),
        (2, "Fornecedor Beta", 8.0, "BLOQUEADO", "Restrição de Compliance"),
        (None, None, None, None, None),  # Linha totalmente vazia
        (3, "Fornecedor Gamma", None, "ATIVO", None)  # Nota None
    ]

    mock_ws = MagicMock()
    mock_ws.iter_rows.return_value = mock_rows
    
    mock_wb = MagicMock()
    mock_wb.active = mock_ws
    mock_load_wb.return_value = mock_wb

    result = load_ranking_data()

    assert len(result) == 3  # A linha totalmente vazia deve ser ignorada
    
    # Valida o primeiro fornecedor (Ativo)
    assert result[0]["fornecedor"] == "Fornecedor Alpha"
    assert result[0]["nota_final"] == 9.5
    assert result[0]["status"] == "ATIVO"

    # Valida o fornecedor bloqueado (nota deve virar '-')
    assert result[1]["fornecedor"] == "Fornecedor Beta"
    assert result[1]["nota_final"] == "-"
    assert result[1]["status"] == "BLOQUEADO"

    # Valida o fornecedor sem nota (nota deve virar '-')
    assert result[2]["nota_final"] == "-"
    assert result[2]["observacao"] == "Sem observações"


# ==========================================
# TESTES DE GERAÇÃO DE RELATÓRIO (generate_html_report)
# ==========================================

@patch("jinja2.Environment.get_template")
@patch("builtins.open", new_callable=MagicMock)
@patch("os.makedirs")
def test_generate_html_report_metrics(mock_makedirs, mock_open, mock_get_template):
    """Verifica se os KPIs (totais, ativos, bloqueados, melhor fornecedor) são passados corretamente ao Jinja2."""
    sample_data = [
        {"posicao": 1, "fornecedor": "Fornecedor A", "nota_final": 9.8, "status": "ATIVO", "observacao": ""},
        {"posicao": 2, "fornecedor": "Fornecedor B", "nota_final": 8.5, "status": "ATIVO", "observacao": ""},
        {"posicao": 3, "fornecedor": "Fornecedor C", "nota_final": "-", "status": "BLOQUEADO", "observacao": ""},
        {"posicao": 4, "fornecedor": "Fornecedor D", "nota_final": "-", "status": "INATIVO", "observacao": ""}
    ]

    mock_template = MagicMock()
    mock_get_template.return_value = mock_template

    generate_html_report(sample_data, output_file="relatorio_teste.html")

    # Verifica se render() do template Jinja2 foi chamado com as contagens certas
    mock_template.render.assert_called_once()
    render_kwargs = mock_template.render.call_args.kwargs

    assert render_kwargs["total_suppliers"] == 4
    assert render_kwargs["approved_count"] == 2
    assert render_kwargs["blocked_count"] == 2
    # O melhor fornecedor deve ser o de menor posição entre os ativos (Posição 1)
    assert render_kwargs["best_supplier"]["fornecedor"] == "Fornecedor A"


@patch("jinja2.Environment.get_template")
@patch("builtins.open", new_callable=MagicMock)
def test_generate_html_report_no_active_suppliers(mock_open, mock_get_template):
    """Verifica se o sistema trata o caso onde TODOS os fornecedores estão bloqueados."""
    sample_data = [
        {"posicao": 1, "fornecedor": "Fornecedor A", "nota_final": "-", "status": "BLOQUEADO", "observacao": ""},
        {"posicao": 2, "fornecedor": "Fornecedor B", "nota_final": "-", "status": "BLOCKED", "observacao": ""}
    ]

    mock_template = MagicMock()
    mock_get_template.return_value = mock_template

    generate_html_report(sample_data, output_file="relatorio_teste.html")

    render_kwargs = mock_template.render.call_args.kwargs

    assert render_kwargs["approved_count"] == 0
    assert render_kwargs["blocked_count"] == 2
    assert render_kwargs["best_supplier"] is None