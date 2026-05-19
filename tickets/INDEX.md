# Índice de Tickets — Reveal

Lista de tickets documentados neste repositório.

| Ticket | Resumo | Tarefas | Progresso |
|--------|--------|---------|-----------|
| [_template](./_template/) | Modelo para novos tickets (não é um ticket real) | 4 | 0/4 ⏳ |

---

## Como Adicionar um Ticket

```bash
# 1. Buscar dados do Jira
export JIRA_USER="seu.email@empresa.com"
export JIRA_TOKEN="seu-token"
export JIRA_BASE="https://seujira.atlassian.net"

./refine-ticket.sh PROJ-123 --refine

# 2. O ticket será criado em tickets/PROJ-123/
```

---

*Gerado em 2026-01-01T00:00:00*

> ⚠️ **Nota:** Tickets com dados reais de clientes não devem ser commitados.
> Use `tickets/_template/` como referência para novos tickets.
