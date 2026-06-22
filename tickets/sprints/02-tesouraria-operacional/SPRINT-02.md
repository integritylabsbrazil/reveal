# Sprint 02: Tesouraria Operacional

## Objetivo de Negocio
Operacoes financeiras do fundo de previdencia: lancamentos, pagamentos, conciliacao bancaria, aprovacao de transacoes e projecao de fluxo de caixa. Substitui o modulo de tesouraria do legado com uma arquitetura event-sourced, imutavel e com deteccao de anomalias.

## Legados Afetados

| Legado | O que e substituido |
|--------|-------------------|
| dataa-tesouraria | LANCAMENTO_SIMPLES (307 classes), REMESSA (28), CONCILIACAO (149), INTEGRACAO_BANCARIA (130), FECHAMENTO_FINANCEIRO (138) |

## Lacunas de Mercado Preenchidas
- Motor de transacoes event-sourced (imutavel, auditavel)
- Workflow de aprovacao com alçada (nao existe no legado)
- Conciliacao com machine learning (sugestoes de match)
- Projecao de fluxo de caixa com machine learning
- Antifraude em pagamentos (anomalias detectadas em tempo real)

## Modulos e Dependencias

| Modulo | Depende de | Descricao |
|--------|-----------|-----------|
| 001 - Transactions | 01-Members, 01-Financial | Motor de transacoes imutavel |
| 002 - Payments | 001 | Remessas, PIX, boletos, DARF |
| 003 - Reconciliation | 001, 002 | Conciliacao automatica |
| 004 - Approval | 002 | Workflow de aprovacao e alçada |
| 005 - Cashflow | 001 | Projecao de liquidez |
| 006 - Bank Integration | 002 | Gateways bancarios |

## Criterios de Aceite da Sprint
1. Transacao financeira e registrada como evento imutavel com idempotencia
2. Pagamento via PIX e processado em menos de 30 segundos
3. Conciliacao automatica faz match de 90%+ das transacoes bancarias
4. Workflow de aprovacao bloqueia pagamentos acima da alçada do usuario
5. Projecao de fluxo de caixa para 30 dias com acuracia de 85%+

## Riscos e Mitigacoes
| Risco | Mitigacao |
|-------|-----------|
| Idempotencia falha causa duplicidade de pagamento | Chave de idempotencia obrigatoria em toda transacao |
| Conciliacao com baixa taxa de match | ML progressivo + fallback manual com sugestoes |
| Falha de gateway bancario | Circuit breaker com fila de retentativa |
