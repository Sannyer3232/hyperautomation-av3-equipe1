"""
Módulo de Trigger por E-mail (IMAP / SMTP) para a Esteira de Hyperautomation.

Responsabilidades:
1. Monitorar a caixa postal (IMAP) aguardando e-mails com assunto específico.
2. Baixar anexos de propostas (.xlsx, .csv) do e-mail recebido.
3. Executar o pipeline de hyperautomation com os arquivos anexados.
4. Responder automaticamente o e-mail (SMTP) com a tabela de classificação,
   planilha Excel de homologação e dashboard HTML em anexo.
"""

import email
import email.header
import imaplib
import logging
import smtplib
import time
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from pathlib import Path
from typing import List, Optional, Tuple, Union
import pandas as pd

from src.config import (
    EMAIL_IMAP_SERVER,
    EMAIL_IMAP_PORT,
    EMAIL_IMAP_SSL,
    EMAIL_SMTP_SERVER,
    EMAIL_SMTP_PORT,
    EMAIL_SMTP_USE_TLS,
    EMAIL_SMTP_USE_SSL,
    EMAIL_USER,
    EMAIL_PASSWORD,
    EMAIL_SUBJECT_TRIGGER,
    EMAIL_ATTACHMENTS_DIR,
    CRITERIOS_PATH,
    WEB_PANEL_LOCAL_PATH,
)
from src.logger import AuditLogger
from src.etapa1_coleta import coletar_propostas_e_status_web
from src.etapa2_leitura import ler_todas_propostas, ler_criterios
from src.etapa3_validacao import validar_todas_propostas
from src.etapa4_consolidacao import consolidar_propostas
from src.etapa5_ranking import calcular_ranking_ponderado
from src.etapa6_resultado import gerar_resultado_final

logger = logging.getLogger("Hyperautomation")

FORMATOS_ANEXO_VALIDOS = {".xlsx", ".xls", ".csv"}


def decodificar_cabecalho(header_val: Optional[str]) -> str:
    """Decodifica cabeçalhos de e-mail codificados segundo a RFC 2047."""
    if not header_val:
        return ""

    partes_decodificadas = []
    for bytes_or_str, encoding in email.header.decode_header(header_val):
        if isinstance(bytes_or_str, bytes):
            enc = encoding or "utf-8"
            try:
                partes_decodificadas.append(bytes_or_str.decode(enc, errors="replace"))
            except (LookupError, UnicodeDecodeError):
                partes_decodificadas.append(bytes_or_str.decode("utf-8", errors="replace"))
        else:
            partes_decodificadas.append(str(bytes_or_str))

    return "".join(partes_decodificadas).strip()


def extrair_anexos_email(
    msg: email.message.Message,
    output_dir: Union[str, Path]
) -> List[Path]:
    """
    Varre as partes do e-mail e extrai todos os anexos válidos (.xlsx, .csv).

    Args:
        msg: Objeto email.message.Message contendo o e-mail.
        output_dir: Diretório onde os arquivos serão salvos.

    Returns:
        Lista de caminhos Path dos arquivos salvos em disco.
    """
    destino = Path(output_dir)
    destino.mkdir(parents=True, exist_ok=True)
    anexos_salvos: List[Path] = []

    if not msg.is_multipart():
        # Mensagem simples sem multipart não possui anexos de arquivo
        return anexos_salvos

    for part in msg.walk():
        filename_raw = part.get_filename()

        if not filename_raw:
            continue

        filename = decodificar_cabecalho(filename_raw)
        ext = Path(filename).suffix.lower()

        # Filtra apenas formatos esperados de propostas
        if ext not in FORMATOS_ANEXO_VALIDOS:
            logger.info(f"[TRIGGER E-MAIL] Anexo ignorado (formato não suportado): {filename}")
            continue

        # Evita conflitos ou caminhos inseguros
        safe_name = Path(filename).name
        target_file = destino / safe_name

        payload = part.get_payload(decode=True)
        if payload:
            with open(target_file, "wb") as f:
                f.write(payload)
            anexos_salvos.append(target_file)
            logger.info(f"[TRIGGER E-MAIL] Anexo salvo com sucesso: {target_file.name} ({len(payload)} bytes)")

    return anexos_salvos


def construir_email_resposta(
    destinatario: str,
    assunto_origem: str,
    df_resultado: pd.DataFrame,
    anexos: List[Union[str, Path]],
    message_id_origem: Optional[str] = None
) -> MIMEMultipart:
    """
    Gera o e-mail de resposta com o quadro de homologação e arquivos anexados.
    """
    assunto_resposta = assunto_origem if assunto_origem.upper().startswith("RE:") else f"Re: {assunto_origem}"

    msg = MIMEMultipart("mixed")
    msg["From"] = EMAIL_USER
    msg["To"] = destinatario
    msg["Subject"] = assunto_resposta
    if message_id_origem:
        msg["In-Reply-To"] = message_id_origem
        msg["References"] = message_id_origem

    # Identifica o vencedor
    ativos = df_resultado[df_resultado["Status"].str.upper() == "ATIVO"]
    vencedor_nome = ativos.iloc[0]["Fornecedor"] if not ativos.empty else "Nenhum fornecedor aprovado"
    vencedor_nota = str(ativos.iloc[0]["Nota_Final"]) if not ativos.empty else "-"

    total = len(df_resultado)
    aprovados = len(ativos)
    rejeitados = total - aprovados

    # Monta linhas da tabela HTML
    linhas_html = []
    for _, row in df_resultado.iterrows():
        st = str(row["Status"]).strip().upper()
        cor_badge = "#16a34a" if st == "ATIVO" else "#dc2626"
        bg_badge = "#dcfce7" if st == "ATIVO" else "#fee2e2"
        badge_html = (
            f'<span style="background-color: {bg_badge}; color: {cor_badge}; '
            f'padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{st}</span>'
        )
        linhas_html.append(f"""
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; font-weight: bold;">#{row['Posicao']}</td>
            <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{row['Fornecedor']}</td>
            <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{row['Nota_Final']}</td>
            <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{badge_html}</td>
            <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; color: #64748b; font-size: 12px;">
                {row['Observacao']}
            </td>
        </tr>
        """)

    tabela_linhas_str = "\n".join(linhas_html)

    # Corpo em Texto Plano (Fallback)
    corpo_texto = f"""Prezado(a),

O processamento automatizado das propostas recebidas foi concluído com sucesso.

--- QUADRO DE HOMOLOGAÇÃO DE FORNECEDORES ---
{df_resultado.to_string(index=False)}

Vencedor Recomendado: {vencedor_nome} (Nota Final: {vencedor_nota})
Total Processados: {total} | Aprovados: {aprovados} | Rejeitados: {rejeitados}

Em anexo enviamos a planilha de ranking oficial (ranking_final.xlsx) e o relatório executivo (relatorio_ranking.html).

Atenciosamente,
Robô de Hyperautomation — Seleção de Fornecedores LG Electronics
"""

    # Corpo HTML Formatado
    corpo_html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: Arial, sans-serif; color: #1e293b; line-height: 1.5; padding: 20px;">
        <div style="max-width: 750px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 8px; padding: 24px;">
            <h2 style="color: #0f172a; margin-top: 0; border-bottom: 2px solid #2563eb; padding-bottom: 8px;">
                Parecer de Seleção de Fornecedores — LG Electronics
            </h2>
            <p>Olá,</p>
            <p>O robô de <strong>Hyperautomation</strong> processou com sucesso as propostas anexadas ao seu e-mail.</p>
            <div style="display: flex; gap: 15px; margin: 20px 0; background: #f8fafc; padding: 15px;">
                <div style="flex: 1;"><strong>Total de Propostas:</strong> {total}</div>
                <div style="flex: 1; color: #16a34a;"><strong>Aprovadas:</strong> {aprovados}</div>
                <div style="flex: 1; color: #dc2626;"><strong>Rejeitadas:</strong> {rejeitados}</div>
                <div style="flex: 1.5; color: #2563eb;"><strong>Vencedor:</strong> {vencedor_nome}</div>
            </div>

            <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 13px;">
                <thead>
                    <tr style="background-color: #f1f5f9; color: #475569;">
                        <th style="padding: 10px; border-bottom: 2px solid #cbd5e1;">Posição</th>
                        <th style="padding: 10px; border-bottom: 2px solid #cbd5e1;">Fornecedor</th>
                        <th style="padding: 10px; border-bottom: 2px solid #cbd5e1;">Nota Final</th>
                        <th style="padding: 10px; border-bottom: 2px solid #cbd5e1;">Status</th>
                        <th style="padding: 10px; border-bottom: 2px solid #cbd5e1;">Observação</th>
                    </tr>
                </thead>
                <tbody>
                    {tabela_linhas_str}
                </tbody>
            </table>

            <p style="margin-top: 25px; font-size: 13px; color: #64748b;">
                📎 <em>Os arquivos <strong>ranking_final.xlsx</strong> e o
                <strong>Dashboard Executivo HTML</strong> foram anexados para auditoria.</em>
            </p>
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">
            <p style="font-size: 11px; color: #94a3b8; margin-bottom: 0;">
                Mensagem gerada automaticamente pelo Pipeline de Hyperautomation LG Electronics.
            </p>
        </div>
    </body>
    </html>
    """

    parte_conteudo = MIMEMultipart("alternative")
    parte_conteudo.attach(MIMEText(corpo_texto, "plain", "utf-8"))
    parte_conteudo.attach(MIMEText(corpo_html, "html", "utf-8"))
    msg.attach(parte_conteudo)

    # Adiciona os arquivos em anexo
    for anexo_path in anexos:
        p = Path(anexo_path)
        if not p.exists():
            continue

        with open(p, "rb") as f:
            mime_attachment = MIMEBase("application", "octet-stream")
            mime_attachment.set_payload(f.read())
            encoders.encode_base64(mime_attachment)
            mime_attachment.add_header(
                "Content-Disposition",
                f'attachment; filename="{p.name}"'
            )
            msg.attach(mime_attachment)

    return msg


def processar_trigger_email(
    email_msg: email.message.Message,
    msg_id: str,
    audit: Optional[AuditLogger] = None,
    output_dir: Optional[Union[str, Path]] = None,
    smtp_client: Optional[smtplib.SMTP] = None,
    enviar_email: bool = True
) -> Tuple[pd.DataFrame, List[Path]]:
    """
    Executa a esteira completa a partir dos anexos extraídos de um e-mail recebido.

    Args:
        email_msg: Objeto do e-mail recebido.
        msg_id: ID do e-mail na caixa postal.
        audit: Instância de AuditLogger para compliance.
        output_dir: Pasta para salvar os anexos baixados e arquivos de saída.
        smtp_client: Conexão SMTP ativa para enviar a resposta (opcional).
        enviar_email: Se True, envia a resposta de e-mail ao remetente.

    Returns:
        Tupla contendo (DataFrame com resultado final, Lista de caminhos dos artefatos anexados).
    """
    if audit is None:
        audit = AuditLogger()

    remetente_raw = email_msg.get("From", "")
    remetente = decodificar_cabecalho(remetente_raw)
    assunto = decodificar_cabecalho(email_msg.get("Subject", "Sem Assunto"))
    message_id_header = email_msg.get("Message-ID")

    logger.info(f"[TRIGGER E-MAIL] Processando mensagem ID {msg_id} de '{remetente}' | Assunto: '{assunto}'")

    if output_dir is None:
        pasta_trabalho = EMAIL_ATTACHMENTS_DIR / f"msg_{msg_id}"
    else:
        pasta_trabalho = Path(output_dir)

    pasta_trabalho.mkdir(parents=True, exist_ok=True)

    # 1. Extração dos anexos do e-mail
    anexos_baixados = extrair_anexos_email(email_msg, pasta_trabalho)

    if not anexos_baixados:
        logger.warning(f"[TRIGGER E-MAIL] Nenhum anexo de proposta válido encontrado no e-mail ID {msg_id}.")
        audit.registrar_erro("TriggerEmail", f"E-mail de {remetente} não continha anexos .xlsx/.csv válidos.")
        df_vazio = pd.DataFrame(columns=["Posicao", "Fornecedor", "Nota_Final", "Status", "Observacao"])
        return df_vazio, []

    # 2. Execução da Pipeline com os anexos do e-mail
    # Etapa 1: Coleta de status web no portal simulado
    _, status_web = coletar_propostas_e_status_web(
        propostas_dir=pasta_trabalho,
        local_path=WEB_PANEL_LOCAL_PATH,
        audit=audit
    )

    # Etapa 2: Leitura das propostas anexadas
    propostas_brutas = ler_todas_propostas(arquivos=anexos_baixados, audit=audit)
    df_criterios = ler_criterios(CRITERIOS_PATH)

    # Etapa 3: Validação das propostas e compliance web
    validas, rejeitadas = validar_todas_propostas(
        propostas=propostas_brutas,
        status_web=status_web,
        audit=audit
    )

    # Etapa 4: Consolidação
    consolidadas = consolidar_propostas(validas)

    # Etapa 5: Ranking MCDA
    df_ranking = calcular_ranking_ponderado(
        propostas=consolidadas,
        df_criterios=df_criterios,
        audit=audit
    )

    # Etapa 6: Geração de Resultado (Excel e Relatório HTML)
    out_excel = pasta_trabalho / "ranking_final.xlsx"
    df_resultado = gerar_resultado_final(
        df_ranking=df_ranking,
        propostas_rejeitadas=rejeitadas,
        output_path=out_excel,
        audit=audit
    )

    out_html = pasta_trabalho / "relatorio_ranking.html"
    anexos_resposta = [out_excel, out_html]

    # Salva auditoria
    audit.salvar_auditoria()

    # 3. Resposta automática por e-mail ao remetente
    if enviar_email and remetente:
        msg_resposta = construir_email_resposta(
            destinatario=remetente,
            assunto_origem=assunto,
            df_resultado=df_resultado,
            anexos=anexos_resposta,
            message_id_origem=message_id_header
        )

        if smtp_client:
            try:
                smtp_client.send_message(msg_resposta)
                logger.info(f"[TRIGGER E-MAIL] Resposta enviada com sucesso para '{remetente}' via SMTP.")
            except Exception as e:
                logger.error(f"[TRIGGER E-MAIL] Falha ao enviar resposta via SMTP para '{remetente}': {e}")
        else:
            logger.info(f"[TRIGGER E-MAIL] Mensagem de resposta construída com sucesso para '{remetente}'.")

    return df_resultado, anexos_resposta


class EmailTriggerService:
    """
    Serviço que gerencia conexões IMAP/SMTP e o ciclo de vida do monitoramento de e-mails.
    """

    def __init__(
        self,
        imap_server: str = EMAIL_IMAP_SERVER,
        imap_port: int = EMAIL_IMAP_PORT,
        imap_ssl: bool = EMAIL_IMAP_SSL,
        smtp_server: str = EMAIL_SMTP_SERVER,
        smtp_port: int = EMAIL_SMTP_PORT,
        smtp_use_tls: bool = EMAIL_SMTP_USE_TLS,
        smtp_use_ssl: bool = EMAIL_SMTP_USE_SSL,
        user: str = EMAIL_USER,
        password: str = EMAIL_PASSWORD,
        subject_trigger: str = EMAIL_SUBJECT_TRIGGER,
        attachments_dir: Path = EMAIL_ATTACHMENTS_DIR
    ):
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.imap_ssl = imap_ssl
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_use_tls = smtp_use_tls
        self.smtp_use_ssl = smtp_use_ssl
        self.user = user
        self.password = password
        self.subject_trigger = subject_trigger
        self.attachments_dir = attachments_dir

    def conectar_imap(self) -> imaplib.IMAP4:
        """Abre conexão autenticada com o servidor IMAP."""
        logger.info(f"[IMAP] Conectando a {self.imap_server}:{self.imap_port} (SSL: {self.imap_ssl})...")
        if self.imap_ssl:
            client = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
        else:
            client = imaplib.IMAP4(self.imap_server, self.imap_port)

        client.login(self.user, self.password)
        logger.info(f"[IMAP] Autenticado com sucesso como '{self.user}'.")
        return client

    def conectar_smtp(self) -> Union[smtplib.SMTP, smtplib.SMTP_SSL]:
        """Abre conexão autenticada com o servidor SMTP."""
        logger.info(f"[SMTP] Conectando a {self.smtp_server}:{self.smtp_port}...")
        if self.smtp_use_ssl:
            client = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
        else:
            client = smtplib.SMTP(self.smtp_server, self.smtp_port)
            if self.smtp_use_tls:
                client.starttls()

        if self.user and self.password:
            client.login(self.user, self.password)
            logger.info(f"[SMTP] Autenticado com sucesso como '{self.user}'.")
        return client

    def buscar_emails_pendentes(
        self,
        imap_client: imaplib.IMAP4,
        pasta: str = "INBOX",
        apenas_nao_lidos: bool = True
    ) -> List[Tuple[str, email.message.Message]]:
        """Busca e-mails na caixa postal que contenham o assunto alvo."""
        imap_client.select(pasta)
        criterio = "(UNSEEN)" if apenas_nao_lidos else "ALL"
        status, data = imap_client.search(None, criterio)

        if status != "OK" or not data or not data[0]:
            return []

        ids = data[0].split()
        emails_encontrados = []

        for msg_id_bytes in ids:
            msg_id = msg_id_bytes.decode()
            status, msg_data = imap_client.fetch(msg_id_bytes, "(RFC822)")
            if status != "OK" or not msg_data:
                continue

            for part in msg_data:
                if isinstance(part, tuple):
                    email_obj = email.message_from_bytes(part[1])
                    assunto = decodificar_cabecalho(email_obj.get("Subject", ""))

                    # Verifica correspondência com o assunto configurado
                    if self.subject_trigger.lower() in assunto.lower():
                        logger.info(f"[TRIGGER E-MAIL] E-mail correspondente encontrado (ID {msg_id}): '{assunto}'")
                        emails_encontrados.append((msg_id, email_obj))
                    else:
                        logger.debug(f"[TRIGGER E-MAIL] E-mail ignorado (assunto diferente): '{assunto}'")

        return emails_encontrados

    def verificar_e_processar(self, marcar_como_lido: bool = True) -> int:
        """Executa uma rodada de verificação e processamento de e-mails."""
        audit = AuditLogger()
        processados = 0

        try:
            imap_client = self.conectar_imap()
        except Exception as e:
            logger.error(f"[IMAP] Falha ao conectar ao servidor de e-mail: {e}")
            return 0

        try:
            pendentes = self.buscar_emails_pendentes(imap_client)
            if not pendentes:
                logger.info("[TRIGGER E-MAIL] Nenhum novo e-mail pendente com o assunto configurado.")
                return 0

            # Conecta SMTP para respostas
            smtp_client = None
            try:
                smtp_client = self.conectar_smtp()
            except Exception as e:
                logger.warning(f"[SMTP] Não foi possível conectar ao SMTP para envio de respostas: {e}")

            for msg_id, email_msg in pendentes:
                try:
                    processar_trigger_email(
                        email_msg=email_msg,
                        msg_id=msg_id,
                        audit=audit,
                        smtp_client=smtp_client,
                        enviar_email=True
                    )
                    processados += 1

                    if marcar_como_lido:
                        imap_client.store(msg_id.encode(), "+FLAGS", "\\Seen")

                except Exception as e:
                    logger.exception(f"[TRIGGER E-MAIL] Erro ao processar e-mail ID {msg_id}: {e}")

            if smtp_client:
                try:
                    smtp_client.quit()
                except Exception:
                    pass

        finally:
            try:
                imap_client.close()
                imap_client.logout()
            except Exception:
                pass

        return processados

    def iniciar_monitoramento(
        self,
        intervalo_segundos: int = 10,
        max_iteracoes: Optional[int] = None
    ) -> None:
        """Inicia loop contínuo de monitoramento da caixa postal."""
        logger.info(
            f"[TRIGGER E-MAIL] Iniciando monitoramento da caixa postal a cada {intervalo_segundos}s "
            f"| Assunto alvo: '{self.subject_trigger}'"
        )
        iteracoes = 0
        try:
            while True:
                iteracoes += 1
                logger.info(f"[TRIGGER E-MAIL] Checando caixa postal (Ciclo #{iteracoes})...")
                total = self.verificar_e_processar()
                if total > 0:
                    logger.info(f"[TRIGGER E-MAIL] Ciclo #{iteracoes}: {total} e-mail(s) processado(s).")

                if max_iteracoes and iteracoes >= max_iteracoes:
                    logger.info(f"[TRIGGER E-MAIL] Limite de {max_iteracoes} iterações atingido. Encerrando.")
                    break

                time.sleep(intervalo_segundos)

        except KeyboardInterrupt:
            logger.info("[TRIGGER E-MAIL] Monitoramento interrompido pelo usuário.")
