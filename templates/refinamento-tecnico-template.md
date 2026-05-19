# Refinamento Técnico — {{TICKET_ID}}

**{{SUMMARY}}**

---

## 1. Dados do Ticket

| Campo | Valor |
|-------|-------|
| **Ticket** | {{TICKET_ID}} |
| **Tipo** | {{ISSUE_TYPE}} |
| **Prioridade** | {{PRIORITY}} |
| **Status** | {{STATUS}} |
| **Responsável** | {{ASSIGNEE}} |
| **Solicitante** | {{REPORTER}} |
| **Componentes** | {{COMPONENTS}} |
| **Épico** | {{EPIC}} |

{% if CUSTOM_FIELDS %}
### Campos Personalizados

| Campo | Valor |
|-------|-------|
{{CUSTOM_FIELDS}}
{% endif %}

## 2. Projetos e Módulos Afetados

{{SCAN_HTML}}

## 3. Visão Geral

**Tipo de alteração:** {{CHANGE_TYPE}}

### Descrição

{{DESCRIPTION}}

## 4. Fluxo de Dados (Proposto)

```
{{FLOW_DIAGRAM}}
```

## 5. Arquivos Sugeridos

{{SUGGESTED_FILES}}

## 6. Decisões Técnicas Pendentes

| Decisão | Impacto | Área |
|---------|---------|------|
{{DECISIONS_TABLE}}

## 7. Riscos Técnicos

| Risco | Probabilidade | Impacto | Mitigação |
|-------|-------------|---------|-----------|
{{RISKS_TABLE}}

## 8. Perguntas para o Negócio

{{QUESTIONS_TABLE}}

## 9. Subtarefas (Proposta)

{{TASKS_TABLE}}

## 10. Checklist de Implementação

{{CHECKLIST}}

---

*Documento gerado em {{DATE}} pelo sistema de refinamento técnico*
