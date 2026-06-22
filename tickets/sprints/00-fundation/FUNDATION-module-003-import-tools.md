# Modulo: Import Tools

## Objetivo de Negocio
Importar dados de sistemas legados para o ClearPension durante a migracao de clientes. Cada cliente que chega tem anos de dados em sistemas diferentes — e preciso trazer tudo sem perder informacao e sem interromper as operacoes.

## O que Existe nos Legados
Nenhum dos legados possui ferramentas de migracao. A entrada de um novo cliente e um projeto de meses com consultoria.

### dataa-tesouraria
- Exportacao manual via relatorios
- Scripts avulsos feitos sob demanda

### mapsdataa-previdenciario
- Exportacao via relatorios
- Sem ferramenta de carga inicial

## Lacuna de Mercado
Migracao automatizada e um diferencial competitivo enorme. Concorrentes tradicionais levam de 3 a 6 meses para implantar um cliente. Nosso objetivo e reduzir para dias.

## Regras de Negocio
1. Importacao guiada por tipo de entidade: participantes, contribuicoes, lancamentos, emprestimos, saldos
2. Cada tipo de entidade tem layout de arquivo pre-definido (CSV padrao)
3. Antes de importar, o sistema valida os dados: CPF duplicado, valores inconsistentes, campos obrigatorios
4. E possivel simular a importacao para ver o resultado antes de confirmar
5. Se um lote falhar, os lotes anteriores permanecem importados (nao perde o que ja foi carregado)
6. Relatorio completo ao final: quantos registros importados, quantos rejeitados e por que
7. Historico de todas as importacoes realizadas, com data e responsavel

## Criterios de Aceitacao
1. Arquivo CSV de 100 mil participantes e importado e validado
2. Validacao pre-importacao aponta todos os erros antes de persistir
3. Simulacao mostra relatorio de impacto sem efetivar a importacao
4. Erro no meio do processo nao perde os registros ja importados
5. Historico permite consultar importacoes passadas e seus resultados
6. Importacao especifica para: participantes, contribuicoes, saldos, lancamentos financeiros, emprestimos
