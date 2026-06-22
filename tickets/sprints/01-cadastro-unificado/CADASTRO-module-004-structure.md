# Modulo: Organizational Structure

## Objetivo de Negocio
Modelar a estrutura de departamentos e centros de custo que os fundos usam para organizar seus participantes e ratear custos.

## O que Existe nos Legados

### dataa-tesouraria
- Centros de custo com codigo e nome
- Departamentos vinculados a centros de custo

### mapsdataa-previdenciario
- Estruturado por orgao publico, tribunal e poder

## Lacuna de Mercado
- Arvore organizacional flexivel com quantos niveis o inquilino precisar
- Participante pode ser alocado a mais de um nodo da estrutura
- Historico de reorganizacoes: se o departamento muda, os dados antigos se mantem

## Regras de Negocio
1. Estrutura organizacional e uma arvore com niveis definidos pelo inquilino
2. Cada nivel tem um tipo: diretoria, gerencia, departamento, setor, nucleo
3. Participantes podem estar alocados a um ou mais nodos
4. Reorganizacoes mantem o historico: dados antigos continuam vinculados ao nodo antigo
5. Rateio de custos pode usar como base a quantidade de participantes alocados

## Criterios de Aceitacao
1. Criacao de estrutura com 4 niveis (Diretoria > Gerencia > Departamento > Setor)
2. Participante alocado em 2 departamentos diferentes
3. Reorganizacao mantem historico com data de vigencia
4. Importacao de estrutura de 1000 nodos via planilha
