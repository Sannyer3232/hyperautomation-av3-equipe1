"""
Módulo de Trigger e Monitoramento por E-mail (IMAP / SMTP).
"""

from .service import (
    EmailTriggerService,
    decodificar_cabecalho,
    extrair_anexos_email,
    construir_email_resposta,
    processar_trigger_email,
)

__all__ = [
    "EmailTriggerService",
    "decodificar_cabecalho",
    "extrair_anexos_email",
    "construir_email_resposta",
    "processar_trigger_email",
]
