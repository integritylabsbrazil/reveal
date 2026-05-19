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
| **Épico** | {{EPIC_KEY}}: {{EPIC_SUMMARY}} |

## 2. Projetos e Módulos Afetados

{{SCAN_RESULT}}

## 3. Visão Geral

**Tipo de alteração:** {{CHANGE_TYPE}}

### Descrição

{{DESCRIPTION}}

## 4. Fluxo de Dados (Proposto)

```
[Entrada]
  │
  ├─> [Validação / Toggle]
  │     ├─ Desabilitado → log + skip
  │     └─ Habilitado → continua
  │
  ├─> [Montar Request]
  │
  ├─> [Chamar API]
  │     ├─ Sucesso → processar
  │     ├─ Erro → tratar
  │     └─ Timeout → retry?
  │
  └─> [Atualizar Escopo]
       │
       └─> [Continuar fluxo]
```

## 5. Arquivos Sugeridos

{{SUGGESTED_FILES}}

## 6. Decisões Técnicas Pendentes

| Decisão | Impacto | Área |
|---------|---------|------|
| {{DECISAO_1}} | Alto | {{AREA}} |

## 7. Riscos Técnicos

| Risco | Probabilidade | Impacto | Mitigação |
|-------|-------------|---------|-----------|
| {{RISCO_1}} | Média | Alto | {{MITIGACAO}} |

## 8. Perguntas para o Negócio

{{QUESTIONS_TABLE}}

## 9. Subtarefas (Proposta)

{{TASKS_PROPOSAL}}

## 10. Checklist de Implementação

- [ ] **Análise:** Entendimento do negócio validado com PO
- [ ] **Perguntas:** Todas as perguntas respondidas
- [ ] **Design:** Arquitetura revisada
- [ ] **Modelos:** DTOs/entidades criados
- [ ] **Interface:** Interface do serviço definida
- [ ] **Integração:** Endpoint implementado
- [ ] **Lógica:** Regras de negócio implementadas
- [ ] **Erros:** Tratamento de erros configurado
- [ ] **Testes unitários:** Cobertura mínima
- [ ] **Testes integração:** Fluxo completo
- [ ] **Configuração:** Parâmetros configurados
- [ ] **Documentação:** Atualizada
- [ ] **Review:** Code review realizado
- [ ] **QA:** Testes de aceite executados

---

*Documento gerado em {{DATE}}*
