"""
Testes Unitários para a Etapa 1: Coleta de Propostas e Status Web (incluindo Playwright RPA).
Responsável: Membro 1 (Sannyer)
"""

from pathlib import Path
from unittest.mock import patch, MagicMock

from src.config import PROPOSTAS_DIR, WEB_PANEL_LOCAL_PATH
from src.logger import AuditLogger
from src.etapa1_coleta.collector import (
    coletar_arquivos_propostas,
    coletar_status_fornecedores_web,
    coletar_status_fornecedores_playwright,
    extrair_status_tabela_html,
    extrair_nome_fornecedor_arquivo,
    coletar_propostas_e_status_web
)


class TestExtracaoNomeFornecedor:
    """Testes para a extração do nome/identificador do fornecedor a partir de caminhos."""

    def test_extrair_nome_padrao_excel(self):
        nome = extrair_nome_fornecedor_arquivo("proposta_fornecedor_A.xlsx")
        assert nome == "Fornecedor A"

    def test_extrair_nome_padrao_csv(self):
        nome = extrair_nome_fornecedor_arquivo("proposta_fornecedor_B.csv")
        assert nome == "Fornecedor B"

    def test_extrair_nome_fornecedor_invalido(self):
        nome = extrair_nome_fornecedor_arquivo("proposta_invalida_fornecedor_D.xlsx")
        assert nome == "Fornecedor D"

    def test_extrair_nome_sem_padrao(self):
        nome = extrair_nome_fornecedor_arquivo("cotacao_geral_2026.pdf")
        assert nome is None


class TestColetaArquivos:
    """Testes para o leitor e varredor de diretório de propostas."""

    def test_coletar_arquivos_diretorio_real(self):
        arquivos = coletar_arquivos_propostas(PROPOSTAS_DIR)
        assert len(arquivos) >= 4
        nomes = [f.name for f in arquivos]
        assert "proposta_fornecedor_A.xlsx" in nomes
        assert "proposta_fornecedor_B.csv" in nomes
        assert "proposta_fornecedor_C.xlsx" in nomes
        assert "proposta_invalida_fornecedor_D.xlsx" in nomes

    def test_coletar_arquivos_ignora_temporarios_e_outros_formatos(self, tmp_path):
        # Cria arquivos válidos
        (tmp_path / "proposta_fornecedor_A.xlsx").write_text("dummy", encoding="utf-8")
        (tmp_path / "proposta_fornecedor_B.csv").write_text("dummy", encoding="utf-8")

        # Cria arquivos que devem ser ignorados
        (tmp_path / "~$proposta_fornecedor_A.xlsx").write_text("lock", encoding="utf-8")
        (tmp_path / ".hidden_proposta.csv").write_text("hidden", encoding="utf-8")
        (tmp_path / "documento.pdf").write_text("pdf", encoding="utf-8")
        (tmp_path / "notas.txt").write_text("txt", encoding="utf-8")
        (tmp_path / "subpasta").mkdir()

        arquivos = coletar_arquivos_propostas(tmp_path)
        nomes = [f.name for f in arquivos]

        assert len(arquivos) == 2
        assert "proposta_fornecedor_A.xlsx" in nomes
        assert "proposta_fornecedor_B.csv" in nomes
        assert "~$proposta_fornecedor_A.xlsx" not in nomes
        assert ".hidden_proposta.csv" not in nomes
        assert "documento.pdf" not in nomes

    def test_coletar_arquivos_diretorio_inexistente(self):
        caminho_inexistente = Path("pasta_que_nao_existe_12345")
        arquivos = coletar_arquivos_propostas(caminho_inexistente)
        assert arquivos == []

    def test_coletar_arquivos_caminho_nao_diretorio(self, tmp_path):
        arquivo = tmp_path / "arquivo_simples.txt"
        arquivo.write_text("conteudo", encoding="utf-8")
        arquivos = coletar_arquivos_propostas(arquivo)
        assert arquivos == []


class TestPlaywrightExtracao:
    """Testes específicos para a extração do portal via Playwright RPA."""

    def test_coletar_status_playwright_portal_real(self):
        # Execução real do Playwright no painel simulado
        status_map = coletar_status_fornecedores_playwright(
            url="http://localhost:9999/porta_fechada",
            local_path=WEB_PANEL_LOCAL_PATH,
            headless=True,
            timeout_ms=3000
        )
        assert len(status_map) > 0
        assert status_map.get("A") == "Ativo"
        assert status_map.get("Fornecedor A") == "Ativo"
        assert status_map.get("D") == "Bloqueado"
        assert status_map.get("Fornecedor D") == "Bloqueado"

    def test_coletar_status_playwright_custom_html(self, tmp_path):
        fake_portal = tmp_path / "portal_teste.html"
        fake_portal.write_text(
            """
            <!doctype html><html><body>
            <h1>Portal de Compras</h1>
            <table>
                <tr><th>Fornecedor</th><th>Status</th></tr>
                <tr><td>Alpha</td><td>Ativo</td></tr>
                <tr><td>Beta</td><td>Suspenso</td></tr>
            </table>
            </body></html>
            """,
            encoding="utf-8"
        )
        status_map = coletar_status_fornecedores_playwright(
            url=None,
            local_path=fake_portal,
            headless=True,
            timeout_ms=3000
        )
        assert status_map.get("Alpha") == "Ativo"
        assert status_map.get("Beta") == "Suspenso"

    def test_coletar_status_playwright_tabela_vazia(self, tmp_path):
        fake_portal = tmp_path / "portal_vazio.html"
        fake_portal.write_text(
            """
            <!doctype html><html><body>
            <table><tr><th>Fornecedor</th><th>Status</th></tr></table>
            </body></html>
            """,
            encoding="utf-8"
        )
        status_map = coletar_status_fornecedores_playwright(
            url=None,
            local_path=fake_portal,
            headless=True,
            timeout_ms=3000
        )
        assert status_map == {}

    def test_coletar_status_playwright_falha_total(self, tmp_path):
        nao_existe = tmp_path / "nao_existe_portal.html"
        status_map = coletar_status_fornecedores_playwright(
            url="http://localhost:9998/falha",
            local_path=nao_existe,
            headless=True,
            timeout_ms=1000
        )
        assert status_map == {}


class TestColetaStatusWeb:
    """Testes para o módulo orquestrador de web scraping e múltiplos fallbacks."""

    def test_extrair_status_tabela_html_valida(self):
        html = """
        <html><body>
        <table>
            <tr><th>Fornecedor</th><th>Status</th></tr>
            <tr><td>A</td><td>Ativo</td></tr>
            <tr><td>B</td><td>Ativo</td></tr>
            <tr><td>C</td><td>Ativo</td></tr>
            <tr><td>D</td><td>Bloqueado</td></tr>
        </table>
        </body></html>
        """
        status_map = extrair_status_tabela_html(html)
        assert status_map["A"] == "Ativo"
        assert status_map["Fornecedor A"] == "Ativo"
        assert status_map["B"] == "Ativo"
        assert status_map["D"] == "Bloqueado"
        assert status_map["Fornecedor D"] == "Bloqueado"

    def test_extrair_status_tabela_com_nome_fornecedor_extenso(self):
        html = """
        <table>
            <tr><th>Fornecedor</th><th>Status</th></tr>
            <tr><td>Fornecedor A</td><td>Ativo</td></tr>
            <tr><td>Fornecedor D</td><td>Bloqueado</td></tr>
        </table>
        """
        status_map = extrair_status_tabela_html(html)
        assert status_map["Fornecedor A"] == "Ativo"
        assert status_map["A"] == "Ativo"
        assert status_map["Fornecedor D"] == "Bloqueado"
        assert status_map["D"] == "Bloqueado"

    def test_extrair_status_tabela_sem_cabecalho_padrao(self):
        html = """
        <table>
            <tr><th>Col1</th><th>Col2</th></tr>
            <tr><td>Empresa 1</td><td>Ativo</td></tr>
        </table>
        """
        status_map = extrair_status_tabela_html(html)
        assert status_map["Empresa 1"] == "Ativo"

    def test_extrair_status_tabela_com_linha_vazia(self):
        html = """
        <table>
            <tr><th>Fornecedor</th><th>Status</th></tr>
            <tr><td></td><td>Ativo</td></tr>
            <tr><td>Fornecedor K</td><td>Ativo</td></tr>
        </table>
        """
        status_map = extrair_status_tabela_html(html)
        assert "" not in status_map
        assert status_map["Fornecedor K"] == "Ativo"

    def test_extrair_status_tabela_html_sem_tabela(self):
        html = "<html><body><h1>Sem tabela aqui</h1></body></html>"
        status_map = extrair_status_tabela_html(html)
        assert status_map == {}

    def test_extrair_status_tabela_html_vazia(self):
        html = "<html><body><table></table></body></html>"
        status_map = extrair_status_tabela_html(html)
        assert status_map == {}

    def test_coletar_status_web_execucao_padrao(self):
        # Execução padrão acionando Playwright
        status_map = coletar_status_fornecedores_web(
            url="http://localhost:9999/url_inexistente",
            local_path=WEB_PANEL_LOCAL_PATH,
            timeout=1.0
        )
        assert len(status_map) > 0
        assert status_map.get("A") == "Ativo"
        assert status_map.get("D") == "Bloqueado"

    @patch("src.etapa1_coleta.collector.coletar_status_fornecedores_playwright")
    @patch("requests.get")
    def test_coletar_status_fallback_requests_quando_playwright_falha(self, mock_get, mock_pw):
        mock_pw.side_effect = RuntimeError("Playwright indisponível")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <table>
            <tr><th>Fornecedor</th><th>Status</th></tr>
            <tr><td>X</td><td>Ativo</td></tr>
            <tr><td>Y</td><td>Suspenso</td></tr>
        </table>
        """
        mock_get.return_value = mock_response

        status_map = coletar_status_fornecedores_web(url="http://fake-server/painel.html")
        assert status_map["X"] == "Ativo"
        assert status_map["Fornecedor X"] == "Ativo"
        assert status_map["Y"] == "Suspenso"
        mock_get.assert_called_once()

    @patch("src.etapa1_coleta.collector.coletar_status_fornecedores_playwright")
    @patch("requests.get")
    def test_coletar_status_fallback_disco_quando_playwright_e_http_falham(self, mock_get, mock_pw, tmp_path):
        mock_pw.side_effect = RuntimeError("Playwright falhou")
        mock_get.side_effect = ConnectionError("HTTP indisponível")

        fake_html = tmp_path / "fallback_disco.html"
        fake_html.write_text(
            "<table><tr><th>Fornecedor</th><th>Status</th></tr><tr><td>Z</td><td>Ativo</td></tr></table>",
            encoding="utf-8"
        )

        status_map = coletar_status_fornecedores_web(
            url="http://fake-server/404",
            local_path=fake_html
        )
        assert status_map["Z"] == "Ativo"

    @patch("src.etapa1_coleta.collector.coletar_status_fornecedores_playwright")
    @patch("requests.get")
    def test_coletar_status_falha_total_todos_metodos(self, mock_get, mock_pw, tmp_path):
        mock_pw.side_effect = RuntimeError("Playwright falhou")
        mock_get.side_effect = ConnectionError("HTTP indisponível")
        nao_existe = tmp_path / "nao_existe.html"

        status_map = coletar_status_fornecedores_web(
            url="http://localhost:9998/falha",
            local_path=nao_existe,
            timeout=0.5
        )
        assert status_map == {}


class TestPipelineColeta:
    """Testes integrados da função orquestradora da Etapa 1 com auditoria."""

    def test_coletar_propostas_e_status_web_completo(self):
        audit = AuditLogger()
        arquivos, status_web = coletar_propostas_e_status_web(
            propostas_dir=PROPOSTAS_DIR,
            local_path=WEB_PANEL_LOCAL_PATH,
            audit=audit
        )

        assert len(arquivos) >= 4
        assert len(status_web) > 0
        assert len(audit.propostas_recebidas) >= 4

        # Verifica se o Fornecedor D e Fornecedor A foram devidamente registrados na auditoria
        fornecedores_registrados = [p["fornecedor"] for p in audit.propostas_recebidas]
        assert "Fornecedor A" in fornecedores_registrados
        assert "Fornecedor D" in fornecedores_registrados

    def test_coletar_propostas_e_status_web_pasta_vazia(self, tmp_path):
        audit = AuditLogger()
        pasta_vazia = tmp_path / "propostas_vazias"
        pasta_vazia.mkdir()

        arquivos, status_web = coletar_propostas_e_status_web(
            propostas_dir=pasta_vazia,
            local_path=WEB_PANEL_LOCAL_PATH,
            audit=audit
        )

        assert arquivos == []
        assert len(audit.erros) == 1
        assert audit.erros[0]["etapa"] == "Coleta"
