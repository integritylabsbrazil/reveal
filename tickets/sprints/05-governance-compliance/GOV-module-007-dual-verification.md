# Modulo: Dupla Verificacao (Dual Verification)

## Objetivo de Negocio
Operacoes criticas — adesao, resgate, portabilidade, alteracao cadastral, emprestimo, lancamento financeiro — precisam ser aprovadas por dois operadores diferentes antes de serem efetivadas. Isso Garante seguranca, segrega funcoes e atende requisitos regulatorios.

## O que Existe nos Legados

### mapsdataa-previdenciario
- Dupla verificacao ativada por padrao para todas as operacoes criticas
- Controle fino por tipo de operacao (contribuicao, adesao, resgate, portabilidade, lancamento financeiro)
- Primeiro operador cria/altera, segundo operador confirma
- Relatorio de operacoes pendentes de segunda aprovacao

## Lacuna de Mercado
Poucos sistemas de previdencia implementam dupla verificacao de forma nativa. A exigencia regulatoria existe, mas na pratica muitos sistemas permitem que um unico operador execute operacoes criticas — o que e um risco de fraude e nao conformidade.

## Regras de Negocio
1. Operacoes sujeitas a dupla verificacao: adesao, resgate, portabilidade, emprestimo, alteracao cadastral de dados sensiveis, lancamento financeiro acima de valor definido
2. Primeiro operador cria ou altera o registro — ele fica como "pendente de aprovacao"
3. Segundo operador (diferente do primeiro) revisa e aprova ou rejeita
4. Se rejeitar, motivo e registrado e o primeiro operador e notificado para ajustar
5. Enquanto pendente, o registro nao produz efeitos financeiros
6. Operador nao pode aprovar a propria operacao
7. Inquilino pode configurar quais operacoes exigem dupla verificacao e a partir de qual valor

## Criterios de Aceitacao
1. Adesao criada por operador A fica pendente ate operador B aprovar
2. Operador B rejeita adesao com motivo — operador A recebe notificacao
3. Enquanto pendente, participante nao aparece em saldos ou relatorios
4. Operador A tenta aprovar propria adesao — sistema bloqueia
5. Resgate acima do valor configurado exige dupla verificacao
6. Relatorio de operacoes pendentes mostra todas as que aguardam segunda aprovacao
