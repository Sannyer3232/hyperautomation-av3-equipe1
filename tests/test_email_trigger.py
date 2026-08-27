"""
Testes Unitários e Integrados para o Trigger por E-mail (IMAP / SMTP).
Responsável: Feature Trigger E-mail
"""

from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from unittest.mock import MagicMock, patch
import pandas as pd


from src.email_trigger import (
    EmailTriggerService,
    decodificar_cabecalho,
    extrair_anexos_email,
    construir_email_resposta,
    processar_trigger_email,
)
from src.logger import AuditLogger
from src.config import PROPOSTAS_DIR


class TestDecodificacaoCabecalho:
    """Testes para tratamento de cabeçalhos RFC 2047 e UTF-8."""

    def test_decodificar_texto_simples(self):
        assert decodificar_cabecalho("Assunto Normal") == "Assunto Normal"

    def test_decodificar_none_ou_vazio(self):
        assert decodificar_cabecalho(None) == ""
        assert decodificar_cabecalho("") == ""

    def test_decodificar_rfc2047_utf8(self):
        # "[SELEÇÃO FORNECEDORES]" codificado em RFC 2047
        header = "=?utf-8?q?=5BSELE=C3=87=C3=83O_FORNECEDORES=5D?="
        resultado = decodificar_cabecalho(header)
        assert "SELEÇÃO FORNECEDORES" in resultado


class TestExtracaoAnexosEmail:
    """Testes para extração e filtragem de anexos de propostas."""

    def test_extrair_anexos_validos_e_ignorar_outros(self, tmp_path):
        msg = MIMEMultipart()
        msg["Subject"] = "[SELEÇÃO FORNECEDORES] Novas Cotações"
        msg.attach(MIMEText("Segue em anexo as cotações comerciais.", "plain"))

        # Anexo 1: Excel Válido
        anexo_xlsx = MIMEBase("application", "vnd.ms-excel")
        anexo_xlsx.set_payload(b"conteudo_fake_excel")
        anexo_xlsx.add_header("Content-Disposition", 'attachment; filename="proposta_A.xlsx"')
        msg.attach(anexo_xlsx)

        # Anexo 2: CSV Válido
        anexo_csv = MIMEBase("text", "csv")
        anexo_csv.set_payload(b"Fornecedor,Produto,Custo\nB,Compressor,90\n")
        anexo_csv.add_header("Content-Disposition", 'attachment; filename="proposta_B.csv"')
        msg.attach(anexo_csv)

        # Anexo 3: Imagem / PNG (Deve ser ignorado)
        anexo_png = MIMEBase("image", "png")
        anexo_png.set_payload(b"bytes_imagem")
        anexo_png.add_header("Content-Disposition", 'attachment; filename="logo.png"')
        msg.attach(anexo_png)

        anexos_salvos = extrair_anexos_email(msg, tmp_path)

        assert len(anexos_salvos) == 2
        nomes = [p.name for p in anexos_salvos]
        assert "proposta_A.xlsx" in nomes
        assert "proposta_B.csv" in nomes
        assert "logo.png" not in nomes

        # Confirma existência física dos arquivos
        for p in anexos_salvos:
            assert p.exists()

    def test_extrair_anexos_mensagem_simples_sem_anexo(self, tmp_path):
        msg = MIMEText("E-mail sem anexo nenhum.")
        anexos = extrair_anexos_email(msg, tmp_path)
        assert anexos == []


class TestConstrucaoEmailResposta:
    """Testes para formatação e montagem do e-mail de resposta automática."""

    def test_construir_email_resposta_completo(self, tmp_path):
        df_resultado = pd.DataFrame([
            {
                "Posicao": 1, "Fornecedor": "Fornecedor B", "Nota_Final": 0.6000,
                "Status": "ATIVO", "Observacao": "Proposta válida."
            },
            {
                "Posicao": 2, "Fornecedor": "Fornecedor A", "Nota_Final": 0.5479,
                "Status": "ATIVO", "Observacao": "Proposta válida."
            },
            {
                "Posicao": "-", "Fornecedor": "Fornecedor D", "Nota_Final": "-",
                "Status": "BLOQUEADO", "Observacao": "Custo negativo."
            }
        ])

        # Cria arquivos temporários de anexo
        arq_excel = tmp_path / "ranking_final.xlsx"
        arq_excel.write_bytes(b"excel_bytes")
        arq_html = tmp_path / "relatorio_ranking.html"
        arq_html.write_text("<html>Dashboard</html>", encoding="utf-8")

        msg = construir_email_resposta(
            destinatario="comprador@empresa.com",
            assunto_origem="[SELEÇÃO FORNECEDORES] RFQ Compressor",
            df_resultado=df_resultado,
            anexos=[arq_excel, arq_html],
            message_id_origem="<msg123@empresa.com>"
        )

        assert msg["To"] == "comprador@empresa.com"
        assert msg["Subject"] == "Re: [SELEÇÃO FORNECEDORES] RFQ Compressor"
        assert msg["In-Reply-To"] == "<msg123@empresa.com>"

        # Verifica conteúdo e anexos
        payload_parts = list(msg.walk())
        assert len(payload_parts) > 2  # Container + alternativo + 2 anexos


class TestProcessamentoTriggerEmail:
    """Testes integrados do fluxo de processamento de um e-mail com propostas reais."""

    def test_processar_trigger_email_com_anexos_reais(self, tmp_path):
        audit = AuditLogger()
        mock_smtp = MagicMock()

        # Monta um e-mail com as 4 propostas reais dos resources
        msg = MIMEMultipart()
        msg["From"] = "gestor.suprimentos@empresa.com"
        msg["Subject"] = "[SELEÇÃO FORNECEDORES] Propostas Compressores Q3"
        msg["Message-ID"] = "<cotacoes_2026@empresa.com>"

        for p_file in PROPOSTAS_DIR.glob("*.*"):
            if p_file.suffix.lower() in [".xlsx", ".csv"]:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(p_file.read_bytes())
                part.add_header("Content-Disposition", f'attachment; filename="{p_file.name}"')
                msg.attach(part)

        pasta_execucao = tmp_path / "email_job"
        df_resultado, anexos = processar_trigger_email(
            email_msg=msg,
            msg_id="101",
            audit=audit,
            output_dir=pasta_execucao,
            smtp_client=mock_smtp,
            enviar_email=True
        )

        # Valida que todos os 4 fornecedores foram avaliados
        assert len(df_resultado) == 4
        assert list(df_resultado["Fornecedor"]) == ["Fornecedor B", "Fornecedor A", "Fornecedor C", "Fornecedor D"]
        assert df_resultado.iloc[0]["Status"] == "ATIVO"
        assert df_resultado.iloc[0]["Fornecedor"] == "Fornecedor B"
        assert df_resultado.iloc[3]["Status"] == "BLOQUEADO"

        # Valida anexos gerados
        assert len(anexos) == 2
        for anexo in anexos:
            assert anexo.exists()

        # Valida que o SMTP disparou a resposta para o remetente
        mock_smtp.send_message.assert_called_once()
        msg_enviada = mock_smtp.send_message.call_args[0][0]
        assert msg_enviada["To"] == "gestor.suprimentos@empresa.com"
        assert "Re: [SELEÇÃO FORNECEDORES]" in msg_enviada["Subject"]

    def test_processar_trigger_email_sem_anexos_validos(self, tmp_path):
        audit = AuditLogger()
        mock_smtp = MagicMock()

        msg = MIMEMultipart()
        msg["From"] = "usuario@empresa.com"
        msg["Subject"] = "[SELEÇÃO FORNECEDORES] Sem anexos"
        msg.attach(MIMEText("Esqueci os anexos.", "plain"))

        df_resultado, anexos = processar_trigger_email(
            email_msg=msg,
            msg_id="102",
            audit=audit,
            output_dir=tmp_path / "vazio",
            smtp_client=mock_smtp,
            enviar_email=True
        )

        assert df_resultado.empty
        assert anexos == []
        assert len(audit.erros) > 0


class TestEmailTriggerService:
    """Testes do serviço gerenciador de IMAP/SMTP."""

    @patch("imaplib.IMAP4_SSL")
    def test_buscar_emails_pendentes_filtra_por_assunto(self, mock_imap_ssl):
        service = EmailTriggerService(subject_trigger="[SELEÇÃO FORNECEDORES]")

        # Mensagem 1: Assunto alvo correto
        msg1 = MIMEMultipart()
        msg1["Subject"] = "[SELEÇÃO FORNECEDORES] Cotação Aprovada"

        # Mensagem 2: Assunto não relacionado
        msg2 = MIMEMultipart()
        msg2["Subject"] = "Reunião de Alinhamento Semanal"

        mock_client = MagicMock()
        mock_client.search.return_value = ("OK", [b"1 2"])
        mock_client.fetch.side_effect = [
            ("OK", [(b"1 (RFC822 {100}", msg1.as_bytes())]),
            ("OK", [(b"2 (RFC822 {100}", msg2.as_bytes())]),
        ]

        encontrados = service.buscar_emails_pendentes(mock_client)
        assert len(encontrados) == 1
        assert encontrados[0][0] == "1"

    @patch.object(EmailTriggerService, "conectar_imap")
    @patch.object(EmailTriggerService, "conectar_smtp")
    @patch("src.email_trigger.service.processar_trigger_email")
    def test_verificar_e_processar_ciclo_completo(self, mock_processar, mock_smtp, mock_imap):
        service = EmailTriggerService(subject_trigger="[SELEÇÃO FORNECEDORES]")

        msg = MIMEMultipart()
        msg["Subject"] = "[SELEÇÃO FORNECEDORES] Teste"

        mock_imap_client = MagicMock()
        mock_imap.return_value = mock_imap_client

        with patch.object(service, "buscar_emails_pendentes", return_value=[("105", msg)]):
            total = service.verificar_e_processar(marcar_como_lido=True)

        assert total == 1
        mock_processar.assert_called_once()
        mock_imap_client.store.assert_called_once_with(b"105", "+FLAGS", "\\Seen")

    @patch.object(EmailTriggerService, "verificar_e_processar", return_value=1)
    def test_iniciar_monitoramento_limite_iteracoes(self, mock_verificar):
        service = EmailTriggerService()
        # Executa exatamente 2 iterações e encerra
        service.iniciar_monitoramento(intervalo_segundos=0, max_iteracoes=2)
        assert mock_verificar.call_count == 2
