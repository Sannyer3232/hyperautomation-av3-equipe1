"""
Módulo de Coleta de Propostas e Status de Fornecedores (Etapa 1).
Responsável: Membro 1 (Sannyer)

Executa a varredura e coleta dos arquivos de propostas comerciais (.xlsx, .csv)
e a extração dos dados cadastrais/status dos fornecedores no painel web (simulado via Playwright/HTTP/HTML local).
"""

import re
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

from src.config import (
    PROPOSTAS_DIR,
    WEB_PANEL_URL,
    WEB_PANEL_LOCAL_PATH
)
from src.logger import logger, AuditLogger

# Extensões de arquivos de propostas suportadas pelo robô
EXTENSOES_PERMITIDAS = {".xlsx", ".xls", ".csv"}


def extrair_nome_fornecedor_arquivo(caminho_arquivo: Union[str, Path]) -> Optional[str]:
    """
    Extrai o identificador ou nome do fornecedor a partir do nome do arquivo.

    Exemplos:
        'proposta_fornecedor_A.xlsx' -> 'Fornecedor A'
        'proposta_invalida_fornecedor_D.xlsx' -> 'Fornecedor D'
        'fornecedor_B.csv' -> 'Fornecedor B'
    """
    stem = Path(caminho_arquivo).stem
    match = re.search(r"fornecedor[_\s]+([a-zA-Z0-9]+)", stem, re.IGNORECASE)
    if match:
        letra_ou_id = match.group(1).upper()
        return f"Fornecedor {letra_ou_id}"
    return None


def coletar_arquivos_propostas(
    propostas_dir: Optional[Union[str, Path]] = None
) -> List[Path]:
    """
    Realiza a varredura do diretório de propostas em busca de arquivos válidos (.xlsx, .csv).
    Ignora arquivos temporários (ex: ~$...) e ocultos.

    Args:
        propostas_dir: Caminho para a pasta contendo as propostas comerciais.

    Returns:
        Lista ordenada de caminhos (Path) dos arquivos encontrados.
    """
    diretorio = Path(propostas_dir) if propostas_dir else PROPOSTAS_DIR

    if not diretorio.exists():
        logger.error(f"[COLETA] Diretório de propostas não encontrado: {diretorio}")
        return []

    if not diretorio.is_dir():
        logger.error(f"[COLETA] O caminho informado não é um diretório: {diretorio}")
        return []

    arquivos_encontrados: List[Path] = []

    for item in sorted(diretorio.iterdir()):
        # Ignora diretórios, arquivos temporários do Office e arquivos ocultos
        if item.is_file() and not item.name.startswith("~$") and not item.name.startswith("."):
            if item.suffix.lower() in EXTENSOES_PERMITIDAS:
                arquivos_encontrados.append(item)
                logger.info(f"[COLETA] Arquivo de proposta localizado: {item.name} ({item.stat().st_size} bytes)")
            else:
                logger.debug(f"[COLETA] Arquivo ignorado por formato não suportado: {item.name}")

    logger.info(f"[COLETA] Total de arquivos de propostas localizados: {len(arquivos_encontrados)}")
    return arquivos_encontrados


def registrar_mapeamento_status(status_map: Dict[str, str], fornecedor_raw: str, status_raw: str) -> None:
    """
    Registra no dicionário de status o fornecedor original e seus aliases padronizados
    (ex: 'A' -> 'Fornecedor A', 'FORNECEDOR A', 'A').
    """
    forn = fornecedor_raw.strip()
    stat = status_raw.strip()
    if not forn:
        return

    status_map[forn] = stat

    if len(forn) <= 2:
        status_map[f"Fornecedor {forn.upper()}"] = stat
        status_map[f"FORNECEDOR {forn.upper()}"] = stat
        status_map[f"fornecedor {forn.lower()}"] = stat
    elif forn.lower().startswith("fornecedor "):
        letra = forn.split()[-1]
        status_map[letra] = stat
        status_map[letra.upper()] = stat
        status_map[letra.lower()] = stat

    logger.info(f"[COLETA WEB] Fornecedor cadastrado: '{forn}' -> Status: '{stat}'")


def extrair_status_tabela_html(html_content: str) -> Dict[str, str]:
    """
    Efetua o parsing do HTML (via BeautifulSoup) para extrair o status cadastral da tabela.

    Args:
        html_content: String contendo o código HTML da página.

    Returns:
        Dicionário com o mapeamento {fornecedor: status}.
    """
    status_map: Dict[str, str] = {}
    soup = BeautifulSoup(html_content, "html.parser")
    tabela = soup.find("table")

    if not tabela:
        logger.warning("[COLETA WEB] Nenhuma tabela <table> encontrada no HTML do painel.")
        return status_map

    linhas = tabela.find_all("tr")
    if not linhas:
        logger.warning("[COLETA WEB] Tabela HTML vazia ou sem linhas <tr>.")
        return status_map

    cabecalhos = [th.get_text(strip=True).lower() for th in linhas[0].find_all(["th", "td"])]

    idx_fornecedor = -1
    idx_status = -1
    for i, col in enumerate(cabecalhos):
        if "fornecedor" in col:
            idx_fornecedor = i
        elif "status" in col:
            idx_status = i

    if idx_fornecedor == -1 or idx_status == -1:
        idx_fornecedor = 0
        idx_status = 1

    for linha in linhas[1:]:
        colunas = [td.get_text(strip=True) for td in linha.find_all(["td", "th"])]
        if len(colunas) > max(idx_fornecedor, idx_status):
            registrar_mapeamento_status(status_map, colunas[idx_fornecedor], colunas[idx_status])

    return status_map


def coletar_status_fornecedores_playwright(
    url: Optional[str] = None,
    local_path: Optional[Union[str, Path]] = None,
    headless: bool = True,
    timeout_ms: int = 4000
) -> Dict[str, str]:
    """
    Navega até o portal web simulado utilizando o Playwright (navegador Chromium automatizado)
    e extrai os dados cadastrais da tabela de fornecedores.

    Em caso de falha de conexão com a URL remota/servidor HTTP (porta 8000), tenta navegar
    automaticamente para a URL do arquivo local (file://) via Playwright em uma nova aba limpa.

    Args:
        url: URL HTTP do painel web simulado (ex: http://localhost:8000/...).
        local_path: Caminho local do arquivo HTML de contingência.
        headless: Se o navegador deve rodar em segundo plano (True).
        timeout_ms: Timeout em milissegundos para carregamento de página e seletores.

    Returns:
        Dicionário com o mapeamento {fornecedor: status}.
    """
    if sync_playwright is None:
        raise ImportError("Playwright não está instalado no ambiente.")

    status_map: Dict[str, str] = {}
    url_target = url or WEB_PANEL_URL
    path_target = Path(local_path) if local_path else WEB_PANEL_LOCAL_PATH

    logger.info(f"[PLAYWRIGHT RPA] Iniciando automação de navegador (Headless={headless})...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()

        navegou_com_sucesso = False

        # Tentativa 1: Acessar via URL HTTP (simulando portal online)
        if url_target:
            try:
                logger.info(f"[PLAYWRIGHT RPA] Navegando até o portal web: {url_target}")
                page.goto(url_target, timeout=timeout_ms, wait_until="domcontentloaded")
                page.wait_for_selector("table", timeout=timeout_ms)
                navegou_com_sucesso = True
                logger.info(f"[PLAYWRIGHT RPA] Portal carregado com sucesso via HTTP. Título: '{page.title()}'")
            except Exception as e:
                logger.warning(
                    f"[PLAYWRIGHT RPA] Falha ao acessar URL HTTP '{url_target}' ({e}). "
                    "Tentando contingência via file:// em nova página..."
                )
                try:
                    page.close()
                except Exception:
                    pass
                page = context.new_page()

        # Tentativa 2: Acessar via URI de arquivo local (file://)
        if not navegou_com_sucesso:
            if path_target and path_target.exists():
                try:
                    file_uri = path_target.resolve().as_uri()
                    logger.info(f"[PLAYWRIGHT RPA - CONTINGÊNCIA] Navegando via file URI: {file_uri}")
                    page.goto(file_uri, timeout=timeout_ms, wait_until="domcontentloaded")
                    page.wait_for_selector("table", timeout=timeout_ms)
                    navegou_com_sucesso = True
                    logger.info(f"[PLAYWRIGHT RPA] Página local carregada com sucesso. Título: '{page.title()}'")
                except Exception as e:
                    logger.error(f"[PLAYWRIGHT RPA - CONTINGÊNCIA] Erro ao navegar para arquivo local: {e}")
            else:
                logger.error(f"[PLAYWRIGHT RPA] Arquivo local não encontrado: {path_target}")

        if navegou_com_sucesso:
            try:
                rows = page.locator("table tr").all()
                if len(rows) > 1:
                    # Identificar cabeçalhos
                    headers = [th.inner_text().strip().lower() for th in rows[0].locator("th, td").all()]
                    idx_forn = 0
                    idx_stat = 1
                    for i, h in enumerate(headers):
                        if "fornecedor" in h:
                            idx_forn = i
                        elif "status" in h:
                            idx_stat = i

                    for row in rows[1:]:
                        cells = [c.inner_text().strip() for c in row.locator("th, td").all()]
                        if len(cells) > max(idx_forn, idx_stat):
                            registrar_mapeamento_status(status_map, cells[idx_forn], cells[idx_stat])
                else:
                    logger.warning("[PLAYWRIGHT RPA] Tabela sem linhas de dados encontradas na página.")
            except Exception as e:
                logger.error(f"[PLAYWRIGHT RPA] Erro ao extrair dados dos elementos da página: {e}")

        browser.close()

    logger.info(f"[PLAYWRIGHT RPA] Extração finalizada com {len(status_map)} registros mapeados.")
    return status_map


def coletar_status_fornecedores_web(
    url: Optional[str] = None,
    local_path: Optional[Union[str, Path]] = None,
    timeout: float = 3.0
) -> Dict[str, str]:
    """
    Coleta o status cadastral dos fornecedores a partir do painel web simulado.
    Utiliza Playwright como motor principal de RPA e, caso ocorra qualquer indisponibilidade,
    aciona automaticamente fallbacks resilientes via HTTP Requests e leitura de arquivo local.

    Args:
        url: URL HTTP do painel web simulado.
        local_path: Caminho local do arquivo HTML de contingência.
        timeout: Tempo limite da requisição HTTP em segundos.

    Returns:
        Dicionário com o status de cada fornecedor.
    """
    url_target = url or WEB_PANEL_URL
    path_target = Path(local_path) if local_path else WEB_PANEL_LOCAL_PATH

    # 1. Tentativa Principal: Automação de Navegador com Playwright
    try:
        status_map = coletar_status_fornecedores_playwright(
            url=url_target,
            local_path=path_target,
            headless=True,
            timeout_ms=int(timeout * 1000)
        )
        if status_map:
            return status_map
    except Exception as e:
        logger.warning(
            f"[COLETA WEB] Execução via Playwright falhou ({e}). "
            "Acionando fallback secundário via Requests/BeautifulSoup..."
        )

    # 2. Fallback Secundário: Requisição HTTP Requests + BeautifulSoup
    html_content: Optional[str] = None
    if url_target:
        try:
            logger.info(f"[COLETA WEB - FALLBACK HTTP] Tentando requisição HTTP em: {url_target}")
            response = requests.get(url_target, timeout=timeout)
            if response.status_code == 200:
                html_content = response.text
                logger.info("[COLETA WEB - FALLBACK HTTP] Dados obtidos com sucesso via HTTP (200 OK).")
        except Exception as e:
            logger.warning(f"[COLETA WEB - FALLBACK HTTP] Falha ao acessar URL ({e}).")

    # 3. Fallback Terciário: Leitura direta do arquivo HTML em disco
    if html_content is None:
        if path_target and path_target.exists():
            try:
                logger.info(f"[COLETA WEB - FALLBACK DISCO] Lendo HTML local: {path_target}")
                html_content = path_target.read_text(encoding="utf-8")
            except Exception as e:
                logger.error(f"[COLETA WEB - FALLBACK DISCO] Erro ao ler HTML: {e}")

    if not html_content:
        logger.error("[COLETA WEB] Não foi possível obter o conteúdo do portal por nenhum método.")
        return {}

    return extrair_status_tabela_html(html_content)


def coletar_propostas_e_status_web(
    propostas_dir: Optional[Union[str, Path]] = None,
    url: Optional[str] = None,
    local_path: Optional[Union[str, Path]] = None,
    audit: Optional[AuditLogger] = None
) -> Tuple[List[Path], Dict[str, str]]:
    """
    Função orquestradora da Etapa 1 (Coleta).
    Executa a busca de propostas comerciais e a extração do status cadastral web via Playwright.
    Registra os artefatos na trilha de auditoria SOX.

    Args:
        propostas_dir: Diretório de arquivos de propostas.
        url: URL do painel web.
        local_path: Caminho do arquivo HTML local para contingência.
        audit: Instância do AuditLogger para rastreabilidade.

    Returns:
        Tupla contendo: (lista de caminhos dos arquivos, dicionário de status web).
    """
    logger.info(">>> INICIANDO ETAPA 1: COLETA DE PROPOSTAS E STATUS WEB (PLAYWRIGHT RPA) <<<")

    # 1. Coleta de Arquivos de Propostas
    arquivos = coletar_arquivos_propostas(propostas_dir=propostas_dir)

    # Registro no log de auditoria
    if audit:
        for arq in arquivos:
            fornecedor_est = extrair_nome_fornecedor_arquivo(arq)
            audit.registrar_proposta_recebida(arquivo=str(arq), fornecedor=fornecedor_est)

    if not arquivos:
        msg = "Nenhum arquivo de proposta encontrado durante a etapa de coleta."
        logger.warning(f"[COLETA] {msg}")
        if audit:
            audit.registrar_erro("Coleta", msg)

    # 2. Coleta do Status Cadastral Web via Playwright
    status_web = coletar_status_fornecedores_web(url=url, local_path=local_path)
    logger.info(f"[COLETA] Status cadastrais mapeados: {len(status_web)} entradas registradas.")

    logger.info(">>> ETAPA 1 (COLETA) CONCLUÍDA COM SUCESSO <<<\n")
    return arquivos, status_web
