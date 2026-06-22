# Modulo: Members

## Objetivo de Negocio
Unificar o cadastro de pessoas e empresas que hoje existe separado em tesouraria (favorecidos) e previdencia (participantes). Uma pessoa tem um unico cadastro, independente de ser participante de um fundo, beneficiario de outro ou patrocinador de um terceiro.

## O que Existe nos Legados

### dataa-tesouraria
- Cadastro de favorecidos com dados pessoais e endereco
- Beneficiarios e dependentes vinculados a favorecidos
- Patrocinadores (empresas patrocinadoras de planos)

### mapsdataa-previdenciario
- Cadastro de participantes (servidores publicos) vinculados a orgaos
- Patrocinadores (orgaos publicos, tribunais)
- Beneficiarios e dependentes vinculados a participantes

Uma mesma pessoa pode existir nos dois sistemas sem nenhuma relacao entre os cadastros.

## Lacuna de Mercado
- Cadastro unico: uma pessoa aparece uma so vez, com todos os seus papeis
- Autosservico: o participante mesmo atualiza seus dados, sem precisar do operador
- Validacao automatica de CPF e endereco
- Hierarquia entre empresas: grupo economico, holding, subsidiaria

## Regras de Negocio
1. Toda pessoa fisica ou juridica e um member, com tipo PF ou PJ
2. Papeis: participante de fundo, beneficiario, patrocinador, prestador de servico
3. Uma pessoa pode ser participante de um fundo e patrocinador de outro ao mesmo tempo
4. CPF/CNPJ e obrigatorio e nao pode se repetir dentro da mesma entidade
5. Alteracao de dados cadastrais mantem historico
6. Cadastro de novo member pode ser aprovado automaticamente ou passar por aprovacao
7. Member inativo nao pode participar de transacoes financeiras nem receber beneficios

## Criterios de Aceitacao
1. Cadastro de pessoa fisica com CPF valido
2. Cadastro de pessoa juridica com CNPJ e socios
3. Uma mesma pessoa e participante de um fundo e patrocinadora de outro
4. Historico mostra todas as alteracoes cadastrais com data e responsavel
5. Busca por CPF, nome ou email localiza o member em segundos
6. Member inativo aparece como bloqueado para novas transacoes
