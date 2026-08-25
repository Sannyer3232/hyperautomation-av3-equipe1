"""
Módulo de Logging e Auditoria.
Garante o registro completo da esteira de hyperautomation.
"""

import os
import logging
import json
from datetime import datetime
from pathlib import Path
from src.config import LOGS_DIR, LOG_LEVEL

log_file_path = LOGS_DIR / "execucao.log"
audit_log_path = LOGS_DIR / "auditoria.json"

# Formatação do Log
formatter = logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Configuração do Logger Raiz
logger = logging.getLogger("Hyperautomation")
logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))

# Handler de Console
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler de Arquivo
    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


class AuditLogger:
    """
    Classe de auditoria estruturada para compliance SOX e avaliação técnica.
    Registra: propostas recebidas, válidas, rejeitadas, cálculo e ranking final.
    """

    def __init__(self):
        self.propostas_recebidas = []
        self.propostas_validas = []
        self.propostas_rejeitadas = []
        self.calculos_realizados = {}
        self.ranking_final = []
        self.erros = []
        self.inicio_execucao = datetime.now().isoformat()

    def registrar_proposta_recebida(self, arquivo: str, fornecedor: str = None):
        info = {"arquivo": str(arquivo), "fornecedor": fornecedor}
        self.propostas_recebidas.append(info)
        logger.info(f"[PROPOSTA RECEBIDA] Arquivo: {arquivo} | Fornecedor: {fornecedor or 'N/A'}")

    def registrar_proposta_valida(self, fornecedor: str, dados: dict):
        self.propostas_validas.append({"fornecedor": fornecedor, "dados": dados})
        logger.info(f"[PROPOSTA VÁLIDA] Fornecedor: {fornecedor} | Dados: {dados}")

    def registrar_proposta_rejeitada(self, fornecedor: str, motivo: str, dados: dict = None):
        self.propostas_rejeitadas.append({
            "fornecedor": fornecedor,
            "motivo": motivo,
            "dados": dados or {}
        })
        logger.warning(f"[PROPOSTA REJEITADA] Fornecedor: {fornecedor} | Motivo: {motivo}")

    def registrar_calculo(self, fornecedor: str, scores: dict, nota_final: float):
        self.calculos_realizados[fornecedor] = {
            "scores_parciais": scores,
            "nota_final": round(nota_final, 4)
        }
        logger.info(f"[CÁLCULO MCDA] Fornecedor: {fornecedor} | Scores: {scores} | Nota Final: {nota_final:.4f}")

    def registrar_ranking(self, ranking_df_records: list):
        self.ranking_final = ranking_df_records
        logger.info(f"[RANKING FINAL GERADO] Total de classificados: {len(ranking_df_records)}")

    def registrar_erro(self, etapa: str, mensagem: str, excecao: Exception = None):
        erro_info = {
            "etapa": etapa,
            "mensagem": mensagem,
            "excecao": str(excecao) if excecao else None
        }
        self.erros.append(erro_info)
        logger.error(f"[ERRO - {etapa}] {mensagem} | Detalhes: {excecao}")

    def salvar_auditoria(self):
        """Salva resumo da auditoria em formato JSON para compliance."""
        resumo = {
            "inicio_execucao": self.inicio_execucao,
            "fim_execucao": datetime.now().isoformat(),
            "total_recebidas": len(self.propostas_recebidas),
            "total_validas": len(self.propostas_validas),
            "total_rejeitadas": len(self.propostas_rejeitadas),
            "propostas_recebidas": self.propostas_recebidas,
            "propostas_validas": self.propostas_validas,
            "propostas_rejeitadas": self.propostas_rejeitadas,
            "calculos": self.calculos_realizados,
            "ranking": self.ranking_final,
            "erros": self.erros
        }
        with open(audit_log_path, "w", encoding="utf-8") as f:
            json.dump(resumo, f, indent=4, ensure_ascii=False)
        logger.info(f"Relatório de auditoria persistido em: {audit_log_path}")
        return resumo
