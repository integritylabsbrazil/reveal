# Modulo: Funds

## Objetivo de Negocio
Gerenciar planos de beneficio (fundos) e seus regulamentos, convenios, patrocinadores e configuracoes especificas. Cada fundo e uma entidade autonoma com suas proprias regras de contribuicao, beneficio e investimento.

## O que Existe nos Legados

### dataa-tesouraria
- Tabela CONVENIO: convenios/planos com dados basicos
- Tabela PATROCINADOR: entidade patrocinadora

### mapsdataa-previdenciario
- Tabela PLANO_BENEFICIO: planos com codigo, nome, tipo (BD, CV, CD), situacao
- Tabela CONVENIO: entidade que formaliza o plano
- Tabela FUNDO_PREVIDENCIA: instituto de previdencia
- Tabela REGIME: regime previdenciario (RPPS, RPC)
- Tabela PATROCINADOR: orgao publico
- Tabela ORGAO_PUBLICO, TRIBUNAL, PODER: entidades vinculadas

## Lacuna de Mercado
- Fundo multipatrocinado com regulamentos diferentes por patrocinador
- Configuracao de regras de elegibilidade por fundo (tempo de carência, idade minima)
- Historico de regulamentos e versoes (cada alteracao de regulamento e imutavel)
- Calculadora de beneficios configurada por fundo
- Dashboard comparativo entre fundos do mesmo tenant

## Regras de Negocio
1. Fundo tem tipo: BENEFICIO_DEFINIDO, CONTRIBUICAO_DEFINIDA, CONTRIBUICAO_VARIAVEL
2. Fundo multipatrocinado pode ter N patrocinadores com aliquotas diferentes
3. Cada fundo tem seu proprio regulamento (documento versionado)
4. Fundo tem data de inicio e pode ser encerrado (sem novos participantes)
5. Regras de elegibilidade: tempo de empresa, idade, cargo
6. Convenio formaliza a adesao do patrocinador ao fundo
7. Fundos sao independentes entre si (cada um tem sua contabilidade separada)

## Criterios de Aceitacao
1. Criacao de fundo com tipo BD, CV ou CD e validacao de campos obrigatorios
2. Fundo multipatrocinado com 2 patrocinadores com aliquotas de 5% e 7%
3. Upload de regulamento em PDF com versionamento
4. Regra de elegibilidade: "minimo 12 meses de empresa" impede participante sem esse tempo
5. Encerramento de fundo bloqueia novas adesocs mas mantem participantes ativos
6. Busca de fundo por codigo, nome ou patrocinador

## Dependencias Tecnicas
- 001 - Members (patrocinadores sao members do tipo PJ)

## Projetos Legados de Referencia
- Tesouraria: `src/main/java/**/convenio/`
- Previdenciario: `core/src/main/java/**/plano/`, `core/src/main/java/**/convenio/`, `core/src/main/java/**/fundo/`
