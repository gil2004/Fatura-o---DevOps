# Projeto Final DevOps — Faturação em Microsserviços Python

**Autor:** Gil Alves · **Curso:** DevOps Engineering — Tokio School
**Repositório:** https://github.com/gil2004/Fatura-o---DevOps

---

## 1. Introdução — Arquitetura do pipeline de entrega contínua

Este projeto implementa um pipeline de entrega contínua para uma aplicação web Python
baseada em microsserviços. A aplicação simula um sistema de faturação composto por
dois serviços que comunicam entre si por HTTP, com respostas em formato JSON:

- **clientes-service** (porta 5001) — gestão de clientes e validação do NIF português.
- **faturas-service** (porta 5002) — emissão de faturas; consulta o clientes-service
  e calcula a base, o IVA e o total.

O ciclo de entrega funciona assim:

1. O código é desenvolvido localmente, num ambiente virtual Python (venv), e testado com pytest.
2. As alterações são enviadas para o GitHub (`git push`).
3. O GitHub Actions executa o pipeline, com um ambiente personalizado por fase:

| Branch | Jobs executados | Testes |
|---|---|---|
| `develop` | DEV | lint (ruff) + testes unitários |
| `main` | DEV → STG → PRD | + testes de integração (STG) + smoke tests (PRD) |

4. O deploy em **PRD** exige aprovação manual, configurada no GitHub Environment `prd`.
5. Os containers são orquestrados com Docker Compose e as transações entre os
   serviços são rastreadas com Jaeger (OpenTelemetry).

## 2. Desenho da arquitetura

![Arquitetura HLD](docs/20260923-HLD-ProjetoFinal-DevOps.drawio.png)

O diagrama tem três blocos:

- **Máquina local** — VS Code, venv, pytest e Docker Compose.
- **GitHub** — o repositório e o pipeline DEV → STG → PRD.
- **Stack Docker Compose** — faturas-service → clientes-service, com envio de traces para o Jaeger.

## 3. Estrutura do repositório

```
├── .github/workflows/pipeline.yml   # pipeline CI/CD
├── clientes-service/
│   ├── app.py
│   └── tests/test_app.py            # testes unitários (DEV)
├── faturas-service/
│   ├── app.py
│   └── tests/test_app.py            # testes unitários (DEV)
├── tests/
│   ├── integracao/test_integracao.py  # testes de integração (STG)
│   └── smoke/test_smoke.py            # smoke tests (PRD)
├── docs/                            # diagrama da arquitetura
├── fotos/                           # evidências
├── requirements.txt
├── .gitignore
└── README.md
```

## 4. Ferramentas e bibliotecas utilizadas

| Ferramenta / biblioteca | Utilização |
|---|---|
| Python 3.12 + venv | linguagem e ambiente virtual isolado |
| Flask | framework das APIs REST |
| requests | chamadas HTTP entre serviços e nos testes de integração |
| gunicorn | servidor WSGI de produção |
| pytest | framework de testes |
| pytest-cov | medição da cobertura de código |
| requests-mock | simulação do clientes-service nos testes unitários |
| ruff | análise estática do código (lint) |
| Git + GitHub | controlo de versões e repositório remoto |
| GitHub Actions + Environments | pipeline CI/CD com os ambientes DEV, STG e PRD |
| Docker + Docker Compose | containers e orquestração |
| Jaeger + OpenTelemetry | rastreamento de transações entre microsserviços |
| draw.io | desenho da arquitetura |

## 5. Decisões de design

- **Domínio de faturação:** tem regras de negócio úteis de testar (validação do NIF,
  taxas de IVA portuguesas de 0, 6, 13 e 23%) sem complicar a arquitetura.
- **Dados em memória:** o foco do projeto é o pipeline de entrega.
- **Docker Compose em vez de Kubernetes:** cumpre o requisito de orquestração com
  menos complexidade.
- **Um único `requirements.txt`** na raiz, partilhado pelos dois serviços.
- **Branches em vez de tags:** a `develop` é a área de trabalho e a `main` a linha de
  entrega. A proteção de produção é feita pela aprovação manual do ambiente `prd`.
- **Testes separados por fase:** unitários em DEV, integração em STG, smoke em PRD.
- **Mocks nos testes unitários:** o faturas-service é testado sem depender do
  clientes-service; a comunicação real é validada nos testes de integração.
- **Ambientes simulados nos runners do GitHub:** cada job corre numa máquina virtual
  nova, que é destruída no fim. Por isso, cada job arranca os serviços antes de os
  testar. Numa empresa, cada ambiente seria um servidor permanente e o job faria o
  deploy da nova versão para esse servidor.
- **Padrão application factory (`create_app()`):** cada teste recebe uma instância
  nova da aplicação, sem dados de testes anteriores.
- **Tratamento de falhas entre serviços:** se o clientes-service estiver indisponível,
  o faturas-service devolve 503 em vez de falhar.

## 6. Implementação — passos

### Passo 1 — Estrutura do projeto e ambiente virtual

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

![pip install](fotos/01-pip-install.png)

### Passo 2 — Testes unitários do clientes-service

```bash
cd clientes-service
python3 -m pytest -v --cov=app
```

Resultado: **15 testes aprovados, 95% de cobertura.**

![Testes clientes-service](fotos/03-testes-clientes.png)

### Passo 3 — Testes unitários do faturas-service

```bash
cd faturas-service
python3 -m pytest -v --cov=app
```

Resultado: **9 testes aprovados, 91% de cobertura.**

![Testes faturas-service](fotos/04-testes-faturas.png)

### Passo 4 — Comunicação entre os microsserviços

Os dois serviços foram arrancados em terminais separados (`python3 app.py`) e foi
enviado um pedido de fatura:

```bash
curl -X POST localhost:5002/api/faturas -H "Content-Type: application/json" \
  -d '{"nif":"501964843","linhas":[{"descricao":"Consultoria","quantidade":2,"preco_unitario":100,"taxa_iva":23}]}'
```

O faturas-service consultou o clientes-service (`GET /api/clientes/501964843` → 200)
e devolveu a fatura em JSON, com o total de 246.0 €.

![Comunicação entre serviços](fotos/05-servicos-juntos.png)

### Passo 5 — Repositório local e remoto (GitHub)

```bash
git init
git add .
git commit -m "Microsserviços clientes e faturas com testes unitários"
git branch -M main
git remote add origin https://github.com/gil2004/Fatura-o---DevOps.git
git push -u origin main
git checkout -b develop
git push -u origin develop
```

### Passo 6 — Pipeline GitHub Actions com ambientes DEV, STG e PRD

**6.1 — Ambientes personalizados.** Em *Settings → Environments* foram criados os
ambientes `dev`, `stg` e `prd`. O `prd` tem a regra *Required reviewers*, que obriga a
uma aprovação manual antes do deploy em produção.

**6.2 — Ambiente DEV.** O ficheiro `.github/workflows/pipeline.yml` define o job DEV,
que corre em cada push para a `develop` ou para a `main`: instala as dependências,
executa o lint com ruff e os testes unitários dos dois serviços.

![Pipeline DEV](fotos/07-pipeline-dev.png)

**6.3 — Ambiente STG.** Foram criados os testes de integração em `tests/integracao/`,
que fazem pedidos HTTP reais aos dois serviços. Foram primeiro validados localmente:

```bash
python3 -m pytest -v tests/integracao
```

Resultado: **3 testes aprovados.**

![Testes de integração local](fotos/06-testes-integracao-local.png)

No pipeline, o job STG só corre na `main` e depois de o DEV passar (`needs: dev`).
Arranca os serviços com gunicorn e executa os testes de integração.

![Pipeline STG](fotos/09-pipeline-stg.png)

**6.4 — Ambiente PRD.** Foram criados os smoke tests em `tests/smoke/`, que verificam
rapidamente se os serviços estão ativos e se a funcionalidade principal responde:

```bash
python3 -m pytest -v tests/smoke
```

Resultado: **3 testes aprovados.**

![Smoke tests local](fotos/10-smoke-local.png)

O job PRD corre depois do STG e fica à espera de aprovação manual. Depois de
aprovado, arranca os serviços e executa os smoke tests.

![Aprovação PRD](fotos/11-aprovacao-prd.png)

![Pipeline completo](fotos/12-pipeline-completo.png)

**Fluxo de trabalho:**

```bash
# trabalho diário → DEV
git checkout develop
git add -A
git commit -m "descrição"
git push

# entrega → DEV → STG → PRD
git checkout main
git merge develop
git push
git checkout develop
```

### Passo 7 — Containers com Docker Compose *(a completar)*

### Passo 8 — Rastreamento com Jaeger *(a completar)*

### Passo 9 — Paragem, destruição e limpeza da infraestrutura *(a completar)*

## 7. Evidências dos testes

| Teste | Ambiente | Resultado |
|---|---|---|
| Unitários clientes-service | local + DEV | 15 aprovados · 95% cobertura |
| Unitários faturas-service | local + DEV | 9 aprovados · 91% cobertura |
| Comunicação entre serviços (curl) | local | fatura criada com sucesso (201) |
| Integração | local + STG | 3 aprovados |
| Smoke tests | local + PRD | 3 aprovados |

## 8. Problemas encontrados

| Problema | Causa | Solução |
|---|---|---|
| `ModuleNotFoundError: No module named 'app'` ao correr `pytest` | o comando `pytest` não adiciona a pasta atual ao caminho de importação | usar `python3 -m pytest` |
| `ModuleNotFoundError: No module named 'flask'` num terminal novo | o venv não estava ativo nesse terminal | `source venv/bin/activate` em cada terminal |
| `flask` sublinhado no VS Code | o VS Code não usava o interpretador do venv | *Python: Select Interpreter* → `./venv/bin/python` |
| Acentos no JSON apareciam como `\u00e3` | o Flask escapa caracteres não-ASCII por defeito | `app.json.ensure_ascii = False` |
| Repositório Git criado dentro de `clientes-service` | `git init` executado na pasta errada | apagar `clientes-service/.git` e repetir na raiz |
| `error: pathspec 'develop' did not match` | a branch `develop` não existia depois de recriar o repositório | `git checkout -b develop` |
| Ruff com resultados diferentes no PC e no CI | estava a ser usado um ruff instalado no sistema, com outra configuração | usar o ruff do venv e corrigir com `ruff check . --fix` |
| Nome do repositório ficou `Fatura-o---DevOps` | o GitHub não aceita caracteres como "ç" e "ã" nos nomes | evitar acentos em nomes de repositórios, pastas e ficheiros |
| STG falhou: `file or directory not found: tests/integracao` | a pasta foi renomeada (sem acentos) mas a alteração não entrou no commit | `git add -A` para incluir ficheiros renomeados e apagados |
| Aviso de Node.js 20 obsoleto no GitHub Actions | versões antigas das actions | atualizar para `actions/checkout@v5` e `actions/setup-python@v6` |

![Erro pytest](fotos/02-erro-pytest-modulo.png)

![Erro STG](fotos/08-erro-stg-pasta.png)

## 9. Utilização de ferramentas de IA

Durante o projeto foi utilizado o Claude (Anthropic) como ferramenta de apoio na
proposta de arquitetura, no código base dos serviços e na estrutura deste relatório.
A escolha do domínio, a simplificação da arquitetura (Docker Compose em vez de
Kubernetes, branches em vez de tags), a implementação, a execução dos testes, a
resolução dos problemas encontrados e a validação de todo o trabalho foram feitas
pelo autor.