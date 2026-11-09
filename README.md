# SplitAgent — Back-End

O **SplitAgent** é uma solução de inteligência financeira desenvolvida para auxiliar pequenos negócios na organização, análise e planejamento de suas finanças. O projeto foi desenvolvido pela equipe **ThreeValley**, em parceria com a IBM e o Banco do Brasil.

Este repositório contém o back-end da aplicação: uma API REST responsável pelo processamento das informações financeiras, gerenciamento de usuários, cálculos, simulações e integração dos agentes inteligentes.

O desenvolvimento do back-end foi realizado por **Tiago Pereira Dias**, abrangendo a arquitetura da API, implementação das regras de negócio, integração com banco de dados, autenticação, serviços financeiros, agentes especializados e integração com inteligência artificial.

## Acesse o projeto

- **Aplicação Web e PWA:** https://splitagent.vercel.app/
- **Documentação da API (Swagger):** https://ibm-splitagent-back-end-production.up.railway.app/docs
- **Repositório Back-End:** https://github.com/Tiasgod/IBM-SplitAgent---Back-End
- **Desenvolvedor:** [Tiasgod](https://github.com/Tiasgod)

## Sobre o Back-End

O back-end foi desenvolvido em Python utilizando FastAPI e segue uma arquitetura organizada em camadas, separando rotas, modelos, validações, serviços e acesso aos dados.

Sua responsabilidade é centralizar o processamento das informações utilizadas pelo SplitAgent, garantindo que os cálculos financeiros sejam executados de maneira determinística e que a inteligência artificial seja utilizada para interpretar resultados e produzir recomendações.

Entre suas principais responsabilidades estão:

- Cadastro, autenticação e gerenciamento de usuários.
- Importação de informações financeiras por planilhas Excel.
- Cadastro e gerenciamento de lançamentos financeiros manuais.
- Organização de receitas, despesas e saldos.
- Cálculos de fluxo de caixa e projeções financeiras.
- Simulações de decisões financeiras.
- Histórico de decisões do usuário.
- Execução de agentes especializados.
- Simulação de Split Payment.
- Estimativas tributárias e análises de crédito.
- Integração com inteligência artificial por meio da Cloudflare Workers AI.
- Comunicação com o front-end por meio de uma API REST.

## Tecnologias utilizadas

| Tecnologia | Finalidade |
|---|---|
| Python | Linguagem principal |
| FastAPI | Construção da API REST |
| Uvicorn | Servidor da aplicação |
| PostgreSQL | Banco de dados |
| Neon | Hospedagem do banco de dados |
| SQLAlchemy | Mapeamento e acesso aos dados |
| Alembic | Controle de migrações |
| Pydantic | Validação e estruturação de dados |
| openpyxl | Processamento de planilhas Excel |
| Cloudflare Workers AI | Integração generativa |
| Pytest | Testes automatizados |
| Railway | Hospedagem do back-end |

## Arquitetura do projeto

A aplicação utiliza uma organização modular para facilitar a manutenção, evolução e integração de novas funcionalidades.

```text
app/
  main.py                 # Inicialização da aplicação
  core/                   # Configurações, banco e segurança
  api/                    # Rotas e endpoints
  schemas/                # Validação de dados com Pydantic
  models/                 # Modelos e tabelas SQLAlchemy
  services/               # Regras de negócio e processamento
  repositories/            # Acesso e consultas ao banco
  agents/                 # Agentes especializados de IA

alembic/                  # Migrações do banco de dados
tests/                    # Testes automatizados
```

## Principais funcionalidades

### 1. Autenticação e gerenciamento de usuários

O sistema possui uma estrutura de autenticação com:

- Cadastro de usuários.
- Login por e-mail ou CPF/CNPJ.
- Logout e revogação de sessões.
- Recuperação e redefinição de senha.
- Login com Google OAuth.
- Consulta e atualização de perfil.
- Desativação de conta.

As senhas são armazenadas utilizando hash Argon2. Os tokens de sessão e recuperação são armazenados por meio de hashes, evitando a persistência dos tokens originais no banco de dados.

### 2. Importação de planilhas Excel

O sistema permite importar informações financeiras por meio de uma planilha padronizada.

A planilha possui abas destinadas a:

- Instruções de preenchimento.
- Saldo inicial.
- Vendas.
- Recebíveis.
- Despesas.

A importação conta com validações de campos, datas e valores, além de limites de tamanho e quantidade de registros.

A operação utiliza a regra de tudo ou nada: caso sejam encontrados erros, os dados da importação não são salvos parcialmente.

Também é possível substituir uma importação anterior sem afetar os lançamentos financeiros cadastrados manualmente.

### 3. Lançamentos financeiros manuais

Além da importação por Excel, o usuário pode cadastrar informações diretamente na aplicação.

O sistema permite:

- Registrar e atualizar saldo inicial.
- Cadastrar entradas financeiras.
- Cadastrar saídas financeiras.
- Consultar lançamentos.
- Atualizar registros.
- Excluir movimentações.

Os dados manuais são armazenados separadamente dos dados importados e são consolidados nos cálculos financeiros.

### 4. Cálculos financeiros e fluxo de caixa

O back-end executa cálculos para apresentar uma visão organizada da situação financeira do negócio.

Entre os indicadores estão:

- Total de vendas.
- Tributos estimados.
- Valor líquido das vendas.
- Saldo atual.
- Receitas e despesas previstas.
- Menor saldo projetado.
- Situação do fluxo de caixa.

Também existe uma projeção diária para os próximos 30 dias, permitindo acompanhar a evolução esperada do saldo financeiro.

Os cálculos são realizados no back-end, sem depender da inteligência artificial para determinar os valores.

### 5. Simulador financeiro

O simulador permite avaliar situações hipotéticas antes de tomar decisões.

O usuário pode simular:

- Uma nova venda.
- Uma despesa.
- Alterações que podem afetar o saldo disponível.

O sistema compara a projeção financeira original com o cenário simulado, apresentando os possíveis impactos sobre o fluxo de caixa.

As simulações não alteram os lançamentos existentes. Quando o usuário confirma uma decisão, ela pode ser registrada no histórico financeiro.

### 6. Histórico de decisões

O sistema possui um módulo para registrar decisões financeiras confirmadas pelo usuário.

São armazenadas informações como:

- Recomendação apresentada.
- Escolha realizada.
- Resultado financeiro projetado.
- Data e horário do registro.

Cada usuário possui seu próprio histórico, garantindo o isolamento dos registros entre contas.

### 7. Agentes inteligentes

O SplitAgent possui agentes especializados que trabalham em conjunto para analisar diferentes aspectos da gestão financeira.

Entre eles estão:

| Agente | Responsabilidade |
|---|---|
| Orquestrador | Coordena as análises |
| Cash | Analisa o fluxo de caixa |
| Forecast | Trabalha com projeções financeiras |
| Tax | Realiza estimativas tributárias |
| Credit | Analisa informações relacionadas ao crédito |
| Guardian | Auxilia na identificação de riscos |
| Split Payment | Simula a divisão de pagamentos |
| Inclusion | Trabalha com aspectos de inclusão financeira |

Os agentes utilizam dados consolidados e regras de negócio para produzir análises. A integração generativa permite complementar os resultados com interpretações e recomendações em linguagem natural.

### 8. Splito — Assistente financeiro com IA

O **Splito** é o assistente virtual do SplitAgent.

Integrado ao back-end, ele permite que o usuário converse sobre sua situação financeira e obtenha orientações com base nas informações disponíveis em sua conta.

Entre suas funcionalidades estão:

- Interpretação de informações financeiras.
- Consulta ao contexto financeiro do usuário.
- Apoio na compreensão do fluxo de caixa.
- Orientações sobre receitas e despesas.
- Utilização de ferramentas para consultar informações e executar análises disponíveis no sistema.
- Continuidade do contexto das conversas.

A integração utiliza a **Cloudflare Workers AI**, com o modelo configurado no ambiente da aplicação.

A arquitetura mantém os cálculos financeiros separados da geração de respostas: os valores são processados pelas regras de negócio do sistema, enquanto a IA auxilia na interpretação dos resultados.

### 9. Split Payment

O back-end também possui funcionalidades relacionadas ao Split Payment, permitindo simular a divisão de pagamentos entre participantes.

O módulo valida os dados informados, realiza os cálculos de distribuição e verifica as condições de inclusão financeira.

O objetivo é auxiliar na compreensão dos impactos desse modelo de pagamento sobre a organização financeira dos pequenos negócios.

### 10. Análises tributárias e de crédito

A API possui módulos específicos para:

- Estimativa matemática de tributos com base em alíquotas informadas.
- Análise de informações relacionadas à disponibilidade de crédito.
- Integração dessas informações às análises financeiras do sistema.

As estimativas tributárias são simplificadas e não substituem uma apuração fiscal profissional. A análise de crédito também não representa aprovação bancária.

## Principais endpoints

Todas as rotas abaixo pertencem à API e, quando indicado, exigem autenticação Bearer.

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/health` | Verifica a disponibilidade da API |
| GET | `/health/db` | Verifica a conexão com o banco |
| POST | `/api/v1/acesso/cadastro` | Cadastra usuário |
| POST | `/api/v1/acesso/login` | Realiza login |
| POST | `/api/v1/acesso/logout` | Encerra sessão |
| GET | `/api/v1/acesso/me` | Consulta perfil |
| POST | `/api/v1/importacoes` | Importa planilha Excel |
| GET | `/api/v1/importacoes/modelo` | Baixa planilha modelo |
| GET | `/api/v1/movimentacoes` | Consulta movimentações |
| GET | `/api/v1/saldo-inicial` | Consulta saldos |
| POST | `/api/v1/movimentacoes/manuais` | Cadastra movimentação manual |
| GET | `/api/v1/calculos-financeiros/visao-geral` | Consulta visão financeira |
| GET | `/api/v1/calculos-financeiros/fluxo-caixa` | Consulta projeção de caixa |
| POST | `/api/v1/simulador/simular` | Executa simulação financeira |
| GET | `/api/v1/simulador/decisoes` | Consulta histórico de decisões |
| GET | `/api/v1/agentes/financeiro/analisar` | Executa análise financeira |
| POST | `/api/v1/agentes/split-payment/simular` | Simula Split Payment |
| POST | `/api/v1/agentes/credito/analisar` | Executa análise de crédito |
| POST | `/api/v1/agentes/tributos/estimar` | Estima tributos |
| POST | `/api/v1/assistente/conversar` | Interage com o Splito |

A documentação Swagger apresenta os parâmetros, modelos de requisição e respostas de cada endpoint:

https://ibm-splitagent-back-end-production.up.railway.app/docs

## Executar localmente

### Requisitos

- Python 3.12 ou superior, conforme as dependências do projeto.
- PostgreSQL.
- Git.

### Instalação

Clone o repositório:

```bash
git clone https://github.com/Tiasgod/IBM-SplitAgent---Back-End.git
cd IBM-SplitAgent---Back-End
```

Crie e ative o ambiente virtual:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Configure as variáveis de ambiente:

```powershell
copy .env.example .env
```

Edite o arquivo `.env` com as credenciais e configurações necessárias.

Aplique as migrações:

```bash
alembic upgrade head
```

Inicie a aplicação:

```bash
uvicorn app.main:app --reload
```

A API ficará disponível em:

```text
http://127.0.0.1:8000
```

Documentação local:

```text
http://127.0.0.1:8000/docs
```

## Banco de dados e migrações

O projeto utiliza PostgreSQL hospedado no Neon.

O SQLAlchemy é responsável pelo mapeamento dos dados, enquanto o Alembic controla a evolução da estrutura do banco.

Comandos principais:

```bash
alembic upgrade head
alembic current
alembic downgrade -1
```

Para a conexão da aplicação, utilize `DATABASE_URL`. Para as migrações, configure `DATABASE_URL_DIRECT` com a conexão direta do Neon.

## Variáveis de ambiente

As configurações da aplicação são realizadas por variáveis de ambiente.

Entre as principais estão:

- `DATABASE_URL`: conexão com o banco PostgreSQL.
- `DATABASE_URL_DIRECT`: conexão direta utilizada nas migrações.
- `ENVIRONMENT`: ambiente de execução.
- `CORS_ORIGINS`: origens autorizadas para comunicação com o front-end.
- `CLOUDFLARE_ACCOUNT_ID`: identificação da conta Cloudflare.
- `CLOUDFLARE_API_TOKEN`: token de acesso à API.
- `CLOUDFLARE_MODEL`: modelo de IA utilizado, conforme configuração do projeto.
- `GOOGLE_CLIENT_ID`: identificação da aplicação para autenticação Google.
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER` e `SMTP_PASSWORD`: configurações de envio de e-mail.

Os nomes exatos das variáveis devem seguir o arquivo `.env.example` e as configurações definidas em `app/core/config.py`.

**Importante:** nunca publique arquivos `.env`, senhas, tokens ou credenciais no GitHub.

## Deploy

O back-end está hospedado no Railway, com banco de dados PostgreSQL no Neon.

A aplicação utiliza o domínio:

https://ibm-splitagent-back-end-production.up.railway.app

A rota `/health` permite verificar a disponibilidade da API.

## Testes automatizados

O projeto utiliza Pytest para verificar o comportamento das funcionalidades e regras de negócio.

Para executar os testes:

```bash
pytest
```

Os testes utilizam banco SQLite temporário e configurações próprias, evitando a necessidade de utilizar os dados reais do ambiente de produção.

## Segurança e proteção de dados

O projeto adota medidas para proteger as informações dos usuários:

- Senhas armazenadas com hash Argon2.
- Tokens de sessão e recuperação armazenados por meio de hashes.
- Autenticação por Bearer Token.
- Isolamento dos dados financeiros por usuário.
- Validação das informações recebidas pela API.
- Uso de HTTPS nos ambientes publicados.
- Separação de credenciais e configurações por variáveis de ambiente.
- Envio de indicadores financeiros agregados à IA, evitando o compartilhamento desnecessário de informações pessoais.

## Sobre o desenvolvimento

Este back-end foi desenvolvido por **Tiago Pereira Dias**, como parte do projeto SplitAgent, da equipe ThreeValley.

O trabalho envolveu a construção da API, modelagem e integração com banco de dados, implementação de regras de negócio, autenticação, cálculos financeiros, simulações, agentes especializados e integração com serviços de inteligência artificial.

O objetivo foi construir uma estrutura capaz de sustentar uma aplicação financeira completa, conectando dados, processamento determinístico e inteligência artificial em uma única solução.

---

**SplitAgent — Inteligência financeira para pequenos negócios.**

Desenvolvido pela equipe ThreeValley | Parceria IBM + Banco do Brasil.
