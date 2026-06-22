# ClearPension — Mapa de Requisitos

## Visão Geral dos 7 Blocos de Construção

---

## Arquitetura: Spring Modulith

Cada módulo abaixo é um módulo Maven/Gradle independente dentro de um mesmo runtime (modulith), com suas próprias tabelas de banco (database-per-module), API interna exposta apenas para outros módulos via interfaces Java, e API externa via REST/GraphQL.

```
+-----------------------------------------------------------------------+
|                        API Gateway / BFF                              |
+----------+----------+----------+----------+----------+---------------+
| Cadastro |Tesouraria| Contábil |Previden- |Governança| Ecossistema   |
| Unificado|Operacion.| Fiscal   |ciário    |Compliance| Digital       |
+----------+----------+----------+----------+----------+---------------+
|                      Módulo de Infraestrutura                        |
|          (Tenant Registry, Identity/Auth, Import Tools)               |
+-----------------------------------------------------------------------+
```

---

## Mapa de Artefatos

### Sprint 00 — Fundação
| Módulo | Arquivo | Prioridade | Legados Resolve |
|--------|---------|-----------|-----------------|
| Tenant Registry | `FUNDATION-module-001-registry.md` | Alta | Nenhum (novo) |
| Identity & Auth | `FUNDATION-module-002-identity.md` | Alta | USUARIO, perfis |
| Import Tools | `FUNDATION-module-003-import-tools.md` | Alta | Migração de legados |

### Sprint 01 — Cadastro Unificado
| Módulo | Arquivo | Prioridade | Legados Resolve |
|--------|---------|-----------|-----------------|
| Members | `CADASTRO-module-001-members.md` | Alta | FAVORECIDO, PARTICIPANTE, PATROCINADOR |
| Funds | `CADASTRO-module-002-funds.md` | Alta | PLANO, PLANO_BENEFICIO, CONVENIO |
| Financial Institutions | `CADASTRO-module-003-financial.md` | Alta | INSTITUICAO_FINANCEIRA, AGENCIA, CONTA_BANCARIA |
| Organizational Structure | `CADASTRO-module-004-structure.md` | Média | CENTRO_CUSTO, DEPARTAMENTO |
| Document Management | `CADASTRO-module-005-documents.md` | Alta | Gap do mercado |

### Sprint 02 — Tesouraria Operacional
| Módulo | Arquivo | Prioridade | Legados Resolve |
|--------|---------|-----------|-----------------|
| Transactions Engine | `TESOURARIA-module-001-transactions.md` | Alta | LANCAMENTO_SIMPLES, MOVIMENTACAO_FINANCEIRA |
| Payments & Remittances | `TESOURARIA-module-002-payments.md` | Alta | REMESSA, PIX, BB_PAGAMENTO |
| Reconciliation | `TESOURARIA-module-003-reconciliation.md` | Alta | FITID, MOV_BANCARIO, SALDO_INICIAL |
| Approval Workflow | `TESOURARIA-module-004-approval.md` | Alta | Gap do mercado |
| Cashflow & Liquidity | `TESOURARIA-module-005-cashflow.md` | Média | Gap do mercado |
| Bank Integration | `TESOURARIA-module-006-bank-integration.md` | Alta | INTEGRACAO_BANCARIA |

### Sprint 03 — Contábil Fiscal
| Módulo | Arquivo | Prioridade | Legados Resolve |
|--------|---------|-----------|-----------------|
| Chart of Accounts | `CONTABIL-module-001-chart-of-accounts.md` | Alta | PLANIFICACAO, NATUREZA_FINANCEIRA, NUMERACAO |
| Journal Engine | `CONTABIL-module-002-journal-engine.md` | Alta | FATO_GERADOR, LOTE, EVENTO_CONTABIL |
| Closing | `CONTABIL-module-003-closing.md` | Alta | FECHAMENTO_CONTABIL, CONSOLIDADO |
| DRE & Balance | `CONTABIL-module-004-dre-balance.md` | Alta | BALANCETE, RAZAO, DIARIO |
| Cost Allocation | `CONTABIL-module-005-cost-allocation.md` | Média | CUSTEIO, CRITERIO_RATEIO, DISPONIVEL |
| Cost Intelligence | `CONTABIL-module-006-cost-intelligence.md` | Média | Gap do mercado |
| Withholding | `FISCAL-module-001-withholding.md` | Alta | RETENCAO, CODIGO_RETENCAO |
| Fiscal Obligations | `FISCAL-module-002-obligations.md` | Alta | EFD, REINF, PIS/COFINS |
| Regulation Radar | `FISCAL-module-003-regulation-radar.md` | Média | Gap do mercado |

### Sprint 04 — Previdenciário Core
| Módulo | Arquivo | Prioridade | Legados Resolve |
|--------|---------|-----------|-----------------|
| Membership | `PREV-module-001-membership.md` | Alta | ADESAO, INSCRICAO_SUBMASSA, VINCULO |
| Contributions | `PREV-module-002-contributions.md` | Alta | CONTRIBUICAO, FOLHA_PAGAMENTO, SALARIO |
| Benefits | `PREV-module-003-benefits.md` | Alta | BENEFICIARIO, DEPENDENTE, CALCULO |
| Payroll | `PREV-module-004-payroll.md` | Alta | FOLHA_BENEFICIO, FECHAMENTO_COMPETENCIA |
| Loans | `PREV-module-005-loans.md` | Média | EMPRESTIMO |
| Portability | `PREV-module-006-portability.md` | Alta | PORTABILIDADE |
| Quota | `PREV-module-007-quota.md` | Alta | COTA, MEMORIA_CALCULO, POSICAO_ATUAL |
| Investment | `PREV-module-008-investment.md` | Alta | PERFIL_INVESTIMENTO, SUB_CONTA, APLICACAO |
| Valuation | `PREV-module-009-valuation.md` | Média | INDEXADOR, SALDO, EXTRATO |
| Batch Processing | `PREV-module-010-processing.md` | Alta | PROCESSAMENTO, MODELO_CALCULO, PREVIA |
| Parameterization | `PREV-module-011-parameterization.md` | Alta | PARAMETRIZACAO, CONFIGURACAO |
| Digital Onboarding | `PREV-module-012-digital-onboarding.md` | Alta | Gap do mercado |

### Sprint 05 — Governance & Compliance
| Módulo | Arquivo | Prioridade | Legados Resolve |
|--------|---------|-----------|-----------------|
| Board Management | `GOV-module-001-board.md` | Média | Gap do mercado |
| Audit Trail | `GOV-module-002-audit.md` | Alta | TRILHA_AUDITORIA |
| Regulatory Reporting | `GOV-module-003-regulatory-reporting.md` | Alta | RELATORIOS PREVIC, CVM |
| Actuarial Simulation | `GOV-module-004-actuarial-simulation.md` | Média | Gap do mercado |
| Document Workflow | `GOV-module-005-document-workflow.md` | Média | WORKFLOW |
| Fraud Prevention | `GOV-module-006-fraud-prevention.md` | Alta | Gap do mercado |

### Sprint 06 — Ecossistema Digital
| Módulo | Arquivo | Prioridade | Legados Resolve |
|--------|---------|-----------|-----------------|
| Mobile App | `ECO-module-001-mobile-app.md` | Alta | Gap do mercado |
| Engagement | `ECO-module-002-engagement.md` | Média | Gap do mercado |
| Open API | `ECO-module-003-open-api.md` | Alta | Gap do mercado |
| Open Finance | `ECO-module-004-open-finance.md` | Média | Gap do mercado |
| Marketplace | `ECO-module-005-marketplace.md` | Baixa | Gap do mercado |
| Benchmarking | `ECO-module-006-benchmarking.md` | Média | Gap do mercado |
| Analytics & BI | `ECO-module-007-analytics-bi.md` | Média | Gap do mercado |

### Sprint 07 — Scale 50 Clients
| Módulo | Arquivo | Prioridade | Legados Resolve |
|--------|---------|-----------|-----------------|
| EAPC Expansion | `SCALE-module-001-eapc.md` | Média | Gap do mercado |
| Health Insurance | `SCALE-module-002-health-insurance.md` | Baixa | Gap do mercado |
| Investment Clubs | `SCALE-module-003-investment-clubs.md` | Baixa | Gap do mercado |
| Enterprise | `SCALE-module-004-enterprise.md` | Média | Gap do mercado |
| White Label | `SCALE-module-005-white-label.md` | Baixa | Gap do mercado |
| International | `SCALE-module-006-international.md` | Baixa | Gap do mercado |

---

## Legenda

| Simbolo | Significado |
|---------|-------------|
| **Tesouraria** | Dominio existente no sistema dataa-tesouraria (2.781 classes, 127 tabelas) |
| **Previdenciario** | Dominio existente no sistema mapsdataa-previdenciario (3.673 classes) |
| **Gap do mercado** | Funcionalidade que NAO existe em nenhum dos legados — inovacao pura |
| **Existe em ambos** | Dominio presente nos dois sistemas, sera unificado |

---

*Documento gerado em 2026-06-22 — ClearPension*
