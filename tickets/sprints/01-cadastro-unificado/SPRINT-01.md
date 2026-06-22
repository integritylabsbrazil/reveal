# Sprint 01: Cadastro Unificado

## Objetivo de Negocio
Centralizar todos os cadastros que hoje estao dispersos entre os sistemas de tesouraria e previdencia: pessoas, empresas, planos de beneficio, bancos e estrutura organizacional. Um unico lugar para tudo, sem duplicidade.

## Legados Afetados
| Legado | O que e substituido |
|--------|-------------------|
| dataa-tesouraria | Favorecidos, patrocinadores, bancos, agencias, contas, centros de custo |
| mapsdataa-previdenciario | Participantes, patrocinadores, planos de beneficio, beneficiarios, dependentes |

## Modulos e Dependencias

| Modulo | Depende de | Descricao |
|--------|-----------|-----------|
| 001 - Members | 00-Identity | Pessoas fisicas e juridicas: cadastro, hierarquia, papeis |
| 002 - Funds | 001 | Planos de beneficio, multipatrocinio, regulamentos |
| 003 - Financial Institutions | 001 | Bancos, agencias, contas, chaves pix |
| 004 - Structure | 001 | Centro de custo, departamento, estrutura organizacional |
| 005 - Documents | 001 | Documentos digitais com validacao |

## Criterios de Aceite da Sprint
1. Pessoa fisica ou juridica cadastrada uma unica vez serve para todos os modulos
2. Um plano de beneficio pode ter multiplos patrocinadores com regras diferentes
3. Participante consegue atualizar seus proprios dados cadastrais
4. Documento enviado digitalmente e validado em ate 30 segundos
5. Cadastro novo passa por aprovacao antes de ser ativado

## Riscos e Mitigacoes
| Risco | Mitigacao |
|-------|-----------|
| Dados duplicados entre legados na migracao | Regras de merge com prioridade |
| Documento com baixa qualidade de leitura | Revisao manual com fila de aprovacao |
