# Sprint 00: Fundacao

## Objetivo de Negocio
Estabelecer a infraestrutura base do SaaS ClearPension: multi-tenancy, identidade e autenticacao, e ferramentas de importacao de dados legados. Sem esta sprint, nenhuma outra pode existir — e a fundacao sobre a qual todo o sistema sera construido.

## Legados Afetados
Nenhum dominio de negocio e substituido nesta sprint. O foco e infraestrutura.

| Legado | O que e substituido |
|--------|-------------------|
| dataa-tesouraria | Tabela USUARIO, perfis de acesso CRUD (SIS_USUARIO, USUARIO_GRUPO) |
| mapsdataa-previdenciario | Tabelas USUARIO, PERFIL, PERMISSAO (entidades do modulo de seguranca) |

## Lacunas de Mercado Preenchidas
- Multi-tenancy nativo (nenhum legado suporta)
- Onboarding tecnico automatizado (auto-provisionamento de tenant)
- RBAC granular com escopo por fundo/modulo
- Ferramentas de importacao de massa para migracao de legados

## Modulos e Dependencias

| Modulo | Depende de | Descricao |
|--------|-----------|-----------|
| 001 - Tenant Registry | Nenhum | Cadastro e provisionamento de inquilinos |
| 002 - Identity & Auth | 001 | Autenticacao, autorizacao, RBAC, SSO |
| 003 - Import Tools | 001 | Pipeline ETL para importar dados de sistemas legados |

## Criterios de Aceite da Sprint
1. Um novo tenant consegue se registrar e ter seu ambiente provisionado em menos de 5 minutos
2. Um usuario consegue fazer login com email+senha e SSO (OAuth2/OIDC)
3. Permissoes sao aplicadas corretamente por escopo (tenant + fundo + modulo)
4. Ferramenta de importacao consegue carregar dados de planilha CSV padrao e validar consistencia
5. Todos os modulos futuros conseguem obter tenant context via thread-local ou header

## Riscos e Mitigacoes
| Risco | Mitigacao |
|-------|-----------|
| Complexidade de multi-tenancy impacta performance | Database-per-tenant com pooling de conexoes |
| Importacao de dados legados com qualidade baixa | Validacao pre-importacao com relatorio de inconsistencias |
| SSO complexo para clientes sem IdP | Fallback para auth local com senha |

## Projetos Legados de Referencia
- dataa-tesouraria: `src/main/java/**/seguranca/`, `src/main/java/**/usuario/`
- mapsdataa-previdenciario: `core/src/main/java/**/usuario/`, `core/src/main/java/**/perfil/`
