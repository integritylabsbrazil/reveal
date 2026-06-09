# Template de Ticket

Este diretório contém arquivos `.example` que servem como modelo para a
documentação de tickets gerada pelo Reveal.

## Arquivos

| Arquivo | Finalidade |
|---------|-----------|
| `description.md.example` | Descrição do ticket enriquecida com análise de negócio |
| `roteiro-demo.md.example` | Script de apresentação para demonstração ao negócio |
| `jira-data.json.example` | Dados brutos da API Jira (usado pelo pipeline) |
| `perguntas-negocio.md.example` | Perguntas para o PO/analista |
| `refinamento-tecnico.md.example` | Documento completo de refinamento técnico |
| `implementation-plan.md.example` | Plano de implementação, riscos e cronograma |
| `status-tasks.json.example` | Subtarefas com nível de senioridade e status |

## Como Usar

Para criar documentação de um ticket real, execute o pipeline:

```bash
./gerar-documentacao.sh PROJ-123
```

Ou em etapas:

```bash
./refine-ticket.sh PROJ-123 --refine
```

Os arquivos gerados seguem a mesma estrutura dos `.example` mas com dados reais.
