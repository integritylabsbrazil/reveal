# Reveal — Technical Refinement Tool

Conecta-se a qualquer Jira, escaneia qualquer base de código e gera documentos
completos de refinamento técnico para o time de desenvolvimento.

Gera subtarefas atômicas com nível de senioridade (junior/pleno/senior) para
distribuição em sprint, baixa attachments do Jira com dedup por MD5, e suporta
projetos Java, JavaScript/TypeScript e Genéricos via configuração.

## Estrutura

```
reveal/
├── refine-ticket.sh              ← Orquestrador principal
├── gerar-documentacao.sh         ← Pipeline completo em 1 comando (--dry-run)
├── setup.sh                      ← Setup interativo do projeto
├── refine-config.json            ← Configuração padrão (Jira, projetos)
├── refine-config.local.json      ← Configuração local (gitignored)
├── generate-context.sh           ← Gera contexto-implementacao.md
├── generate-index.sh             ← Regenera INDEX.md
├── validate-ticket.sh            ← Valida consistência entre docs + schema JSON
├── completions.sh                ← Auto-complete bash para IDs de ticket
│
├── lib/
│   ├── utils.sh                  ← Funções compartilhadas de logging
│   ├── jira-fetch.sh             ← Deep fetch Jira + download attachments (MD5)
│   ├── code-scan.sh              ← Scan de código multi-linguagem
│   ├── generate-questions.sh     ← Perguntas para o negócio
│   ├── generate-refinement.sh    ← Documento de refinamento (template-driven)
│   ├── generate-tasks.sh         ← Wrapper shell para generate_tasks.py
│   ├── utils.py                  ← Funções Python compartilhadas (load_json, validação)
│   ├── render_template.py        ← Renderizador Mustache-like {{VAR}}
│   ├── assemble_jira.py          ← Monta dados do Jira para processamento
│   ├── generate_implementation_plan.py ← Plano de implementação técnica
│   ├── generate_tasks.py         ← Gera status-tasks.json (config-driven)
│   ├── generate_per_task_jira_text.py ← Texto Jira por subtarefa
│   ├── jira_agile_parse.py       ← Parse de dados ágeis (sprints, pontos)
│   ├── jira_attachment_dedup.py  ← Download de attachments com dedup MD5
│   └── jira_count_attachments.py ← Contagem de attachments baixados
│
├── templates/
│   └── refinamento-tecnico-template.md
│
├── hooks/
│   └── commit-msg                ← Hook para validar mensagens de commit
│
├── tests/
│   ├── test_generate_tasks.py    ← 22 testes unitários
│   ├── test_utils.py             ← 20 testes unitários
│   └── test_extracted.py         ← 5 testes unitários
│
├── tickets/                      ← Documentação de tickets (um por pasta)
│   ├── _template/                ← Modelo para novos tickets
│   └── INDEX.md                  ← Índice gerado por generate-index.sh
│
├── AGENTS.md                     ← Instruções detalhadas para agentes de IA
└── README.md                     ← Este arquivo
```

## Pré-requisitos

- Bash 4+
- python3 (stdlib apenas — sem pip necessário)
- jq
- curl
- git

## Configuração Rápida

```bash
# 1. Copiar configuração
cp refine-config.json refine-config.local.json

# 2. Ajustar projetos e Jira
# edite refine-config.local.json:
#   - jira.baseUrl → sua instância
#   - projects[].path → seus projetos

# 3. Credenciais Jira (env vars ou arquivo)
export JIRA_USER="email@empresa.com"
export JIRA_TOKEN="seu-token"
export JIRA_BASE="https://meujira.atlassian.net"
# ou crie ~/.jira-credentials (formato: usuario:token)
```

## Documentos Gerados por Ticket

| Arquivo | Finalidade | Gerado por |
|---------|-----------|------------|
| `jira-data.json` | Dados brutos da API Jira + attachments baixados | pipeline |
| `jira-summary.md` | Resumo legível do ticket | pipeline |
| `impact-report.json` | Estrutura dos projetos escaneados | pipeline |
| `perguntas-negocio.md` | Perguntas para o PO/analista | pipeline |
| `refinamento-tecnico.md` | Documento completo de refinamento | pipeline |
| `implementation-plan.md` | Plano técnico, riscos, cronograma | pipeline (`--plan`) |
| `status-tasks.json` | Subtarefas com nível de senioridade + status | pipeline |
| `contexto-implementacao.md` | Resumo visual com tabela de progresso | pipeline |
| `attachments/` | Imagens baixadas do Jira (dedup por MD5) | pipeline |
| `description.md` | Descrição enriquecida com análise de negócio | agente IA |
| `roteiro-demo.md` | Script de apresentação ao negócio | agente IA |
| `demo-artifacts/postman-collection.json` | Collection Postman por cenário | agente IA |
| `demo-artifacts/postman-environment.json` | Variáveis de ambiente da demo | agente IA |
| `demo-artifacts/queries.sql` | Consultas SQL para demonstrar dados | agente IA |

## Fluxo de Trabalho

### 0. Configuração Inicial (uma vez por projeto)

```bash
# 1. Copiar e ajustar configuração
cp refine-config.json refine-config.local.json
# edite refine-config.local.json:
#   - jira.baseUrl → sua instância Jira
#   - projects[].path → caminho dos seus projetos

# 2. Credenciais Jira
export JIRA_USER="email@empresa.com"
export JIRA_TOKEN="seu-token"
export JIRA_BASE="https://meujira.atlassian.net"
# ou crie ~/.jira-credentials (formato: usuario:token)
```

### 1. Gerar Documentação do Ticket

```bash
./gerar-documentacao.sh PROJ-123
```

**O que é criado em `tickets/PROJ-123/`:**

| Arquivo | Finalidade | Gerado por |
|---------|-----------|------------|
| `jira-data.json` | Dados brutos + attachments (imagens) | pipeline |
| `jira-summary.md` | Resumo do ticket | pipeline |
| `impact-report.json` | Estrutura dos projetos escaneados | pipeline |
| `perguntas-negocio.md` | Perguntas para o PO | pipeline |
| `refinamento-tecnico.md` | Refinamento técnico completo | pipeline |
| `implementation-plan.md` | Plano de implementação | pipeline (`--plan`) |
| `status-tasks.json` | **3 subtarefas** verticais com nível de senioridade | pipeline |
| `contexto-implementacao.md` | Resumo visual com progresso | pipeline |
| `attachments/` | Imagens baixadas do Jira | pipeline |
| `description.md` | Descrição enriquecida | agente IA |
| `roteiro-demo.md` | Script de apresentação | agente IA |
| `demo-artifacts/` | Postman collection + queries SQL | agente IA |

> Use `--dry-run` para ver o que seria feito sem criar nada.

### 2. Revisar Perguntas com o PO

1. Abra `tickets/PROJ-123/perguntas-negocio.md`
2. Envie para o PO/analista responder
3. Após respostas, atualize `refinamento-tecnico.md` manualmente

### 3. Validar Consistência (obrigatório após cada alteração)

```bash
./generate-context.sh PROJ-123   # Sincroniza tabela visual
./validate-ticket.sh PROJ-123    # Valida tasks em todos os docs
./generate-index.sh              # Atualiza índice geral
```

Ver [AGENTS.md](AGENTS.md#101-verificação-obrigatória-de-consistência--pós-toda-ação)
para os 5 checks automáticos (contagem de tasks, docs vazios,
dependências inválidas).

### 4. Implementar Tasks (agente IA ou dev)

Cada task da branch `feature/PROJ-X`:

```
 Task 0001 → commits → squash → "PROJ-X-0001: descricao"
 Task 0002 → commits → squash → "PROJ-X-0002: descricao"
 ...
 Final    → squash de tudo → "PROJ-X: Resumo do ticket"
```

Registre cada conclusão no `status-tasks.json` com `commitHash`
e `rollbackCommand`. Veja [AGENTS.md](AGENTS.md#6-ciclo-de-vida-de-uma-task)
para o ciclo completo (pre-commit hook, auto-detecção de arquivos,
squash, rollback).

### 5. Demo ao Negócio

Use `roteiro-demo.md` + Postman collection + queries SQL.

---

## Subtarefas Inteligentes

O `generate_tasks.py` lê a configuração do projeto e gera tarefas por:

| Característica | Descrição |
|----------------|-----------|
| **Linguagem** | Java (entidades, repositories, services) |
| | JavaScript/TypeScript (components, hooks, services) |
| | Genérico (adaptável a qualquer stack) |
| **Senioridade** | junior, pleno, senior |
| **Dependências** | Ordem de implementação entre tasks |
| **Múltiplos projetos** | Tasks distribuídas entre backend + frontend |

## Comandos Úteis

```bash
# Pipeline completo (atalho)
./gerar-documentacao.sh PROJ-123 --dry-run   # Modo seco (não escreve nada)

# Etapas individuais
./refine-ticket.sh PROJ-123 --jira-deep       # Apenas fetch Jira
./refine-ticket.sh PROJ-123 --scan-impact     # Apenas scan de código
./refine-ticket.sh PROJ-123 --questions       # Apenas perguntas
./refine-ticket.sh PROJ-123 --refinement      # Apenas refinamento
./refine-ticket.sh PROJ-123 --plan            # Apenas plano de implementação

# Status e validação
./validate-ticket.sh PROJ-123                 # Valida consistência
./generate-context.sh PROJ-123                # Sincroniza tabela
./generate-index.sh                           # Atualiza índice

# Tickets com tarefas pendentes
find ./tickets -name "status-tasks.json" \
  -exec sh -c 'jq -r ".ticketId + \": \" + ([.tarefas[] | select(.status==\"pendente\")] | length | tostring) + \" pendentes\"" "$1"' _ {} \;

# Auto-complete (adicione ao .bashrc)
source completions.sh
```

## Configuração (`refine-config.local.json`)

```json
{
  "jira": {
    "baseUrl": "https://meujira.atlassian.net",
    "projectPrefixes": ["PROJ"]
  },
  "projects": [
    {
      "name": "meu-backend",
      "path": "../projetos/meu-backend",
      "language": "java",
      "buildTool": "gradle"
    }
  ]
}
```

Suporta múltiplos projetos (ex: backend + frontend) no array `projects[]`.

## Schema Validation

O `validate-ticket.sh` valida a estrutura dos JSONs gerados (`status-tasks.json`,
`impact-report.json`, `jira-data.json`) contra schemas embutidos:

- Presença de campos obrigatórios
- Tipos corretos (string, array, objeto)
- Dependências entre tasks válidas (não referenciam IDs inexistentes)

A validação roda **automaticamente** ao final do pipeline `--refine`.
Para rodar manualmente:

```bash
./validate-ticket.sh PROJ-123
```

## Proxy HTTP

Se o ambiente exigir proxy para acessar o Jira, configure via variáveis de
ambiente padrão:

```bash
export HTTPS_PROXY="http://proxy.empresa.com:8080"
export HTTP_PROXY="http://proxy.empresa.com:8080"
```

O `jira-fetch.sh` respeita estas variáveis automaticamente nas chamadas curl.

## Variáveis de Ambiente

| Variável | Obrigatória | Descrição |
|----------|-------------|-----------|
| `JIRA_USER` | Para fetch | Email do usuário Jira |
| `JIRA_TOKEN` | Para fetch | Token de API do Jira |
| `JIRA_BASE` | Para fetch | URL base do Jira |

Fallback: `~/.jira-credentials` (formato: `usuario:token`)

## Testes

```bash
python3 -m unittest discover tests
```

52 testes em 3 suites, stdlib apenas (sem dependências externas).

| Suite | Testes | O que cobre |
|-------|--------|-------------|
| `test_generate_tasks.py` | 22 | Geração de subtarefas por projeto |
| `test_utils.py` | 20 | Funções compartilhadas de validação |
| `test_extracted.py` | 5 | Scripts extraídos do bash para Python |

## Troubleshooting

| Problema | Causa provável | Solução |
|----------|---------------|---------|
| `curl: (28) Connection timed out` | Sem acesso à rede do Jira | Configure `HTTPS_PROXY` ou verifique VPN |
| `JIRA_USER/JIRA_TOKEN não definidos` | Credenciais ausentes | Exporte as vars ou crie `~/.jira-credentials` |
| `jq: command not found` | Falta jq | Instale: `apt install jq` ou `brew install jq` |
| `0 tarefas` no contexto | `generate_tasks.py` falhou | Verifique se `refine-config.local.json` existe e tem `projects[]` |
| `ERRO: status-tasks.json tem X tasks, contexto-implementacao.md mostra Y` | Documentos dessincronizados | Execute `./generate-context.sh TICKET_ID` e `./validate-ticket.sh TICKET_ID` |
| `ERRO: description.md está vazio` | Documento não gerado pelo agente | O `description.md` é criado pelo agente IA, não pelo pipeline |
| `refine-config.json` não encontrado | Configuração não copiada | `cp refine-config.json refine-config.local.json` e ajuste |
| `ERRO: task X depende de Y que nao existe` | Dependência inválida no JSON | Edite `dependeDe` no `status-tasks.json` manualmente |

## Licença

MIT
