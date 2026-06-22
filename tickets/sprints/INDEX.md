# ClearPension — Mapa de Requisitos

## Visao Geral dos 7 Blocos de Construcao

```
+-----------------------------------------------------------------------+
|                  ClearPension — Plataforma de Previdencia              |
+----------+----------+----------+----------+----------+---------------+
| Cadastro |Tesouraria| Contabil |Previden- |Governanca| Ecossistema   |
| Unificado|Operacion.| Fiscal   |ciario    |Compliance| Digital       |
+----------+----------+----------+----------+----------+---------------+
|                      Modulo de Infraestrutura                        |
|          (Cadastro de Entidades, Acesso, Importacao)                  |
+-----------------------------------------------------------------------+
```

---

## Mapa de Artefatos

### Sprint 00 — Fundacao
| Modulo | Arquivo | Prioridade | Legados Resolve |
|--------|---------|-----------|-----------------|
| Cadastro de Entidades | `FUNDATION-module-001-registry.md` | Alta | Novo |
| Identidade e Acesso | `FUNDATION-module-002-identity.md` | Alta | Usuarios e permissoes |
| Ferramentas de Importacao | `FUNDATION-module-003-import-tools.md` | Alta | Migracao de legados |

### Sprint 01 — Cadastro Unificado
| Modulo | Arquivo | Prioridade | Legados Resolve |
|--------|---------|-----------|-----------------|
| Members | `CADASTRO-module-001-members.md` | Alta | Favorecidos, participantes, patrocinadores |
| Funds | `CADASTRO-module-002-funds.md` | Alta | Planos de beneficio, convenios |
| Instituicoes Financeiras | `CADASTRO-module-003-financial.md` | Alta | Bancos, agencias, contas |
| Estrutura Organizacional | `CADASTRO-module-004-structure.md` | Media | Centros de custo, departamentos |
| Gestao Documental | `CADASTRO-module-005-documents.md` | Alta | Novo |

### Sprint 02 — Tesouraria Operacional
| Modulo | Arquivo | Prioridade | Legados Resolve |
|--------|---------|-----------|-----------------|
| Transacoes Financeiras | `TESOURARIA-module-001-transactions.md` | Alta | Lancamentos financeiros |
| Pagamentos | `TESOURARIA-module-002-payments.md` | Alta | Remessas, PIX, boletos |
| Conciliacao | `TESOURARIA-module-003-reconciliation.md` | Alta | Conciliacao bancaria |
| Aprovacao e Alçada | `TESOURARIA-module-004-approval.md` | Alta | Novo |
| Fluxo de Caixa | `TESOURARIA-module-005-cashflow.md` | Media | Novo |
| Integracao Bancaria | `TESOURARIA-module-006-bank-integration.md` | Alta | Integracao com bancos |

### Sprint 03 — Contabil Fiscal
| Modulo | Arquivo | Prioridade | Legados Resolve |
|--------|---------|-----------|-----------------|
| Plano de Contas | `CONTABIL-module-001-chart-of-accounts.md` | Alta | Planificacao contabil |
| Motor de Lancamentos | `CONTABIL-module-002-journal-engine.md` | Alta | Fatos geradores, lotes |
| Fechamento Contabil | `CONTABIL-module-003-closing.md` | Alta | Fechamento, consolidado |
| DRE e Balanco | `CONTABIL-module-004-dre-balance.md` | Alta | Balancete, razao, diario |
| Rateio de Custos | `CONTABIL-module-005-cost-allocation.md` | Media | Custeio, criterios de rateio |
| Inteligencia de Custos | `CONTABIL-module-006-cost-intelligence.md` | Media | Novo |
| Retencoes | `FISCAL-module-001-withholding.md` | Alta | Retencoes fiscais |
| Obrigacoes Acessorias | `FISCAL-module-002-obligations.md` | Alta | EFD, REINF |
| Radar Regulatorio | `FISCAL-module-003-regulation-radar.md` | Media | Novo |

### Sprint 04 — Previdenciario Core
| Modulo | Arquivo | Prioridade | Legados Resolve |
|--------|---------|-----------|-----------------|
| Adesao | `PREV-module-001-membership.md` | Alta | Adesao, inscricao, vinculo |
| Contribuicoes | `PREV-module-002-contributions.md` | Alta | Contribuicoes, folha, salario |
| Beneficios | `PREV-module-003-benefits.md` | Alta | Beneficiarios, dependentes, calculo |
| Folha de Beneficio | `PREV-module-004-payroll.md` | Alta | Folha, fechamento de competencia |
| Emprestimos | `PREV-module-005-loans.md` | Media | Emprestimos consignados |
| Portabilidade | `PREV-module-006-portability.md` | Alta | Portabilidade entrada/saida |
| Cotas | `PREV-module-007-quota.md` | Alta | Cotas, memoria de calculo, posicao |
| Investimentos | `PREV-module-008-investment.md` | Alta | Perfis, subcontas, aplicacao |
| Indexacao e Saldo | `PREV-module-009-valuation.md` | Media | Indexadores, saldo, extrato |
| Processamento | `PREV-module-010-processing.md` | Alta | Processamento batch, modelos |
| Parametrizacao | `PREV-module-011-parameterization.md` | Alta | Regras configuradas pelo cliente |
| Onboarding Digital | `PREV-module-012-digital-onboarding.md` | Alta | Novo |
| Previa e Conciliacao | `PREV-module-013-preview-reconciliation.md` | Alta | Previa antes do processamento |
| Pos-Liquidacao | `PREV-module-014-post-settlement.md` | Alta | Acoes apos liquidar operacao |
| Fechamento de Competencia | `PREV-module-015-period-closing.md` | Alta | Fechamento mensal previdenciario |

### Sprint 05 — Governance & Compliance
| Modulo | Arquivo | Prioridade | Legados Resolve |
|--------|---------|-----------|-----------------|
| Orgaos Colegiados | `GOV-module-001-board.md` | Media | Novo |
| Trilha de Auditoria | `GOV-module-002-audit.md` | Alta | Auditoria de operacoes |
| Relatorios Regulatorios | `GOV-module-003-regulatory-reporting.md` | Alta | Relatorios PREVIC, CVM |
| Simulacao Atuarial | `GOV-module-004-actuarial-simulation.md` | Media | Novo |
| Workflow de Documentos | `GOV-module-005-document-workflow.md` | Media | Workflow de processos |
| Prevencao a Fraude | `GOV-module-006-fraud-prevention.md` | Alta | Novo |
| Dupla Verificacao | `GOV-module-007-dual-verification.md` | Alta | Dupla aprovacao para operacoes criticas |

### Sprint 06 — Ecossistema Digital
| Modulo | Arquivo | Prioridade | Legados Resolve |
|--------|---------|-----------|-----------------|
| Aplicativo Movel | `ECO-module-001-mobile-app.md` | Alta | Novo |
| Engajamento | `ECO-module-002-engagement.md` | Media | Novo |
| API Publica | `ECO-module-003-open-api.md` | Alta | Novo |
| Open Finance | `ECO-module-004-open-finance.md` | Media | Novo |
| Marketplace | `ECO-module-005-marketplace.md` | Baixa | Novo |
| Benchmarking | `ECO-module-006-benchmarking.md` | Media | Novo |
| Analytics e BI | `ECO-module-007-analytics-bi.md` | Media | Novo |

### Sprint 07 — Scale 50 Clients
| Modulo | Arquivo | Prioridade | Legados Resolve |
|--------|---------|-----------|-----------------|
| Expansao EAPC | `SCALE-module-001-eapc.md` | Media | Novo |
| Autogestao de Saude | `SCALE-module-002-health-insurance.md` | Baixa | Novo |
| Clubes de Investimento | `SCALE-module-003-investment-clubs.md` | Baixa | Novo |
| Enterprise | `SCALE-module-004-enterprise.md` | Media | Novo |
| White Label | `SCALE-module-005-white-label.md` | Baixa | Novo |
| Internacionalizacao | `SCALE-module-006-international.md` | Baixa | Novo |

---

## Legenda

| Simbolo | Significado |
|---------|-------------|
| **Tesouraria** | Processo existente no sistema dataa-tesouraria |
| **Previdenciario** | Processo existente no sistema mapsdataa-previdenciario |
| **Novo** | Funcionalidade que nao existe em nenhum legado — inovacao |

---

*Documento gerado em 2026-06-22 — ClearPension*
