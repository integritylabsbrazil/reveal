# Modulo: Transactions Engine

## Objetivo de Negocio
Registrar toda movimentacao financeira do fundo de forma que nenhuma transacao possa ser alterada ou apagada. Qualquer correcao gera uma nova transacao de estorno vinculada a original. Garantia de auditoria completa.

## O que Existe no Legado

### dataa-tesouraria
- Lancamentos financeiros que podem ser alterados e excluidos (risco de auditoria)
- Movimentacoes vinculadas a lancamentos
- Folha de pagamento
- Historico em texto livre
- Debitos avulsos

## Lacuna de Mercado
- Transacao imutavel: uma vez registrada, vira parte do historico permanente
- Estorno obrigatorio: para corrigir, precisa lancar uma transacao de reversao
- Rastreabilidade completa: quem criou, quando, por que, qual a origem

## Regras de Negocio
1. Toda transacao tem: tipo, participante, fundo, valor, data e motivo
2. Transacoes nao podem ser alteradas ou excluidas depois de confirmadas
3. Para corrigir: criar transacao de estorno referenciando a original
4. Saldo do fundo e a soma de todas as transacoes nao estornadas
5. Transacoes tem situacao: pendente, confirmada, estornada ou rejeitada
6. Cada transacao registra quem criou, quem aprovou e quando

## Criterios de Aceitacao
1. Transacao confirmada aparece no saldo do fundo
2. Estorno reverte o efeito no saldo e mantem referencia a original
3. Nao e possivel alterar nenhum dado de uma transacao ja confirmada
4. Historico mostra data, usuario e motivo de cada acao na transacao
5. Saldo calculado corretamente mesmo com milhares de transacoes

## Dependencias
- 01-Members, 01-Financial Institutions
