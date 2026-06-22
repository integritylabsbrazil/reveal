# Modulo: Organizational Structure

## Objetivo de Negocio
Modelar a estrutura organizacional que os fundos utilizam para alocar custos, rateios e controles: centros de custo, departamentos, nucleos e hierarquia organizacional.

## O que Existe nos Legados

### dataa-tesouraria
- Tabela CENTRO_CUSTO: codigo, nome, ativo
- Tabela DEPARTAMENTO: codigo, nome, centro_custo FK
- Estrutura simples de dois niveis

### mapsdataa-previdenciario
- Nao ha entidade explicita de centro de custo
- A estrutura e definida por orgao publico -> poder -> tribunal

## Lacuna de Mercado
- Hierarquia flexivel com N niveis (tenant define a arvore)
- Vinculacao de member a estrutura organizacional
- Arvore organica com historico de movimentacoes
- Importacao em massa de estrutura via planilha
- Dashboard de headcount por nodo da arvore

## Regras de Negocio
1. Estrutura organizacional e uma arvore com N niveis (configurado por tenant)
2. Cada nodo tem tipo configurável: DEPARTAMENTO, SETOR, NUCLEO, GERENCIA, DIRETORIA
3. Members podem ser alocados a um ou mais nodos
4. Arvore tem data de vigencia (historico de reorganizacoes)
5. Rateio de custos pode ser proporcional por member alocado

## Criterios de Aceitacao
1. Criacao de arvore com 4 niveis (Diretoria -> Gerencia -> Setor -> Nucleo)
2. Alocacao de member em 2 nodos diferentes
3. Reorganizacao mantem historico com data de vigencia
4. Importacao de estrutura via CSV com 1000 nodos em menos de 1 minuto

## Dependencias Tecnicas
- 001 - Members

## Projetos Legados de Referencia
- Tesouraria: `src/main/java/**/centrocusto/`
