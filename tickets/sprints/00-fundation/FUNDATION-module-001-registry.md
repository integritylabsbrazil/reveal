# Modulo: Tenant Registry

## Objetivo de Negocio
Permitir que entidades de previdencia complementar se cadastrem no ClearPension e tenham seu proprio ambiente. Cada inquilino (tenant) e uma entidade juridica independente com seus proprios dados, usuarios e configuracao.

## O que Existe nos Legados
Nenhum dos legados possui conceito de multi-inquilino. Ambos sistemas sao instalacoes isoladas, uma para cada cliente.

### dataa-tesouraria
- Cada cliente tem uma instalacao propria do software. Nao ha compartilhamento.

### mapsdataa-previdenciario
- Mesmo modelo: cada cliente tem sua propria instancia do sistema.

## Lacuna de Mercado
Multi-inquilino e o fundamento do SaaS. Concorrentes tradicionais nao oferecem plataforma compartilhada — cada cliente requer instalacao dedicada, aumento custo e complexidade.

## Regras de Negocio
1. Cada inquilino possui um identificador unico usado em todas as interfaces
2. Ao se cadastrar, o inquilino informa dados cadastrais e recebe acesso imediato ao ambiente
3. Um inquilino pode estar em status: trial, ativo, suspenso ou cancelado
4. Periodo trial de 30 dias com limite de 100 participantes
5. Ao cancelar, os dados sao retidos por 90 dias (conforme legislacao)
6. Cada inquilino tem um plano de precificacao (Starter, Growth, Enterprise)
7. Configuracoes proprias: branding, idioma, dominio personalizado

## Criterios de Aceitacao
1. Entidade consegue se registrar e acessar o sistema em menos de 5 minutos
2. Dois inquilinos diferentes nao tem acesso aos dados um do outro
3. Administrador do sistema ve painel com todos os inquilinos e metricas de uso
4. Ao cancelar, dados ficam retidos pelo prazo legal e depois sao removidos
5. Inquilino trial com 100 participantes pode operar normalmente
