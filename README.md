# Reveal — Technical Refinement Tool

Conecta-se a qualquer Jira, escaneia qualquer base de código e gera documentos
completos de refinamento técnico para o time de desenvolvimento.

## Estrutura

```
reveal/
├── tickets/                       ← Documentação de tickets (um por pasta)
│   ├── _template/                  ← Modelo para novos tickets
│   └── INDEX.md
├── lib/
│   ├── jira-fetch.sh               ← Deep fetch Jira (épico, links, subtasks, comentários)
│   ├── code-scan.sh                ← Scan de código multi-linguagem
│   ├── generate-questions.sh       ← Perguntas para o negócio
│   └── generate-refinement.sh      ← Documento de refinamento técnico
├── templates/                      ← Templates markdown
├── hooks/
│   └── commit-msg                  ← Hook para validar mensagens de commit
├── refine-ticket.sh                ← Orquestrador principal
├── create-ticket-doc.sh            ← Script de fetch Jira (legado)
├── refine-config.json              ← Configuração (Jira, projetos)
├── AGENTS.md                       ← Instruções para agentes de IA
└── README.md                       ← Este arquivo
```

## Documentos Gerados por Ticket

| Arquivo | Finalidade |
|---------|-----------|
| `jira-data.json` | Dados brutos da API Jira (enriquecido) |
| `jira-summary.md` | Resumo legível do Jira |
| `description.md` | Descrição + critérios de aceitação |
| `implementation-plan.md` | Plano técnico, riscos, cronograma |
| `roteiro-demo.md` | Script de apresentação ao negócio |
| `demo-artifacts/postman-collection.json` | Collection Postman por cenário |
| `demo-artifacts/postman-environment.json` | Variáveis de ambiente da demo |
| `demo-artifacts/queries.sql` | Consultas SQL para demonstrar dados |
| `contexto-implementacao.md` | Resumo visual + progresso |
| `status-tasks.json` | Estado real de cada subtarefa |
| `perguntas-negocio.md` | Perguntas para o PO/analista |
| `refinamento-tecnico.md` | Documento completo de refinamento |

## Fluxo de Trabalho

### 1. Buscar dados do Jira

```bash
export JIRA_USER="seu.email@empresa.com"
export JIRA_TOKEN="seu-token"
export JIRA_BASE="https://seujira.atlassian.net"

./refine-ticket.sh PROJ-123 --refine
```

### 2. Revisar perguntas para o negócio

Enviar `perguntas-negocio.md` para o PO/analista responder.

### 3. Após respostas, refinar

Atualizar `refinamento-tecnico.md` com as respostas e gerar subtarefas.

### 4. Implementar tasks

Cada task na mesma branch (`feature/PROJ-X`):
- Commits intermediários → squash em 1 commit da task
- Mensagem: `PROJ-X-0001: descricao`
- Registro no `status-tasks.json` com `commitHash` e `rollbackCommand`
- Ao final: squash de todas as tasks em 1 commit para o MR

### 5. Demo ao negócio

Usando `roteiro-demo.md` + Postman collection + queries SQL.

## Comandos Principais

```bash
# Pipeline completo de refinamento
./refine-ticket.sh PROJ-123 --refine

# Ou por etapas:
./refine-ticket.sh PROJ-123 --jira-deep      # Apenas fetch Jira
./refine-ticket.sh PROJ-123 --scan-impact    # Apenas scan de código
./refine-ticket.sh PROJ-123 --questions      # Apenas perguntas
./refine-ticket.sh PROJ-123 --refinement     # Apenas refinamento

# Utilitários (legado via create-ticket-doc.sh)
./create-ticket-doc.sh PROJ-123 --fetch-only
./create-ticket-doc.sh PROJ-123 --status
./create-ticket-doc.sh PROJ-123 --deps
./create-ticket-doc.sh PROJ-123 --validate
./create-ticket-doc.sh --list-projects
./create-ticket-doc.sh --list-tickets
```

## Configuração

Copie `refine-config.json` → `refine-config.local.json` e ajuste:

```json
{
  "jira": {
    "baseUrl": "https://meuprojeto.atlassian.net",
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

Ou use variáveis de ambiente:

| Variável | Obrigatória | Descrição |
|----------|-------------|-----------|
| `JIRA_USER` | Para fetch | Email do usuário Jira |
| `JIRA_TOKEN` | Para fetch | Token de API do Jira |
| `JIRA_BASE` | Para fetch | URL base do Jira |

## Licença

MIT
