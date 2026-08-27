"""
Módulo de Leitura e Extração de Propostas Comerciais e Critérios (Etapa 2).
Responsável: Membro 1 (Sannyer)

Realiza a ingestão e extração de dados estruturados em múltiplos formatos (.xlsx, .csv),
com padronização de cabeçalhos, tolerância a delimitadores/encodings e fallback para pesos de negócio.
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

from src.config import (
    CRITERIOS_PATH,
    MODELO_RANKING_PATH,
    DEFAULT_WEIGHTS
)
from src.logger import logger, AuditLogger

# Mapeamento para normalização de variações comuns de cabeçalhos
MAPEAMENTO_COLUNAS = {
    "fornecedor": "Fornecedor",
    "empresa": "Fornecedor",
    "supplier": "Fornecedor",
    "produto": "Produto",
    "item": "Produto",
    "descricao": "Produto",
    "custo": "Custo",
    "preco": "Custo",
    "preco_unitario": "Custo",
    "valor": "Custo",
    "cost": "Custo",
    "price": "Custo",
    "prazo_dias": "Prazo_Dias",
    "prazo": "Prazo_Dias",
    "prazo (dias)": "Prazo_Dias",
    "lead_time": "Prazo_Dias",
    "lead time": "Prazo_Dias",
    "capacidade": "Capacidade",
    "capacidade_mensal": "Capacidade",
    "capacity": "Capacidade",
    "qualidade": "Qualidade",
    "score_qualidade": "Qualidade",
    "quality": "Qualidade"
}

COLUNAS_OBRIGATORIAS = ["Fornecedor", "Produto", "Custo", "Prazo_Dias", "Capacidade", "Qualidade"]
COLUNAS_TEMPLATE_RANKING = ["Posicao", "Fornecedor", "Nota_Final", "Status", "Observacao"]


def normalizar_nome_coluna(coluna: str) -> str:
    """
    Normaliza o nome de uma coluna removendo espaços, acentos e aplicando correspondência padrão.

    Args:
        coluna: Nome original da coluna.

    Returns:
        Nome padronizado da coluna.
    """
    chave = str(coluna).strip().lower().replace(" ", "_")
    return MAPEAMENTO_COLUNAS.get(chave, str(coluna).strip())


def ler_proposta(caminho_arquivo: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Efetua a leitura e extração estruturada de um arquivo de proposta individual (.xlsx, .xls ou .csv).
    Garante tolerância a delimitadores (';', ',') e encodings ('utf-8', 'latin-1').

    Args:
        caminho_arquivo: Caminho do arquivo a ser lido.

    Returns:
        Lista de dicionários contendo os registros da proposta com a chave de metadados '_arquivo'.
    """
    arquivo = Path(caminho_arquivo)

    if not arquivo.exists():
        logger.error(f"[LEITURA] Arquivo de proposta não encontrado: {arquivo}")
        return []

    extensao = arquivo.suffix.lower()
    df: Optional[pd.DataFrame] = None

    try:
        if extensao in {".xlsx", ".xls"}:
            logger.info(f"[LEITURA EXCEL] Processando planilha: {arquivo.name}")
            df = pd.read_excel(arquivo)
        elif extensao == ".csv":
            logger.info(f"[LEITURA CSV] Processando arquivo CSV: {arquivo.name}")
            # Tentativa de detecção automática de delimitador e encoding
            for sep in [";", ",", "\t"]:
                for enc in ["utf-8", "latin-1", "cp1252"]:
                    try:
                        temp_df = pd.read_csv(arquivo, sep=sep, encoding=enc)
                        if len(temp_df.columns) > 1:
                            df = temp_df
                            break
                    except Exception:
                        continue
                if df is not None:
                    break

            if df is None:
                # Fallback padrão pandas
                df = pd.read_csv(arquivo, sep=None, engine="python", encoding="utf-8")
        else:
            logger.warning(f"[LEITURA] Formato não suportado para leitura: {arquivo.name}")
            return []

    except Exception as e:
        logger.error(f"[LEITURA] Falha técnica ao abrir arquivo {arquivo.name}: {e}")
        return []

    if df is None or df.empty:
        logger.warning(f"[LEITURA] O arquivo {arquivo.name} está vazio ou não pôde ser interpretado.")
        return []

    # Normalizar nomes de colunas
    novas_colunas = {col: normalizar_nome_coluna(col) for col in df.columns}
    df = df.rename(columns=novas_colunas)

    # Converter para registros tipados mantendo a referência do arquivo de origem
    registros: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        dados_linha = row.to_dict()
        dados_linha["_arquivo"] = str(arquivo.name)
        registros.append(dados_linha)

    logger.info(f"[LEITURA] {len(registros)} registro(s) extraído(s) com sucesso de '{arquivo.name}'")
    return registros


def ler_todas_propostas(
    arquivos: List[Union[str, Path]],
    audit: Optional[AuditLogger] = None
) -> List[Dict[str, Any]]:
    """
    Realiza a leitura em lote de todos os arquivos de propostas comerciais coletados.
    Registra anomalias na auditoria sem interromper o processamento dos demais arquivos.

    Args:
        arquivos: Lista de caminhos de arquivos a serem lidos.
        audit: Instância de AuditLogger para governança.

    Returns:
        Lista consolidada de registros de propostas brutas.
    """
    logger.info(">>> INICIANDO ETAPA 2: LEITURA E EXTRAÇÃO DE PROPOSTAS <<<")
    todas_propostas: List[Dict[str, Any]] = []

    if not arquivos:
        msg = "Nenhum arquivo fornecido para leitura na Etapa 2."
        logger.warning(f"[LEITURA] {msg}")
        if audit:
            audit.registrar_erro("Leitura", msg)
        return todas_propostas

    for arq in arquivos:
        try:
            propostas_arquivo = ler_proposta(arq)
            if propostas_arquivo:
                todas_propostas.extend(propostas_arquivo)
            else:
                msg = f"Arquivo '{Path(arq).name}' não continha registros válidos extraíveis."
                logger.warning(f"[LEITURA] {msg}")
                if audit:
                    audit.registrar_erro("Leitura", msg)
        except Exception as e:
            msg = f"Erro não tratado ao processar o arquivo '{Path(arq).name}': {e}"
            logger.error(f"[LEITURA] {msg}")
            if audit:
                audit.registrar_erro("Leitura", msg, e)

    logger.info(f"[LEITURA] Total geral de propostas brutas lidas: {len(todas_propostas)}")
    logger.info(">>> ETAPA 2 (LEITURA) CONCLUÍDA COM SUCESSO <<<\n")
    return todas_propostas


def ler_criterios(caminho_criterios: Optional[Union[str, Path]] = None) -> pd.DataFrame:
    """
    Carrega a matriz de critérios de ranking e pesos a partir do arquivo Excel criterios_ranking.xlsx.
    Caso o arquivo não exista ou contenha falhas, aplica o fallback inteligente baseado nas
    constantes de negócio de DEFAULT_WEIGHTS (Custo 40%, Prazo 25%, Capacidade 20%, Qualidade 15%).

    Args:
        caminho_criterios: Caminho para a planilha de critérios.

    Returns:
        DataFrame padronizado com as colunas ['Criterio', 'Direcao', 'Peso'].
    """
    caminho = Path(caminho_criterios) if caminho_criterios else CRITERIOS_PATH

    if caminho and caminho.exists():
        try:
            logger.info(f"[CRITÉRIOS] Lendo arquivo oficial de critérios: {caminho}")
            df = pd.read_excel(caminho)

            # Normalização de colunas
            df.columns = [normalizar_nome_coluna(c) for c in df.columns]

            # Validação se as colunas essenciais existem
            colunas_existentes = {c.lower() for c in df.columns}
            if "criterio" in colunas_existentes and "peso" in colunas_existentes:
                # Padronizar nomes exatos
                col_rename = {}
                for c in df.columns:
                    if c.lower() == "criterio":
                        col_rename[c] = "Criterio"
                    elif c.lower() == "direcao":
                        col_rename[c] = "Direcao"
                    elif c.lower() == "peso":
                        col_rename[c] = "Peso"
                df = df.rename(columns=col_rename)

                # Garantir tipo numérico no peso
                df["Peso"] = pd.to_numeric(df["Peso"], errors="coerce")
                logger.info("[CRITÉRIOS] Critérios carregados com sucesso do arquivo Excel.")
                return df
            else:
                logger.warning("[CRITÉRIOS] Estrutura do arquivo de critérios divergente. Aplicando fallback.")
        except Exception as e:
            logger.warning(f"[CRITÉRIOS] Falha ao ler planilha de critérios ({e}). Aplicando fallback de negócio.")

    # Fallback: Criação do DataFrame com base em DEFAULT_WEIGHTS
    logger.info("[CRITÉRIOS - FALLBACK] Utilizando pesos de negócio padrão (Custo: 40%, Prazo: 25%, ...)")
    linhas_fallback = []
    for crit, config in DEFAULT_WEIGHTS.items():
        linhas_fallback.append({
            "Criterio": crit,
            "Direcao": config.get("direcao", "Maior"),
            "Peso": config.get("peso", 0.0)
        })

    return pd.DataFrame(linhas_fallback)


def ler_modelo_ranking(caminho_modelo: Optional[Union[str, Path]] = None) -> pd.DataFrame:
    """
    Lê o template oficial de modelo de ranking modelo_ranking.xlsx.
    Caso não encontrado, cria um DataFrame vazio com os cabeçalhos oficiais.

    Args:
        caminho_modelo: Caminho para a planilha modelo de ranking.

    Returns:
        DataFrame com a estrutura de colunas do ranking final.
    """
    caminho = Path(caminho_modelo) if caminho_modelo else MODELO_RANKING_PATH

    if caminho and caminho.exists():
        try:
            logger.info(f"[MODELO RANKING] Carregando template oficial: {caminho}")
            df = pd.read_excel(caminho)
            return df
        except Exception as e:
            logger.warning(f"[MODELO RANKING] Falha ao carregar template ({e}). Criando estrutura padrão.")

    return pd.DataFrame(columns=COLUNAS_TEMPLATE_RANKING)
