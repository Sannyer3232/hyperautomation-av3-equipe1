"""
Módulo de Configuração Central do Projeto.
Carrega variáveis de ambiente (.env) e define caminhos e constantes.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

# Diretório raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# Timezone obrigatório para o projeto
TZ = os.getenv("TZ", "America/Manaus")
os.environ["TZ"] = TZ

# Configurações do Painel Web Simulado
WEB_PANEL_URL = os.getenv(
    "WEB_PANEL_URL",
    "http://localhost:8000/resources/01_SELECAO_FORNECEDORES/web/painel_fornecedores_fake.html"
)
WEB_PANEL_LOCAL_PATH = Path(
    os.getenv(
        "WEB_PANEL_LOCAL_PATH",
        str(BASE_DIR / "resources" / "01_SELECAO_FORNECEDORES" / "web" / "painel_fornecedores_fake.html")
    )
)

# Diretórios e Arquivos de Entrada
RESOURCES_DIR = Path(
    os.getenv("RESOURCES_DIR", str(BASE_DIR / "resources" / "01_SELECAO_FORNECEDORES"))
)
PROPOSTAS_DIR = Path(
    os.getenv("PROPOSTAS_DIR", str(RESOURCES_DIR / "propostas"))
)
CRITERIOS_PATH = Path(
    os.getenv("CRITERIOS_PATH", str(RESOURCES_DIR / "criterios_ranking.xlsx"))
)
MODELO_RANKING_PATH = Path(
    os.getenv("MODELO_RANKING_PATH", str(RESOURCES_DIR / "modelo_ranking.xlsx"))
)

# Diretórios de Saída e Logs
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", str(BASE_DIR / "output")))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_RANKING_PATH = Path(
    os.getenv("OUTPUT_RANKING_PATH", str(OUTPUT_DIR / "ranking_final.xlsx"))
)

LOGS_DIR = Path(os.getenv("LOGS_DIR", str(BASE_DIR / "logs")))
LOGS_DIR.mkdir(parents=True, exist_ok=True)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Configurações do Trigger por E-mail (IMAP / SMTP)
EMAIL_IMAP_SERVER = os.getenv("EMAIL_IMAP_SERVER", "imap.gmail.com")
EMAIL_IMAP_PORT = int(os.getenv("EMAIL_IMAP_PORT", "993"))
EMAIL_IMAP_SSL = os.getenv("EMAIL_IMAP_SSL", "true").lower() in ["true", "1", "yes"]

EMAIL_SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587"))
EMAIL_SMTP_USE_TLS = os.getenv("EMAIL_SMTP_USE_TLS", "true").lower() in ["true", "1", "yes"]
EMAIL_SMTP_USE_SSL = os.getenv("EMAIL_SMTP_USE_SSL", "false").lower() in ["true", "1", "yes"]

EMAIL_USER = os.getenv("EMAIL_USER", os.getenv("EMAIL_IMAP_USER", "rpa.suprimentos@empresa.com"))
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", os.getenv("EMAIL_IMAP_PASSWORD", ""))

EMAIL_SUBJECT_TRIGGER = os.getenv("EMAIL_SUBJECT_TRIGGER", "[SELEÇÃO FORNECEDORES]")
EMAIL_ATTACHMENTS_DIR = Path(os.getenv("EMAIL_ATTACHMENTS_DIR", str(OUTPUT_DIR / "email_anexos")))
EMAIL_ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)
EMAIL_POLL_INTERVAL = int(os.getenv("EMAIL_POLL_INTERVAL", "10"))
TRIGGER_MODE = os.getenv("TRIGGER_MODE", "diretorio")  # 'diretorio' ou 'email'

# Pesos Padrão de Negócio (caso o arquivo não seja encontrado)
DEFAULT_WEIGHTS = {
    "Custo": {"peso": 0.40, "direcao": "Menor"},
    "Prazo_Dias": {"peso": 0.25, "direcao": "Menor"},
    "Capacidade": {"peso": 0.20, "direcao": "Maior"},
    "Qualidade": {"peso": 0.15, "direcao": "Maior"}
}
