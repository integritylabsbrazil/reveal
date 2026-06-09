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
| **Squad** | {{SQUAD}} |
| **Sistema** | {{SYSTEM}} |
| **Epico** | {{EPIC}} |
| **Componentes** | {{COMPONENTS}} |

{% if CUSTOM_FIELDS %}
### Campos Personalizados

| Campo | Valor |
|-------|-------|
{{CUSTOM_FIELDS}}
{% endif %}

---

## 2. Objetivo Funcional

{{OBJETIVO_FUNCIONAL}}

---

## 3. Contexto de Negócio

### Problema Atual

{{CONTEXTO_PROBLEMA}}

### Impacto

{{CONTEXTO_IMPACTO}}

### Objetivo Esperado

{{CONTEXTO_OBJETIVO}}

### Fluxo Atual

```
{{FLUXO_ATUAL}}
```

### Fluxo Novo

```
{{FLUXO_NOVO}}
```

---

## 4. Impacto Técnico

### Módulos Afetados

{{MODULOS_AFETADOS}}

### Componentes Afetados

#### Backend

{{COMPONENTES_BACKEND}}

{% if COMPONENTES_FRONTEND %}
#### Frontend

{{COMPONENTES_FRONTEND}}
{% endif %}

#### Banco

{{COMPONENTES_BANCO}}

### Arquivos Identificados (Scan)

Os arquivos abaixo foram identificados pelo scan de código como potencialmente relevantes para esta demanda:

{{SCAN_HTML}}

---

## 5. Fluxo Técnico

```
{{FLOW_DIAGRAM}}
```

---

## 6. Decisões Técnicas Pendentes

| Decisão | Impacto | Área |
|---------|---------|------|
{{DECISIONS_TABLE}}

---

## 7. Riscos Técnicos

| Risco | Probabilidade | Impacto | Mitigação |
|-------|-------------|---------|-----------|
{{RISKS_TABLE}}

---

## 8. Perguntas para o Negócio

{{QUESTIONS_TABLE}}

---

## 9. Configurações de Ambiente

{{CONFIG_AMBIENTE}}

---

## 10. Dependências Externas

{{DEPENDENCIAS_EXTERNAS}}

---

## 11. Segurança e Permissões

{{SEGURANCA_PERMISSOES}}

---

## 12. Observações Técnicas por Task

Esta seção contém orientações específicas para desenvolvedores, com referência a padrões existentes no código fonte.

{{TECHNICAL_OBSERVATIONS}}

---

## 13. Tasks

{{TASKS_LIST}}

Consulte **`implementation-plan.md`** para o guia detalhado de implementação por task, com código concreto (entity, DTO, migration, service, controller).

---

## 14. Checklist de Implementação

{{CHECKLIST}}

---

## 15. Matriz de Rastreabilidade Negócio-Técnico

Esta matriz mostra como as respostas às perguntas de negócio influenciam as decisões técnicas e as tasks de implementação.

{{TRACEABILITY_MATRIX}}

---

*Documento gerado em {{DATE}} pelo sistema de refinamento técnico*