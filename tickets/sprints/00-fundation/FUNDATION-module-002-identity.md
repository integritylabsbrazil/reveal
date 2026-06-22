# Modulo: Identity & Auth

## Objetivo de Negocio
Gerenciar identidades, autenticacao e autorizacao de todos os usuarios do sistema: administradores do tenant, operadores, participantes (PF), prestadores e auditores. Suportar SSO, MFA e RBAC granular.

## O que Existe nos Legados

### dataa-tesouraria
- Tabela USUARIO: CRUD basico com login/senha hash
- Tabela USUARIO_GRUPO: associacao usuario-grupo
- Tabela PERFIL: perfis de acesso (ADMIN, OPERADOR, CONSULTA)
- Sem suporte a SSO, MFA ou OAuth2
- Senhas armazenadas com hash simples (sem bcrypt/scrypt)

### mapsdataa-previdenciario
- Tabela USUARIO: entidade com email, senha, ativo
- Tabela PERFIL: roles administrativas
- Tabela PERMISSAO: permissoes granulares por entidade
- Sem suporte a SSO, MFA ou federacao

## Lacuna de Mercado
- Autenticacao multifator (MFA) — nenhum legado oferece
- SSO via OAuth2/OIDC (Google, Azure AD, Keycloak) — essencial para clientes enterprise
- Self-service de registro e recuperacao de senha
- Auditoria de autenticacao completa (logins, falhas, MFA reset)
- Suporte a API keys para integracao machine-to-machine

## Regras de Negocio
1. Todo login e registrado com IP, user-agent, timestamp e resultado (sucesso/falha)
5. Apos 5 tentativas de login falhas consecutivas, conta e bloqueada por 15 minutos
6. Sessoes expiram apos 8 horas de inatividade (configuravel por tenant)
7. Links de reset de senha expiram em 30 minutos
8. MFA via TOTP ou notificacao push (Obrigatorio para usuarios admin)
9. Usuarios podem ter multiplos papeis com escopos diferentes (ex: admin do Fundo A, consultor do Fundo B)
10. API keys tem escopo limitado a modulos especificos e expiram em 365 dias

## Criterios de Aceitacao
1. Login com email/senha funciona com MFA configurado
2. SSO com OAuth2/OIDC (Keycloak) permite login sem senha local
3. RBAC impede acesso a recursos fora do escopo do usuario
4. API key com escopo restrito so acessa endpoints permitidos
5. Auditoria de autenticacao registra todos os eventos com dados forenses
6. Bloqueio por tentativas falhas e testado com integracao

## Dependencias Tecnicas
- 001 - Tenant Registry (para obter contexto do tenant)

## Projetos Legados de Referencia
- Tesouraria: `**/seguranca/**`, `**/usuario/**`
- Previdenciario: `core/src/main/java/**/usuario/`, `core/src/main/java/**/perfil/`
