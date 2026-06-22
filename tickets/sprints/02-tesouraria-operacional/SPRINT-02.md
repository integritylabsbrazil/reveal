# Sprint 02: Tesouraria Operacional

## Objetivo de Negocio
Operacoes financeiras do fundo de previdencia: registrar movimentacoes, fazer pagamentos, conciliar com bancos, aprovar transacoes e projetar fluxo de caixa. Toda transacao e registrada de forma que nunca possa ser apagada — apenas corrigida com estorno.

## Legados Afetados
| Legado | O que e substituido |
|--------|-------------------|
| dataa-tesouraria | Lancamentos financeiros, remessas de pagamento, conciliacao bancaria, integracao bancaria, fechamento financeiro |

## Modulos e Dependencias

| Modulo | Depende de | Descricao |
|--------|-----------|-----------|
| 001 - Transactions | 01-Members, 01-Financial | Registro de movimentacoes financeiras |
| 002 - Payments | 001 | Pagamentos: TED, PIX, boletos, DARF, GPS |
| 003 - Reconciliation | 001, 002 | Conciliacao com extratos bancarios |
| 004 - Approval | 002 | Aprovacao de pagamentos conforme alçada |
| 005 - Cashflow | 001 | Projecao de fluxo de caixa |
| 006 - Bank Integration | 002 | Conexao com bancos para envio/recebimento |

## Criterios de Aceite da Sprint
1. Toda transacao registrada e imutavel — so pode ser estornada com outra transacao
2. Pagamento via PIX e processado em segundos
3. Conciliacao automatica encontra correspondencia para mais de 90% das transacoes
4. Pagamento acima da alçada do usuario fica bloqueado ate aprovacao superior
5. Projecao de fluxo de caixa para os proximos 30 dias

## Riscos e Mitigacoes
| Risco | Mitigacao |
|-------|-----------|
| Pagamento duplicado por erro de sistema | Chave unica obrigatoria por transacao |
| Conciliacao com baixa taxa de acerto | Sugestoes automaticas + conferencia manual |
| Falha de comunicacao com banco | Retentativa automatica com notificacao |
