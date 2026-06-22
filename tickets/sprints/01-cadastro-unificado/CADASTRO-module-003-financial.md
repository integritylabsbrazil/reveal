# Modulo: Financial Institutions

## Objetivo de Negocio
Centralizar o cadastro de bancos, agencias e contas bancarias utilizados nas operacoes do fundo. Cada participante e cada fundo precisam de contas para receber e pagar valores.

## O que Existe nos Legados

### dataa-tesouraria
- Bancos com codigo e nome
- Agencias com codigo e endereco
- Contas correntes vinculadas a favorecidos

### mapsdataa-previdenciario
- Instituicoes financeiras
- Agencias vinculadas
- Contas bancarias vinculadas a participantes e planos

## Lacuna de Mercado
- Chave PIX como forma de identificacao de conta
- Validacao de titularidade: a conta realmente pertence a quem diz ser
- Historico de contas do participante: contas antigas, motivo da troca
- Conta padrao por tipo de operacao (ex: pagamento de beneficio sempre para conta X)

## Regras de Negocio
1. Conta bancaria pertence a uma pessoa fisica ou juridica
2. Cada pessoa pode ter varias contas, mas uma e a principal para cada finalidade
3. Chave PIX e vinculada a pessoa e deve ser unica
4. Contas podem ser bloqueadas para tipos especificos de transacao
5. Troca de conta registra data e motivo
6. Historico de contas e mantido por 5 anos apos o encerramento

## Criterios de Aceitacao
1. Cadastro de banco, agencia e conta bancaria
2. Participante cadastra chave PIX vinculada ao seu CPF
3. Participante define uma conta principal para receber beneficios
4. Troca de conta registra data e motivo no historico
5. Conta bloqueada nao pode ser usada em novas transacoes
