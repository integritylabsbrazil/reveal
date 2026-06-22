# Plano: Criar Requisitos ClearPension

## Contexto
Este plano descreve a criação de ~51 arquivos de requisitos no padrão Jira para o SaaS ClearPension, substituindo os sistemas legados dataa-tesouraria e mapsdataa-previdenciario.

## Estrutura de Diretórios
```
tickets/sprints/
├── INDEX.md
├── 00-fundation/
│   ├── SPRINT-00.md
│   ├── FUNDATION-module-001-registry.md
│   ├── FUNDATION-module-002-identity.md
│   └── FUNDATION-module-003-import-tools.md
├── 01-cadastro-unificado/
│   ├── SPRINT-01.md
│   ├── CADASTRO-module-001-members.md
│   ├── CADASTRO-module-002-funds.md
│   ├── CADASTRO-module-003-financial.md
│   ├── CADASTRO-module-004-structure.md
│   └── CADASTRO-module-005-documents.md
├── 02-tesouraria-operacional/
│   ├── SPRINT-02.md
│   ├── TESOURARIA-module-001-transactions.md
│   ├── TESOURARIA-module-002-payments.md
│   ├── TESOURARIA-module-003-reconciliation.md
│   ├── TESOURARIA-module-004-approval.md
│   ├── TESOURARIA-module-005-cashflow.md
│   └── TESOURARIA-module-006-bank-integration.md
├── 03-contabil-fiscal/
│   ├── SPRINT-03.md
│   ├── CONTABIL-module-001-chart-of-accounts.md
│   ├── CONTABIL-module-002-journal-engine.md
│   ├── CONTABIL-module-003-closing.md
│   ├── CONTABIL-module-004-dre-balance.md
│   ├── CONTABIL-module-005-cost-allocation.md
│   ├── CONTABIL-module-006-cost-intelligence.md
│   ├── FISCAL-module-001-withholding.md
│   ├── FISCAL-module-002-obligations.md
│   └── FISCAL-module-003-regulation-radar.md
├── 04-previdenciario-core/
│   ├── SPRINT-04.md
│   ├── PREV-module-001-membership.md
│   ├── PREV-module-002-contributions.md
│   ├── PREV-module-003-benefits.md
│   ├── PREV-module-004-payroll.md
│   ├── PREV-module-005-loans.md
│   ├── PREV-module-006-portability.md
│   ├── PREV-module-007-quota.md
│   ├── PREV-module-008-investment.md
│   ├── PREV-module-009-valuation.md
│   ├── PREV-module-010-processing.md
│   ├── PREV-module-011-parameterization.md
│   └── PREV-module-012-digital-onboarding.md
├── 05-governance-compliance/
│   ├── SPRINT-05.md
│   ├── GOV-module-001-board.md
│   ├── GOV-module-002-audit.md
│   ├── GOV-module-003-regulatory-reporting.md
│   ├── GOV-module-004-actuarial-simulation.md
│   ├── GOV-module-005-document-workflow.md
│   └── GOV-module-006-fraud-prevention.md
├── 06-ecossistema-digital/
│   ├── SPRINT-06.md
│   ├── ECO-module-001-mobile-app.md
│   ├── ECO-module-002-engagement.md
│   ├── ECO-module-003-open-api.md
│   ├── ECO-module-004-open-finance.md
│   ├── ECO-module-005-marketplace.md
│   ├── ECO-module-006-benchmarking.md
│   └── ECO-module-007-analytics-bi.md
├── 07-scale-50-clients/
│   ├── SPRINT-07.md
│   ├── SCALE-module-001-eapc.md
│   ├── SCALE-module-002-health-insurance.md
│   ├── SCALE-module-003-investment-clubs.md
│   ├── SCALE-module-004-enterprise.md
│   ├── SCALE-module-005-white-label.md
│   └── SCALE-module-006-international.md
```

## Template de Cada Arquivo

### SPRINT-NN.md (visão geral)
```markdown
# Sprint NN: Nome da Sprint

## Objetivo de Negocio
[Por que esta sprint existe, qual macro-problema resolve]

## Legados Afetados
[Quais dominios/classes/tabelas dos legados sao substituidos]

## Lacunas de Mercado Preenchidas
[O que e inovacao pura nesta sprint]

## Modulos e Dependencias
[Lista de modulos com dependencias entre si]

## Criterios de Aceite da Sprint
[O que precisa funcionar ao final da sprint]

## Riscos e Mitigacoes
[Principais riscos tecnicos/de negocio]
```

### MODULE-NNN-descricao.md (cada modulo)
```markdown
# Modulo: Nome do Modulo

## Objetivo de Negocio

## O que Existe nos Legados

### dataa-tesouraria
- Tabela X (descricao, ~N registros estimados)
- Classes de referencia: pacote.Y

### mapsdataa-previdenciario
- Tabela Z (descricao)
- Classes de referencia: pacote.W

## Lacuna de Mercado

## Regras de Negocio

## Criterios de Aceitacao

## Dependencias Tecnicas

## Projetos Legados de Referencia
```

## Material de Referencia para Preencher os Modulos

Para cada modulo, use estes dados reais extraidos dos codigos fonte:

### Tesouraria — Tabelas por Dominio
| Dominio | Tabelas Principais | Classes |
|---------|-------------------|---------|
| CONTABILIDADE | PLANIFICACAO, NATUREZA_FINANCEIRA, LANCAMENTO_CONTABIL, FATO_GERADOR, FECHAMENTO_CONTABIL, LOTE, DEBITO_CREDITO, PARAMETRO_CONTABIL, SALDO_CONTABIL, RATEIO, CONSOLIDADO, PARTIDA_DOBRADA, SISTEMA_CONTABIL, EVENTO_CONTABIL, CONTABIL, ITEM_NATUREZA, TIPO_CONTABIL | ~806 |
| FAVORECIDO | FAVORECIDO, BANCO, AGENCIA, CONTA_CORRENTE, ENDERECO, PROFISSAO, ESCOLARIDADE, PARENTESCO, DEPENDENTE, BENEFICIARIO, SEXO, ESTADO_CIVIL, TIPO_FAVORECIDO | ~332 |
| LANCAMENTO | LANCAMENTO_SIMPLES, MOVIMENTACAO_BANCARIA, FOLHA_PAGAMENTO, COMPETENCIA, EXTRATO, HISTORICO, DEBITOS_DIVERSOS, VALORES, MOVIMENTACAO_PROVISAO | ~307 |
| CONCILIACAO | FITID, MOVIMENTACAO, SALDO_INICIAL, EXTRATO_BANCARIO, CONCILIACAO, CONTA_BANCARIA, CONTA_FITID, OCORRENCIA, PERIODO_CONCILIACAO, IMPORTACAO | ~149 |
| FECHAMENTO | FECHAMENTO_FINANCEIRO, SALDO_CONTABIL, CONSOLIDADO, ACUMULADO | ~138 |
| INTEGRACAO | INTEGRACAO_BANCARIA, LOTE_SERVICO, AGENDAMENTO, TRANSACAO, PROCESSAMENTO_ARQUIVO | ~130 |
| REMESSA | REMESSA, PAGAMENTO, REMESSA_PAGAMENTO, BOLETO, LOTE_SERVICO, REMESSA_TIPO | ~28 |
| EFD | EFD, EFD_ESCRITURACAO, EFD_PAGAMENTO, EFD_CENTRO_CUSTO, EFD_TIPO_LANCAMENTO, EFD_AJUSTE | ~47 |
| RETENCAO | RETENCAO, CODIGO_RETENCAO, DOCUMENTO_RETENCAO, NOTA_FISCAL, GUIA_RETENCAO | ~67 |

### Previdenciario — Modulos do Liquibase
| Versao | Modulos Incluidos |
|--------|------------------|
| INIT | FUNDO_PREVIDENCIA, REGIME, TRIBUNAL, ORGAO_PUBLICO, PODER |
| 24.4-24.7 | PARAMETRIZACAO_BASICA, ENTIDADE, USUARIO, PERFIL, PLANO, PATROCINADOR, BENEFICIARIO, ADESAO |
| 24.8-24.12 | CONTRIBUICAO, FOLHA_PAGAMENTO, SALARIO, SERVIDOR, PROCESSAMENTO, FECHAMENTO |
| 25.1-25.6 | CALCULO_BENEFICIO, EMPRESTIMO, PORTABILIDADE, COTA, INDEXADOR, INVESTIMENTO, SUB_CONTA |
| 25.7-25.12 | WORKFLOW, PARECER, TRAMITE, DOCUMENTO, CONFIGURACAO, REGRA, NOTIFICACAO |
| 26.1-26.5 | EXPORTACAO, VALIDACAO, RELATORIO, LOG_INTEGRACAO, CACHE, ASSINATURA |

## Comandos para Executar o Plano

Quando a permissao de edicao estiver liberada, executar:

```bash
# 1. Criar diretorios
mkdir -p tickets/sprints/{00-fundation,01-cadastro-unificado,02-tesouraria-operacional,03-contabil-fiscal,04-previdenciario-core,05-governance-compliance,06-ecossistema-digital,07-scale-50-clients}

# 2. Criar INDEX.md usando o conteudo abaixo
cat > tickets/sprints/INDEX.md << 'INDEXEOF'
...
INDEXEOF

# 3. Para cada sprint e modulo, criar o arquivo seguindo o template
# ... (repetir para os ~50 arquivos)

# 4. Validar estrutura
find tickets/sprints -name "*.md" | sort | wc -l
# Deve retornar 51 (1 INDEX + 7 sprints + 43 modulos)
```
