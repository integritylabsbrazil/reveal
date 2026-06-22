# Sprint 01: Cadastro Unificado

## Objetivo de Negocio
Unificar todos os cadastros de pessoas, entidades, planos e instituicoes financeiras que hoje estao dispersos entre tesouraria e previdenciario. Um unico cadastro de members (PF/PJ), funds (planos), financial institutions e estrutura organizacional, com gestao documental integrada.

## Legados Afetados

| Legado | O que e substituido |
|--------|-------------------|
| dataa-tesouraria | FAVORECIDO (332 classes), PATROCINADOR, INSTITUICAO_FINANCEIRA, AGENCIA, CONTA_CORRENTE, CENTRO_CUSTO |
| mapsdataa-previdenciario | PARTICIPANTE, PATROCINADOR, PLANO, BENEFICIARIO, DEPENDENTE, CONVENIO, ORGAO_PUBLICO |

## Lacunas de Mercado Preenchidas
- Cadastro unico de members (favorecido + participante + beneficiario = uma entidade so)
- Biometria facial e assinatura digital no cadastro
- Autosservico para participantes atualizarem dados cadastrais
- Gestao documental com OCR e validacao automatica
- Workflow de aprovacao de cadastro

## Modulos e Dependencias

| Modulo | Depende de | Descricao |
|--------|-----------|-----------|
| 001 - Members | 00-Identity | Pessoas fisicas e juridicas: criacao, validacao, hierarquia |
| 002 - Funds | 001 | Planos de beneficio, multipatrocinio, convenios |
| 003 - Financial Institutions | 001 | Bancos, agencias, contas, PIX |
| 004 - Structure | 001 | Centro custo, departamento, nucleo |
| 005 - Documents | 001 | Upload, OCR, validacao, workflow |

## Criterios de Aceite da Sprint
1. Um member pode ser criado com dados minimos (CPF/CNPJ + nome) e enriquecido depois
2. Fundo multipatrocinado tem multiplos patrocinadores com regulamentos diferentes
3. Integracao PIX permite cadastro de chaves por member
4. Documento enviado e processado por OCR em menos de 30 segundos
5. Workflow de aprovacao de cadastro notifica aprovadores e registra auditoria

## Riscos e Mitigacoes
| Risco | Mitigacao |
|-------|-----------|
| Unificacao de cadastros com dados conflitantes | Regras de merge com prioridade configurável |
| Qualidade de OCR baixa para documentos digitalizados | Fallback para revisao manual com fila de aprovacao |
| Performance com muitos participantes (>100k) | Indexacao otimizada e cache de consultas frequentes |
