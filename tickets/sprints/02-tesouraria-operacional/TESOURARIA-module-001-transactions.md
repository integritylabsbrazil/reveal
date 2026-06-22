# Modulo: Transactions Engine

## Objetivo de Negocio
Motor de transacoes financeiras imutavel, event-sourced, com CQRS. Substitui o LANCAMENTO_SIMPLES do legado por um modelo onde toda transacao e um evento que nunca pode ser alterado ou deletado — apenas compensado por outro evento.

## O que Existe no Legado

### dataa-tesouraria
- Tabela LANCAMENTO_SIMPLES: lancamentos financeiros com possibilidade de alteracao e exclusao logica
- Tabela MOVIMENTACAO_FINANCEIRA: movimentacoes vinculadas a lancamentos
- Tabela FOLHA_PAGAMENTO: folha
- Tabela COMPETENCIA: competencia contabil
- Tabela HISTORICO: historico do lancamento (texto livre)
- Tabela DEBITOS_DIVERSOS: debitos avulsos
- Modelo permite ALTERAR e EXCLUIR lancamentos (risco de auditoria)

## Lacuna de Mercado
- Modelo event-sourced: toda transacao e imutavel. Alteracao = novo evento de compensacao.
- CQRS: escrita em event store, leitura em projecoes otimizadas.
- Idempotencia: cada transacao tem chave unica para evitar duplicidade.
- Rastreabilidade completa: quem criou, quando, qual IP, qual motivo.
- Suporte a transacoes em moeda estrangeira com taxa de cambio historica.

## Regras de Negocio
1. Toda transacao tem: idempotencyKey, tipo, member, fundo, valor, data, moeda
2. Transacoes sao imutaveis: nao podem ser alteradas ou excluidas
3. Para corrigir: criar transacao de estorno (tipo = REVERSAO, referencia a original)
4. Saldo de um fundo e calculado pela soma de todas as transacoes nao estornadas
5. Transacoes tem status: PENDENTE, CONFIRMADA, ESTORNADA, REJEITADA
6. Cada transacao tem trilha de auditoria (criacao, aprovacao, confirmacao)
7. Chave de idempotencia previne processamento duplicado

## Criterios de Aceitacao
1. Criacao de transacao com idempotencyKey retorna mesma resposta em caso de repeticao
2. Transacao confirmada aparece no saldo do fundo
3. Estorno de transacao reverte o efeito no saldo com referencia a original
4. Nao e possivel alterar campos de uma transacao confirmada
5. Auditoria mostra data, usuario, IP de cada acao na transacao
6. Projecao de saldo calcula corretamente com 10k transacoes

## Dependencias Tecnicas
- 01-Members, 01-Financial Institutions

## Projetos Legados de Referencia
- Tesouraria: `src/main/java/**/lancamento/`, `src/main/java/**/movimentacao/`
- Nova implementacao usa EventStoreDB (events) + PostgreSQL (projecoes)
