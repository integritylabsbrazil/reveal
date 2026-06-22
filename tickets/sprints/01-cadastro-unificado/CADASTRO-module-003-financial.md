# Modulo: Financial Institutions

## Objetivo de Negocio
Gerenciar instituicoes financeiras, agencias, contas bancarias e chaves PIX utilizadas nas operacoes de tesouraria e previdencia. Centralizar o cadastro bancario que hoje existe duplicado nos dois legados.

## O que Existe nos Legados

### dataa-tesouraria
- Tabela BANCO: codigo (COMPE), nome, site
- Tabela AGENCIA: codigo, digito, nome, endereco, banco FK
- Tabela CONTA_CORRENTE: numero, digito, agencia FK, favorecido FK, tipo, ativo
- Tabela TIPO_CONTA: corrente, poupanca, pagamento

### mapsdataa-previdenciario
- Tabela INSTITUICAO_FINANCEIRA: dados bancarios com codigo, nome
- Tabela AGENCIA: codigo, digito, endereco
- Tabela CONTA_BANCARIA: dados da conta vinculada a participante ou plano

## Lacuna de Mercado
- Integracao PIX: cadastro e validacao de chaves PIX (CPF, CNPJ, email, telefone, aleatoria)
- Validacao de conta bancaria via consulta ao BACEN (comprovacao de titularidade)
- Historico de contas bancarias de um member (contas antigas, motivo da troca)
- Regras de conta padrao por tipo de operacao (ex: pagamento de beneficio sempre para conta X)
- Compliance bancario: bloqueio de contas em paises nao cooperantes

## Regras de Negocio
1. Conta bancaria pertence a um member (PF ou PJ)
2. Cada member pode ter N contas, mas uma e a padrao por tipo de operacao
3. Chave PIX deve ser unica por tenant
4. Validacao de titularidade: member PF precisa ser titular ou procurador
5. Contas podem ser bloqueadas para tipos especificos de operacao
6. Historico mantem contas inativas por 5 anos (exigencia legal)

## Criterios de Aceitacao
1. Cadastro de conta bancaria com validacao de numero + digito
2. Chave PIX CPF e validada contra o CPF do member
3. Member pode ter conta padrao para recebimento e outra para pagamento
4. Troca de conta registra motivo e aprovador no historico
5. Bloqueio de conta impede seu uso em novas transacoes

## Dependencias Tecnicas
- 001 - Members

## Projetos Legados de Referencia
- Tesouraria: `src/main/java/**/banco/`, `src/main/java/**/agencia/`, `src/main/java/**/contacorrente/`
- Previdenciario: `core/src/main/java/**/instituicaoFinanceira/`
