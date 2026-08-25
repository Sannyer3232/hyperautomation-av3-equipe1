"""
Módulo de Coleta de Propostas e Dados Web (Etapa 1).
Responsável: Membro 1 (Sannyer)
"""

from .collector import (
    coletar_propostas_e_status_web,
    coletar_arquivos_propostas,
    coletar_status_fornecedores_web,
    coletar_status_fornecedores_playwright,
    extrair_status_tabela_html,
    extrair_nome_fornecedor_arquivo
)

__all__ = [
    "coletar_propostas_e_status_web",
    "coletar_arquivos_propostas",
    "coletar_status_fornecedores_web",
    "coletar_status_fornecedores_playwright",
    "extrair_status_tabela_html",
    "extrair_nome_fornecedor_arquivo"
]
