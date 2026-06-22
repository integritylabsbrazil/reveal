# Sprint 04: Previdenciario Core

## Objetivo de Negocio
Nucleo do sistema de previdencia: gerenciar participantes, contribuicoes, beneficios, folha de pagamento, emprestimos, portabilidade, cotas, investimentos e processamento mensal. Inclui rotinas de previa (conferencia antes de processar), fechamento de competencia e acoes pos-liquidacao.

## Legados Afetados
| Legado | O que e substituido |
|--------|-------------------|
| mapsdataa-previdenciario | Adesao, contribuicao, beneficio, folha, emprestimo, portabilidade, cota, investimento, processamento, parametrizacao (>3.500 classes) |

## Modulos e Dependencias

| Modulo | Depende de | Descricao |
|--------|-----------|-----------|
| 001 - Membership | 01-Members | Adesao, inscricao, vinculo ao plano |
| 002 - Contributions | 001 | Contribuicoes mensais, patrocinio, aportes |
| 003 - Benefits | 001 | Beneficiarios, dependentes, calculo de beneficio |
| 004 - Payroll | 001, 002 | Folha de beneficio, processamento mensal |
| 005 - Loans | 001, 002 | Emprestimos consignados |
| 006 - Portability | 001, 002 | Portabilidade de entrada e saida |
| 007 - Quota | 001 | Cotas, valor da cota, posicao do participante |
| 008 - Investment | 001, 007 | Perfis de investimento, aplicacao, resgate |
| 009 - Valuation | 001, 007 | Indexadores, saldo, extrato, movimentacao |
| 010 - Processing | 001-009 | Processamento batch mensal, modelos, previa |
| 011 - Parameterization | 001-010 | Regras de negocio configuradas pelo cliente |
| 012 - Digital Onboarding | 01-Members | Adesao 100% digital do participante |
| 013 - Preview Reconciliation | 010 | Previa antes do processamento com conciliacao |
| 014 - Post Settlement | 001-009 | Acoes automaticas apos liquidacao de operacao |
| 015 - Period Closing | 001-014 | Fechamento mensal de competencia |

## Criterios de Aceite da Sprint
1. Participante adere ao plano e começa a contribuir no mesmo mes
2. Processamento mensal com previa gera contribuicoes, beneficios e emprestimos
3. Apos liquidacao de adesao/resgate/portabilidade, acoes automaticas sao executadas
4. Fechamento de mes valida consistencia e bloqueia novas movimentacoes
5. Participante acompanha saldo, cotas e extrato pelo aplicativo

## Riscos e Mitigacoes
| Risco | Mitigacao |
|-------|-----------|
| Processamento com dados inconsistentes | Previa obrigatoria antes de efetivar |
| Retrabalho por falha pos-liquidacao | Fila de revisao com notificacao |
| Fechamento bloqueado por divergencia | Relatorio claro do que precisa ser corrigido |
