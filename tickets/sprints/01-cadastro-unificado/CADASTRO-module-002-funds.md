# Modulo: Funds

## Objetivo de Negocio
Gerenciar os planos de beneficio (fundos) e seus regulamentos, convenios, patrocinadores e regras especificas. Cada fundo pode ter suas proprias regras de contribuicao, calculo de beneficio e investimento.

## O que Existe nos Legados

### dataa-tesouraria
- Convenios com dados basicos
- Patrocinadores

### mapsdataa-previdenciario
- Planos de beneficio com codigo, nome e tipo (BD, CV, CD)
- Convenios formalizando a relacao
- Patrocinadores (orgaos publicos)
- Regimes previdenciarios (RPPS, RPC)

## Lacuna de Mercado
- Fundo com multiplos patrocinadores, cada um com regras diferentes
- Regulamento com versoes: cada alteracao fica registrada no historico
- Regras de elegibilidade customizadas por fundo (tempo minimo, idade, cargo)
- Simulacao de beneficios para o participante baseada nas regras do seu fundo

## Regras de Negocio
1. Fundo tem tipo: Beneficio Definido, Contribuicao Definida ou Contribuicao Variavel
2. Fundo multipatrocinado pode ter varios patrocinadores com aliquotas diferentes
3. Cada fundo tem seu regulamento que pode ser substituido (versoes mantidas)
4. Fundo pode ser encerrado para novas adesões, mantendo participantes ativos
5. Regras de elegibilidade: tempo de empresa, idade minima, cargo

## Criterios de Aceitacao
1. Cadastro de fundo com tipo, nome e patrocinador
2. Fundo com 2 patrocinadores, cada um com aliquota de contribuicao diferente
3. Regulamento do fundo pode ser substituido mantendo o historico de versoes
4. Regra de elegibilidade "12 meses de empresa" impede participante sem esse tempo
5. Encerramento de fundo bloqueia novas adesões mas nao afeta participantes atuais
