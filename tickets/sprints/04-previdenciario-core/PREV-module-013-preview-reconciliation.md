# Modulo: Previa e Conciliacao (Preview & Reconciliation)

## Objetivo de Negocio
Antes de processar contribuicoes ou fechar uma competencia, o sistema gera uma previa do resultado para que o operador confira, ajuste divergencias e so entao confirme o processamento. Reduz erros e evita retrabalho.

## O que Existe nos Legados

### mapsdataa-previdenciario
- Previa de arrecadacao com conciliacao entre contribuicoes e emprestimos
- Geracao de previa antes do processamento definitivo
- Conciliacao automatica aponta divergencias para revisao manual

## Lacuna de Mercado
No mercado de previdencia, o processamento cego (sem previa) gera retrabalho e erros que afetam o participante. Um passo de conferencia antes de efetivar e uma boa pratica regulatoria que poucos sistemas oferecem de forma integrada.

## Regras de Negocio
1. Ao solicitar processamento de contribuicoes, o sistema gera uma previa com valores projetados
2. A previa compara: valor esperado vs valor apurado, destacando diferencas
3. Divergencias acima de um percentual configurado exigem revisao manual
4. Operador pode ajustar valores na previa antes de confirmar
5. Apos confirmada, a previa vira processamento definitivo
6. Conciliacao tambem cobre emprestimos: valores descontados vs valores repassados
7. Historico de previas e mantido para auditoria

## Criterios de Aceitacao
1. Ao solicitar processamento do mes, sistema gera previa em menos de 1 minuto
2. Previa destaca participantes com divergencia acima de 5% para revisao
3. Operador ajusta valor manualmente e sistema recalcula a previa
4. Confirmacao da previa dispara o processamento definitivo
5. Conciliacao de emprestimos aponta descontos sem repasse correspondente
6. Historico mostra todas as previas geradas, com data e responsavel
