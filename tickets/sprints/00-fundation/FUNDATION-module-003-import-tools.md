# Modulo: Import Tools

## Objetivo de Negocio
Fornecer ferramentas para importar dados de sistemas legados (dataa-tesouraria, mapsdataa-previdenciario e outros) para o ClearPension. Essencial para a migracao de clientes sem interrupcao das operacoes.

## O que Existe nos Legados
Nenhum dos legados possui ferramentas de importacao/exportacao padronizadas.

### dataa-tesouraria
- Scripts SQL avulsos para carga inicial
- Relatorios em CSV para exportacao manual
- Sem API de importacao de massa

### mapsdataa-previdenciario
- Nao ha ferramentas de migracao
- Exportacao via relatorios JasperReports

## Lacuna de Mercado
Ferramentas de migracao sao um diferencial competitivo crucial. Concorrentes tradicionais nao oferecem on-ramp automatizado — a migracao e tipicamente um projeto de meses com consultoria.

## Regras de Negocio
1. Importacao via CSV, JSON ou conexao direta JDBC com banco legado
2. Mapeamento de campos entre schema legado e novo e configurado via YAML
3. Validacao pre-importacao: verifica consistencia, duplicatas e integridade referencial
4. Importacao em lotes com checkpoint e rollback parcial em caso de erro
5. Relatorio de importacao: registros importados, rejeitados, warnings
6. Suporte a dry-run: simula importacao sem persistir dados
7. Historico de importacoes por tenant com possibilidade de reverter
8. Pipeline de ETL versionado (cada versao de mapeamento e imutavel)

## Criterios de Aceitacao
1. Ferramenta importa CSV de 100 mil registros em menos de 5 minutos
2. Validacao pre-importacao detecta todos os erros de schema e duplicatas
3. Dry-run mostra relatorio de impacto sem persistir dados
4. Rollback parcial funciona quando um lote falha no meio do processo
5. Mapeamento YAML permite transformacao de campos (ex: data formato BR -> ISO)
6. Historico de importacoes permite auditoria completa

## Dependencias Tecnicas
- 001 - Tenant Registry (para saber em qual tenant importar)

## Projetos Legados de Referencia
- Tesouraria: schema completo em `target/database_dump.sql` (127 tabelas)
- Previdenciario: schema nos changelogs Liquibase (`db/changelog/`)
- Ambos os schemas servem como origem para os mapeamentos de importacao
