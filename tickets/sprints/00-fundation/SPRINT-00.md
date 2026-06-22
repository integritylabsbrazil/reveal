# Sprint 00: Fundacao

## Objetivo de Negocio
Estabelecer a base do SaaS: cadastro de entidades (inquilinos), controle de quem acessa o sistema e ferramentas para trazer dados de sistemas legados. Sem esta base, nenhum outro modulo pode funcionar.

## Legados Afetados
| Legado | O que e substituido |
|--------|-------------------|
| dataa-tesouraria | Cadastro de usuarios e permissoes |
| mapsdataa-previdenciario | Cadastro de usuarios, perfis e permissoes |

## Modulos e Dependencias

| Modulo | Depende de | Descricao |
|--------|-----------|-----------|
| 001 - Tenant Registry | Nenhum | Cadastro e provisionamento de inquilinos |
| 002 - Identity & Auth | 001 | Quem acessa, o que pode fazer, registro de acesso |
| 003 - Import Tools | 001 | Migracao de dados de sistemas legados |

## Criterios de Aceite da Sprint
1. Entidade se cadastra e comeca a usar o sistema em minutos
2. Duas entidades diferentes jamais acessam dados uma da outra
3. Operador faz login e ve apenas o que sua funcao permite
4. Participante acessa o sistema para ver seus proprios dados
5. Importacao de dados legados ocorre com validacao e relatorio

## Riscos e Mitigacoes
| Risco | Mitigacao |
|-------|-----------|
| Qualidade dos dados legados e baixa | Validação pre-importacao com relatorio claro |
| Entidade quer personalizar o ambiente | Configuracoes por inquilino (branding, idioma) |
