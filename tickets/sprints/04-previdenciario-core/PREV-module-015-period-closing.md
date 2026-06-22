# Modulo: Fechamento de Competencia (Period Closing)

## Objetivo de Negocio
Fechar o mes de operacoes do fundo de previdencia: validar que todos os dados estao consistentes, gerar demonstrativos legais e bloquear novas movimentacoes na competencia encerrada. Cada mes fechado vira um periodo contabil imutavel.

## O que Existe nos Legados

### mapsdataa-previdenciario
- Fechamento de competencia com status especificos
- Validacao de consistencia antes de fechar
- Bloqueio de movimentacao em periodo fechado
- Controles para garantir que contribuicoes, beneficios e emprestimos estao conciliados

## Lacuna de Mercado
Fechamento de competencia nos legados e manual e suscetivel a erros. Um fechamento automatizado com validacoes integradas (contribuicao vs folha vs beneficios vs emprestimos) reduz riscos regulatorios e agiliza a disponibilidade dos demonstrativos.

## Regras de Negocio
1. Fechamento e mensal e segue o calendario de competencias
2. Antes de fechar, o sistema valida: todas as contribuicoes processadas, folhas fechadas, emprestimos conciliados
3. Se houver inconsistencia, o fechamento e bloqueado ate correcao
4. Apos fechado, a competencia nao permite novas movimentacoes
5. Fechamento gera demonstrativos: relacao de participantes, valores contribuidos, beneficios pagos
6. Fechamento pode ser refeito (reabertura) mediante autorizacao, com registro em auditoria
7. Historico de fechamentos: todas as competencias fechadas ficam disponiveis para consulta

## Criterios de Aceitacao
1. Ao solicitar fechamento do mes, sistema valida automaticamente todos os dados
2. Se faltar processar contribuicoes, sistema bloqueia e informa o motivo
3. Apos fechado, nova movimentacao na competencia e impedida
4. Demonstrativo de fechamento e gerado e disponivel para download
5. Reabertura de competencia e registrada em auditoria com data e responsavel
6. Consulta historica mostra todos os meses fechados e seus demonstrativos
