# Modulo: Pos-Liquidacao (Post-Settlement)

## Objetivo de Negocio
Apos liquidar uma operacao (adesao, resgate, portabilidade, emprestimo), acoes automaticas precisam ocorrer: contabilizar o evento, atualizar saldo de cotas, notificar o participante e registrar na auditoria. Este modulo gerencia essas acoes pos-evento.

## O que Existe nos Legados

### mapsdataa-previdenciario
- Servicos de pos-liquidacao para cada tipo de operacao:
  - Adesao a beneficio: apos aderir, calcular e registrar primeira contribuicao
  - Resgate total: apos resgatar, encerrar vinculo e calcular impostos
  - Portabilidade: apos portar, liquidar contribuicoes de entrada
  - Folha de pagamento: apos fechar folha, efetivar pagamentos

## Lacuna de Mercado
Sistemas tradicionais tratam a liquidacao como fim do processo. Na pratica, e quando comeca o trabalho de contabilizacao, atualizacao de saldos e notificacao. Automatizar esse pos-evento reduz erros manuais e agiliza a disponibilidade da informacao para o participante.

## Regras de Negocio
1. Cada tipo de operacao tem uma sequencia de acoes pos-liquidacao
2. Adesao a plano: apos confirmada, criar vinculo, calcular primeira contribuicao, notificar
3. Resgate: apos liquidado, encerrar vinculo, calcular tributos, liberar valor, notificar
4. Portabilidade: apos liquidada entrada, alocar contribuicoes no plano destino, notificar
5. Emprestimo: apos contratado, liberar credito na conta do participante
6. Se alguma acao pos-liquidacao falhar, a operacao principal nao e desfeita — a falha fica registrada para revisao
7. Participante recebe notificacao a cada acao pos-liquidacao concluida

## Criterios de Aceitacao
1. Apos adesao a plano, participante recebe notificacao e primeira contribuicao e calculada
2. Apos resgate total, vinculo e encerrado e valor e disponibilizado na conta
3. Apos portabilidade, contribuicoes sao alocadas no novo plano
4. Falha em acao pos-liquidacao e registrada para revisao manual
5. Participante recebe notificacao (email ou app) de cada etapa concluida
