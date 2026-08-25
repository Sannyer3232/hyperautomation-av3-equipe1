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

# Pesos Padrão de Negócio (caso o arquivo não seja encontrado)
DEFAULT_WEIGHTS = {
    "Custo": {"peso": 0.40, "direcao": "Menor"},
    "Prazo_Dias": {"peso": 0.25, "direcao": "Menor"},
    "Capacidade": {"peso": 0.20, "direcao": "Maior"},
    "Qualidade": {"peso": 0.15, "direcao": "Maior"}
}
