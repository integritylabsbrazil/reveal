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
├── refine-config.json            ← Configuração padrão (Jira, projetos)
├── refine-config.local.json      ← Configuração local (gitignored)
├── generate-context.sh           ← Gera contexto-implementacao.md
├── generate-index.sh             ← Regenera INDEX.md
├── validate-ticket.sh            ← Valida consistência entre docs
├── completions.sh                ← Auto-complete bash para IDs de ticket
│
├── lib/
│   ├── jira-fetch.sh             ← Deep fetch Jira + download attachments (MD5)
│   ├── code-scan.sh              ← Scan de código multi-linguagem
│   ├── generate-questions.sh     ← Perguntas para o negócio
│   ├── generate-refinement.sh    ← Documento de refinamento (template-driven)
│   ├── generate-tasks.sh         ← Wrapper shell para generate_tasks.py
│   ├── generate_tasks.py         ← Gera status-tasks.json (config-driven)
│   └── render_template.py        ← Renderizador Mustache-like {{VAR}}
│
├── templates/
│   ├── perguntas-negocio-template.md
│   └── refinamento-tecnico-template.md
│
├── hooks/
│   └── commit-msg                ← Hook para validar mensagens de commit
│
├── tests/
│   └── test_generate_tasks.py    ← 22 testes unitários (stdlib unittest)
│
├── tickets/                      ← Documentação de tickets (um por pasta)
│   ├── _template/                ← Modelo para novos tickets
│   └── INDEX.md                  ← Índice gerado por generate-index.sh
│
├── create-ticket-doc.sh          ← [DEPRECATED] Substituído por gerar-documentacao.sh
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

| Arquivo | Finalidade |
|---------|-----------|
| `jira-data.json` | Dados brutos da API Jira + attachments baixados |
| `jira-summary.md` | Resumo legível do ticket |
| `description.md` | Descrição extraída do Jira |
| `impact-report.json` | Estrutura dos projetos escaneados |
| `perguntas-negocio.md` | Perguntas para o PO/analista |
| `refinamento-tecnico.md` | Documento completo de refinamento |
| `implementation-plan.md` | Plano técnico, riscos, cronograma |
| `roteiro-demo.md` | Script de apresentação ao negócio |
| `demo-artifacts/postman-collection.json` | Collection Postman por cenário |
| `demo-artifacts/postman-environment.json` | Variáveis de ambiente da demo |
| `demo-artifacts/queries.sql` | Consultas SQL para demonstrar dados |
| `status-tasks.json` | Subtarefas com nível de senioridade + status |
| `contexto-implementacao.md` | Resumo visual com tabela de progresso |
| `attachments/` | Imagens baixadas do Jira (dedup por MD5) |

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

| Arquivo | Finalidade |
|---------|-----------|
| `jira-data.json` | Dados brutos + attachments (imagens) |
| `jira-summary.md` | Resumo do ticket |
| `description.md` | Descrição extraída |
| `impact-report.json` | Estrutura dos projetos escaneados |
| `perguntas-negocio.md` | Perguntas para o PO |
| `refinamento-tecnico.md` | Refinamento técnico completo |
| `implementation-plan.md` | Plano de implementação |
| `roteiro-demo.md` | Script de apresentação |
| `demo-artifacts/` | Postman collection + queries SQL |
| `status-tasks.json` | **7 subtarefas** com nível de senioridade |
| `contexto-implementacao.md` | Resumo visual com progresso |
| `attachments/` | Imagens baixadas do Jira |

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

## Variáveis de Ambiente

| Variável | Obrigatória | Descrição |
|----------|-------------|-----------|
| `JIRA_USER` | Para fetch | Email do usuário Jira |
| `JIRA_TOKEN` | Para fetch | Token de API do Jira |
| `JIRA_BASE` | Para fetch | URL base do Jira |

Fallback: `~/.jira-credentials` (formato: `usuario:token`)

## Testes

```bash
python3 -m unittest tests.test_generate_tasks
```

22 testes, stdlib apenas (sem dependências externas).

## Licença

MIT
