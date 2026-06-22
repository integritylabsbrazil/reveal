# Modulo: Tenant Registry

## Objetivo de Negocio
Permitir que entidades de previdencia complementar se cadastrem no ClearPension e tenham seu ambiente isolado provisionado automaticamente. Cada tenant e uma entidade juridica independente com seus proprios dados, usuarios e configuracao.

## O que Existe nos Legados
Nenhum dos legados possui conceito de tenant ou multi-tenancy. Ambos sao sistemas monoliticos single-tenant instalados on-premise por cliente.

### dataa-tesouraria
- Nao existe tabela de tenant. Cada instalacao e um banco de dados separado.
- A identificacao do "cliente" e feita via configuracao de properties (application-{perfil}.properties)

### mapsdataa-previdenciario
- Mesmo modelo: single-tenant. Cada cliente tem sua propria instancia do sistema.

## Lacuna de Mercado
Multi-tenancy e o fundamento do SaaS. Nenhum concorrente tradicional (Dataa, Maps) oferece uma plataforma multi-tenant nativa. Startups como Zro Bank e Clara estao nessa direcao, mas sem foco em previdencia.

## Regras de Negocio
1. Cada tenant possui um identificador unico (slug) usado em todas as URLs e APIs
2. O provisionamento inclui: criacao do schema de banco, configuracao de storage, filas e topicos Kafka
3. Um tenant pode estar em status: trial, ativo, suspenso, cancelado
4. Trial dura 30 dias com limite de 100 participantes
5. Ao cancelar, os dados sao retidos por 90 dias (politica de retencao legal)
6. Cada tenant tem um plano de precificacao associado (Starter, Growth, Enterprise)
7. Configuracoes especificas do tenant (dominio personalizado, branding, idioma)

## Criterios de Aceitacao
1. API de registro de tenant recebe dados cadastrais e retorna slug + instrucoes de onboarding
2. Provisionamento cria schema de banco isolado em menos de 30 segundos
3. Tenant context e propagado em toda request via header X-Tenant-Id
4. Dashboard admin lista todos os tenants com status e metricas de uso
5. Politica de retencao de 90 dias apos cancelamento e testada
6. Impossivel um usuario acessar dados de outro tenant

## Dependencias Tecnicas
- Nenhuma (modulo raiz)

## Projetos Legados de Referencia
- Nenhum (dominio novo)
- Referencia de arquitetura: Spring Modulith + Flyway multi-schema + TenantContext holder
