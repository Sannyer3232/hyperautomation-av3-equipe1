# 🎓 GUIA OFICIAL DE DEFESA TÉCNICA — AVALIAÇÃO 03 (PARTE 2)
## Automação Inteligente do Processo de Seleção de Fornecedores (LG Electronics)

- **Disciplina:** Técnicas de Hyperautomation
- **Professor:** Prof. Moisés Levy
- **Equipe:** Equipe 01 | Turma: T02 (Agosto/2026)
- **Arquivo de Apresentação:** [`docs/Apresentacao_Defesa_Hyperautomation_LG_Equipe01.pptx`](file:///C:/Users/Turma02/Documents/Sannyer%20Carvalho/hyperautomation-av3/docs/Apresentacao_Defesa_Hyperautomation_LG_Equipe01.pptx)

---

## 👥 1. Divisão da Apresentação em 4 Integrantes

A apresentação foi estruturada de forma lógica e equilibrada para **4 pessoas**, cobrindo a narrativa completa:
$$\text{PROBLEMA} \rightarrow \text{SOLUÇÃO} \rightarrow \text{AUTOMAÇÃO} \rightarrow \text{TESTES} \rightarrow \text{DOCKER} \rightarrow \text{CI/CD} \rightarrow \text{GHCR} \rightarrow \text{EXECUÇÃO} \rightarrow \text{RESULTADO}$$

| Integrante | Papel na Apresentação | Slides Teóricos | Etapa na Demonstração Prática |
| :--- | :--- | :--- | :--- |
| **👤 Integrante 1** | **Líder de Negócio & AS-IS / TO-BE** | Slides 1, 2 e 3 | **Etapa 1:** Apresentação do repositório, governança e estrutura de pastas. |
| **👤 Integrante 2** | **Engenheiro de Automação & Ingestão de Dados** | Slides 4, 5 e 6 | **Etapa 2:** Execução da pipeline (`main.py`), scraping Playwright e leitura multiformato. |
| **👤 Integrante 3** | **Especialista em Qualidade, Exceções & MCDA** | Slides 7, 8 e 9 | **Etapa 3:** Execução dos testes automatizados (`pytest`), rejeição Fornecedor D e algoritmo MCDA. |
| **👤 Integrante 4** | **Arquiteto DevOps, CI/CD & Auditoria** | Slides 10, 11, 12 e 13 | **Etapas 4 a 7:** GitHub Actions, GHCR, execução Docker, `auditoria.json` e planilha final. |

---

## 🗣️ 2. Roteiro de Fala Completo (Slide a Slide)

### 👤 INTEGRANTE 1 — Visão Executiva, Contexto de Negócio & Arquitetura TO-BE

#### **Slide 1 — Identificação do Projeto & Equipe**
> *"Boa tarde, professor Moisés Levy e colegas. Nós somos a **Equipe 01** e vamos apresentar a defesa técnica da Avaliação 3 da disciplina de **Técnicas de Hyperautomation**.*
>
> *O nosso projeto é a **Automação Inteligente do Processo de Seleção de Fornecedores Industriais para a LG Electronics do Brasil**. Desenvolvemos uma solução robusta e auditável de ponta a ponta que integra RPA com Playwright, Processamento Inteligente de Documentos (IDP), Algoritmo de Decisão Multicritério (MCDA), containerização em Docker e esteira completa de CI/CD publicada no GitHub Container Registry.*
>
> *Nossa apresentação está dividida em quatro partes equilibradas, seguida de uma demonstração prática ao vivo."*

#### **Slide 2 — O Problema de Negócio: Processo Manual AS-IS**
> *"Para entender o valor da nossa solução, precisamos olhar para o cenário anterior na LG Electronics em Manaus.*
>
> *No modelo **AS-IS manual**, o processo de cotação era fragmentado: os compradores enviavam RFQs por e-mail e recebiam propostas em formatos completamente dispersos — planilhas Excel e arquivos CSV. O comprador precisava transcrever manualmente cada preço, prazo e capacidade para uma planilha de controle, calcular o custo total de posse (TCO) através de fórmulas manuais e consultar o status de cada fornecedor em portais web externos.*
>
> *Esse fluxo gerava três grandes vulnerabilidades:*
> 1. *Risco de erro humano de até 12% na digitação de valores e fórmulas;*
> 2. *Ciclo de compras moroso, levando de 5 a 10 dias úteis;*
> 3. *Falta de conformidade e rastreabilidade para auditorias da Lei Sarbanes-Oxley (SOX), já que não existiam logs estruturados de auditoria."*

#### **Slide 3 — A Solução Proposta: Hyperautomation TO-BE**
> *"Para resolver esse gargalo, projetamos uma arquitetura de **Hyperautomation TO-BE** estruturada em três pilares fundamentais:*
>
> 1. ***Ingestão & Automação Robótica (RPA):** O robô faz a varredura automática dos diretórios, ingere múltiplos formatos sem intervenção humana e utiliza um navegador headless Playwright para consultar o status cadastral dos fornecedores no portal corporativo com fallback inteligente.*
> 2. ***Validação Técnica & Motor de Decisão:** Implementamos um gateway de validação em duas camadas (cadastral e integridade numérica) acoplado a um algoritmo MCDA de scoring relativo ponderado.*
> 3. ***Governança & Auditoria Digital:** Geração automática da planilha oficial homologada (`ranking_final.xlsx`) e persistência de um snapshot JSON de auditoria (`auditoria.json`) com rastreabilidade completa.*
>
> *Passo a palavra agora para o **Integrante 2**, que apresentará a arquitetura técnica e o fluxo do pipeline."*

---

### 👤 INTEGRANTE 2 — Pipeline de Automação, Ingestão & Cenário Normal

#### **Slide 4 — Fluxo da Solução: Pipeline Modular em 6 Etapas**
> *"Obrigado. O coração da nossa aplicação foi desenhado seguindo o padrão de **Pipeline Sequencial em 6 Etapas Modulares**, garantindo isolamento de responsabilidades e facilidade de testes:*
>
> - ***Etapa 1 (Coleta):** Varredura de propostas no diretório e automação web RPA com Playwright para extrair o status dos fornecedores no portal corporativo.*
> - ***Etapa 2 (Leitura):** Ingestão com tolerância a delimitadores (ponto-e-vírgula e vírgula), encodings e normalização automática de sinônimos de cabeçalhos.*
> - ***Etapa 3 (Validação):** Checagem rigorosa de regras de negócio, bloqueando fornecedores inaptos ou com valores negativos.*
> - ***Etapa 4 (Consolidação):** Agrupamento dos dados válidos e tipagem estrita em DataFrame pandas.*
> - ***Etapa 5 (Ranking MCDA):** Aplicação das fórmulas de normalização e pesos de negócio.*
> - ***Etapa 6 (Resultado & Auditoria):** Preenchimento do template oficial da LG e gravação do log de auditoria.*
>
> *Essa modularidade assegura que se qualquer etapa falhar, o erro é isolado e logado sem derrubar o sistema."*

#### **Slide 5 — Stack Tecnológico e Integração dos Componentes**
> *"Nossa stack tecnológica foi selecionada com foco em performance, modernidade e padrões de engenharia de software:*
>
> - ***Python 3.12:** Linguagem base, utilizando tipagem estrita (`typing`) e orquestração limpa.*
> - ***Playwright (Chromium RPA):** Escolhido em substituição ao Selenium/BotCity pela execução headless ultrarrápida, seletores modernos e estabilidade nativa no tratamento de eventos assíncronos.*
> - ***Pandas & OpenPyXL:** Manipulação vetorial e preenchimento de templates Excel.*
> - ***Pytest & Pytest-Cov:** Suíte com 51 testes automatizados e relatório de cobertura.*
> - ***Docker & Docker Compose:** Containerização multi-serviço com fuso horário `America/Manaus`.*
> - ***GitHub Actions & GHCR:** Esteira automatizada de CI/CD e publicação de imagem no registro oficial do GitHub."*

#### **Slide 6 — Cenário de Execução Normal (Caminho Feliz)**
> *"No **Cenário Normal de Execução**, demonstramos o processamento das propostas dos fornecedores válidos: A, B e C.*
>
> *O robô identifica os arquivos `proposta_fornecedor_A.xlsx`, `proposta_fornecedor_B.csv` e `proposta_fornecedor_C.xlsx`. Na etapa web, o Playwright acessa a tabela HTML e valida que os três possuem status **'Ativo'**.*
>
> *Após a extração e validação, os dados são consolidados e processados pelo motor MCDA:*
> - *O **Fornecedor B** é classificado em **1º Lugar** (Score: 92.98) por apresentar o menor custo de mercado (R$ 90) e a maior capacidade produtiva (700 unidades).*
> - *O **Fornecedor A** fica em **2º Lugar** (Score: 89.28) com uma proposta intermediária equilibrada.*
> - *O **Fornecedor C** fica em **3º Lugar** (Score: 88.08), pois embora tenha o melhor prazo e qualidade, seu custo é mais elevado (R$ 110).*
>
> *O resultado é gravado no template oficial. Passo a palavra para o **Integrante 3** para falar sobre exceções e testes."*

---

### 👤 INTEGRANTE 3 — Gestão de Exceções, Resiliência, Testes & Algoritmo MCDA

#### **Slide 7 — Tratamento de Exceções, Resiliência e Barramentos**
> *"Obrigado. Uma solução de Hyperautomation não pode ser desenvolvida apenas para o 'caminho feliz'. Implementamos mecanismos avançados para tratamento de anomalias e contingência de rede.*
>
> *No caso do **Fornecedor D (`proposta_invalida_fornecedor_D.xlsx`)**, nosso robô aplica uma **dupla barreira de proteção**:*
> 1. ***Barreira Cadastral Web:** O Playwright identifica no portal web que o Fornecedor D está com status **'Bloqueado'**.*
> 2. ***Barreira de Integridade Numérica:** O validador detecta valores negativos absurdos (`Custo: -50`, `Prazo: -2`, `Capacidade: -100`).*
>
> *Aplicamos o padrão de arquitetura **Data Filtering Gateway**: a proposta inválida é isolada imediatamente, não entra no cálculo relativo do MCDA (evitando distorcer as notas dos concorrentes) e figura no ranking final como **'Desclassificado' (Nota 0.00)** com justificativa técnica.*
>
> *Além disso, criamos uma **Resiliência Multi-Camada de Rede**: se o servidor web HTTP na porta 8000 estiver fora do ar, o Playwright migra automaticamente para o protocolo `file://` em nova aba; se o Chromium sofrer falha de SO, o sistema aciona fallback com `requests + BeautifulSoup` ou leitura direta em disco, garantindo 0% de parada na fábrica."*

#### **Slide 8 — Suíte de Testes Automatizados com Pytest**
> *"Para garantir que a solução funciona e não sofre regressão, desenvolvemos uma suíte de **51 testes automatizados** com Pytest:*
>
> - ***test_coleta.py (24 testes):** Testa varredura de diretório, filtros de arquivos de lock temporários (`~$*`), extração Playwright, transição de abas e falhas simuladas de rede.*
> - ***test_leitura.py (25 testes):** Testa ingestão de planilhas Excel e CSV com delimitadores `;` e `,`, diferentes encodings, tolerância a cabeçalhos e fallbacks de critérios.*
> - ***test_integration.py (2 testes):** Testa o fluxo integrado de ponta a ponta e o orquestrador principal `main.py`.*
>
> *O comando `python -m pytest -v` executa todos os 51 testes em aproximadamente 35 segundos com **100% de taxa de aprovação** e cobertura de código completa nos módulos de negócio."*

#### **Slide 9 — Motor de Decisão Multicritério: Algoritmo MCDA**
> *"Nosso motor de decisão utiliza o método **MCDA (Multi-Criteria Decision Analysis)** para ponderar múltiplos atributos conflitantes:*
>
> *Os pesos oficiais são carregados dinamicamente do arquivo `criterios_ranking.xlsx`:*
> - ***Custo (Peso 0.40 / 40%):** Direção 'Menor é Melhor';*
> - ***Prazo (Peso 0.25 / 25%):** Direção 'Menor é Melhor';*
> - ***Capacidade (Peso 0.20 / 20%):** Direção 'Maior é Melhor';*
> - ***Qualidade (Peso 0.15 / 15%):** Direção 'Maior é Melhor';*
>
> *A normalização relativa calcula a nota de 0 a 100 com base no benchmark real do mercado. Para critérios de menor valor, calculamos $(\text{Menor Valor} / \text{Valor da Proposta}) \times 100$. Para critérios de maior valor, calculamos $(\text{Valor da Proposta} / \text{Maior Valor}) \times 100$. O score global é a soma ponderada de cada critério.*
>
> *Passo a palavra agora para o **Integrante 4**, que apresentará a arquitetura de Docker, CI/CD, GHCR e Auditoria."*

---

### 👤 INTEGRANTE 4 — Infraestrutura Docker, CI/CD GitHub Actions, GHCR & Governança

#### **Slide 10 — Containerização Docker & Docker Compose**
> *"Obrigado. Para garantir portabilidade e isolamento total, containerizamos a aplicação atendendo a todos os requisitos do edital:*
>
> - ***Dockerfile:** Baseado em `python:3.12-slim`, instalando dependências de sistema e o Chromium do Playwright de forma otimizada.*
> - ***Timezone Corporativo:** Configuração explícita de `TZ=America/Manaus` via `tzdata` e variáveis de ambiente, garantindo que os timestamps de logs e auditoria reflitam o horário local da fábrica.*
> - ***Volumes Persistentes:** Mapeamento de `./output` para exportação da planilha e `./logs` para persistência dos logs fora do container.*
> - ***Docker Compose:** Orquestração multi-serviço contendo o serviço `web-panel` (disponibilizando o portal na porta 8000) e o serviço `robot` (que aguarda o portal subir e executa a automação).*
>
> *Com o comando `docker compose up --build`, qualquer operador sobe o ambiente completo com um único comando."*

#### **Slide 11 — Pipeline de CI/CD (GitHub Actions) & Publicação no GHCR**
> *"Implementamos uma esteira de **Integração Contínua (CI/CD)** completa no GitHub Actions através do arquivo `.github/workflows/ci.yml`:*
>
> 1. ***Gatilhos Automáticos:** Disparados em cada `git push` e `pull request` nas branches `main`, `develop` e `feature/**`.*
> 2. ***Job de Qualidade & Testes:** Faz o checkout, instala dependências, roda a verificação estrita de linting com `flake8` (0 erros) e executa os 51 testes Pytest com relatório de cobertura.*
> 3. ***Job de Build & Publicação:** Após a aprovação dos testes, a imagem Docker é construída e publicada no **GitHub Container Registry (`ghcr.io`)**.*
>
> *Em conformidade com o edital, **não utilizamos Docker Hub**, mas sim o GHCR corporativo. Em produção, a aplicação é executada via `docker pull ghcr.io/sannyer3232/hyperautomation-av3-equipe1:latest` e `docker run`."*

#### **Slide 12 — Rastreabilidade Digital, Logs e Auditoria SOX**
> *"A conformidade e governança da solução são asseguradas por dois mecanismos complementares:*
>
> 1. ***Trilha de Auditoria SOX (`logs/auditoria.json`):** Snapshot estruturado contendo carimbo de data/hora ISO 8601 de Manaus, lista de arquivos processados, dados das propostas aprovadas, justificativa técnica da desclassificação do Fornecedor D e a memória de cálculo completa dos scores ponderados.*
> 2. ***Log Operacional Contínuo (`logs/execucao.log`):** Rastreabilidade em tempo real com 4 níveis de severidade padronizados: `INFO` para fluxos normais, `WARNING` para contingência e rejeições, `ERROR` para falhas de leitura e `CRITICAL` para exceções fatais.*
>
> *A planilha oficial gerada em `output/ranking_final.xlsx` preenche com precisão o modelo exigido pela LG."*

#### **Slide 13 — Conclusão e Entrega de Valor para o Negócio**
> *"Para concluir nossa apresentação teórica, sintetizamos o valor entregue pela solução nas 5 perguntas essenciais:*
>
> 1. ***O que desenvolvemos?** Uma esteira autônoma de Hyperautomation com RPA, IA/MCDA, Docker e CI/CD.*
> 2. ***Qual problema foi resolvido?** Fim da digitação manual de propostas, eliminação de erros de cálculo e bloqueio imediato de fornecedores inaptos.*
> 3. ***Como funciona?** Pipeline de 6 etapas que coleta, lê, valida, consolida, ranqueia e homologa fornecedores de ponta a ponta.*
> 4. ***Qual resultado obtido?** Redução do tempo de processamento de 8 horas para 25 segundos, com 100% de acurácia matemática.*
> 5. ***Qual valor entregue para a LG?** Decisões objetivas de compras, rastreabilidade total para auditorias SOX e alta escalabilidade operacional.*
>
> *Vamos agora dar início à demonstração prática ao vivo."*

---

## 💻 3. Roteiro Cronometrado da Demonstração Prática (7 Etapas Obrigatórias)

| Etapa | Responsável | Ação ao Vivo no Computador | O que Falar / Mostrar na Tela |
| :---: | :---: | :--- | :--- |
| **ETAPA 1<br>Código** | **👤 Integrante 1** | Abrir o VS Code e repositório GitHub. | • Mostrar a árvore de diretórios (`src/`, `tests/`, `resources/`, `docs/`, `.github/`).<br>• Explicar os arquivos `config.py`, `logger.py` e `.flake8`. |
| **ETAPA 2<br>Execução** | **👤 Integrante 2** | No terminal, executar:<br>`python src/main.py` | • Mostrar a execução do robô no terminal.<br>• Explicar os logs em tempo real: coleta Playwright RPA, leitura das 4 propostas e cálculo. |
| **ETAPA 3<br>Testes** | **👤 Integrante 3** | No terminal, executar:<br>`python -m pytest -v` | • Mostrar os 51 testes passando em verde.<br>• Explicar que foram testados cenários válidos, dados negativos, scraping web e fallback. |
| **ETAPA 4<br>CI/CD** | **👤 Integrante 4** | Abrir o navegador no GitHub Actions. | • Mostrar o workflow `.github/workflows/ci.yml` com status verde (Checks aprovados).<br>• Explicar as etapas: Lint Flake8 $\rightarrow$ Pytest $\rightarrow$ Docker Build. |
| **ETAPA 5<br>GHCR** | **👤 Integrante 4** | Abrir a aba *Packages* do repositório no GitHub. | • Mostrar o pacote Docker publicado no **GitHub Container Registry (`ghcr.io`)**. |
| **ETAPA 6<br>Docker** | **👤 Integrante 4** | No terminal, executar:<br>`docker compose up --build` *(ou `docker run`)* | • Mostrar a execução em container com timezone `America/Manaus` e persistência em volumes. |
| **ETAPA 7<br>Resultados** | **👥 Todos** | Abrir os arquivos gerados no VS Code/Excel: | 1. `output/ranking_final.xlsx` (1º B, 2º A, 3º C, Desclassificado D).<br>2. `logs/auditoria.json` (Trilha SOX e scores parciais).<br>3. `logs/execucao.log` (Severidades INFO e WARNING). |

---

## 🎯 4. Perguntas Prováveis da Banca (Prof. Moisés Levy) & Respostas Rápidas

### P1: *"Por que utilizaram Playwright em vez de Selenium ou BotCity?"*
> **Resposta (👤 Integrante 2):**
> *"O Playwright oferece execução nativa assíncrona e headless extremamente rápida, com gerenciamento automático de esperas do DOM (`auto-wait`), sem depender de WebDrivers externos instáveis. Além disso, permite a manipulação de contextos isolados de abas para implementação ágil de fallbacks."*

### P2: *"Como o robô identifica uma proposta inválida e por que o Fornecedor D foi rejeitado?"*
> **Resposta (👤 Integrante 3):**
> *"O Fornecedor D sofreu dupla rejeição: primeiro na checagem cadastral web, onde o Playwright capturou seu status como 'Bloqueado' no portal; segundo na validação técnica de integridade, onde foram detectados valores negativos (`Custo: -50`, `Prazo: -2`, `Capacidade: -100`). Propostas inválidas são filtradas antes do cálculo do ranking para não contaminar a nota dos concorrentes."*

### P3: *"Como funciona o cálculo de ranking e a normalização de pesos?"*
> **Resposta (👤 Integrante 3):**
> *"Utilizamos o modelo MCDA com pesos carregados da planilha `criterios_ranking.xlsx` (Custo 40%, Prazo 25%, Capacidade 20%, Qualidade 15%). Para critérios em que 'Menor é Melhor' (Custo e Prazo), a fórmula é $(\text{Menor Valor} / \text{Valor da Proposta}) \times 100$. Para critérios em que 'Maior é Melhor' (Capacidade e Qualidade), é $(\text{Valor da Proposta} / \text{Maior Valor}) \times 100$. A nota final é a soma ponderada das 4 notas normalizadas."*

### P4: *"O que acontece se o servidor web HTTP (porta 8000) estiver indisponível?"*
> **Resposta (👤 Integrante 2 / 3):**
> *"Implementamos uma arquitetura de resiliência multi-camada: se a URL `http://localhost:8000/...` der timeout ou connection refused, o robô abre uma nova página no Playwright com o protocolo local `file:///...`. Se houver falha de renderizador gráfico, o robô aciona o fallback com `requests + BeautifulSoup` ou leitura direta em disco, garantindo que o processo não seja interrompido."*

### P5: *"O que está armazenado em Volumes e em Variáveis de Ambiente no Docker?"*
> **Resposta (👤 Integrante 4):**
> *"Em **Volumes** mapeamos os diretórios persistentes `./output` (onde a planilha final `ranking_final.xlsx` é salva) e `./logs` (onde ficam `execucao.log` e `auditoria.json`), garantindo que os dados não se percam quando o container for destruído. Em **Variáveis de Ambiente** definimos `TZ=America/Manaus` para fixar o fuso horário oficial da fábrica e os caminhos de configuração."*

### P6: *"Qual a diferença entre o arquivo `execucao.log` e o `auditoria.json`?"*
> **Resposta (👤 Integrante 4):**
> *"O `execucao.log` é um log textual contínuo para diagnóstico de infraestrutura e suporte de TI, registrando eventos com severidades `INFO`, `WARNING`, `ERROR` e `CRITICAL`. Já o `auditoria.json` é um artefato de governança corporativa e compliance SOX, contendo um snapshot estruturado com todas as propostas processadas, justificativas de desclassificação e a memória matemática de cálculo."*

### P7: *"Onde ocorre a validação humana no processo?"*
> **Resposta (👤 Integrante 1):**
> *"A validação humana ocorre na etapa de aprovação formal de homologação e na análise das propostas desclassificadas. O robô automatiza 100% da coleta, conferência cadastral, cálculo e ordenação, gerando o parecer oficial pré-preenchido. O gestor de suprimentos assume a partir da planilha gerada para emitir o pedido de compra (PO) no ERP corporativo (SAP)."*

---

## 📋 5. Checklist Final Pré-Apresentação

- [x] Apresentação PowerPoint gerada e conferida: [`docs/Apresentacao_Defesa_Hyperautomation_LG_Equipe01.pptx`](file:///C:/Users/Turma02/Documents/Sannyer%20Carvalho/hyperautomation-av3/docs/Apresentacao_Defesa_Hyperautomation_LG_Equipe01.pptx)
- [x] Todos os 51 testes automatizados passando localmente (`python -m pytest`)
- [x] Linting sem nenhum erro (`flake8 src tests`)
- [x] Execução do pipeline principal testada (`python src/main.py`)
- [x] Docker e Docker Compose testados (`docker compose up --build`)
- [x] Workflow do GitHub Actions verde no repositório
- [x] Imagem publicada no GitHub Container Registry (GHCR)
- [x] Divisão e ensaio do roteiro de fala entre os 4 integrantes
