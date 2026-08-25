# Base Image
FROM python:3.12-slim

# Metadados
LABEL maintainer="Equipe Hyperautomation <equipe@hyperautomation.local>"
LABEL description="Robô de Automação Inteligente para Seleção de Fornecedores LG Electronics"

# Definir Timezone exigido: America/Manaus
ENV TZ=America/Manaus
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Instalar pacotes de sistema e configuração de timezone
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    curl \
    && ln -fs /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && dpkg-reconfigure --frontend noninteractive tzdata \
    && rm -rf /var/lib/apt/lists/*

# Diretório de trabalho
WORKDIR /app

# Copiar arquivos de dependência primeiro (otimização de cache)
COPY requirements.txt requirements-dev.txt ./

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código-fonte, recursos e configurações
COPY src/ ./src/
COPY resources/ ./resources/
COPY tests/ ./tests/
COPY pytest.ini .env.example ./

# Criar diretórios de logs e saída com permissões adequadas
RUN mkdir -p output logs

# Comando padrão de execução do robô
CMD ["python", "src/main.py"]
